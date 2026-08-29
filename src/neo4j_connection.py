"""
Neo4j Database Connection and Transaction Management
Provides robust singleton driver lifecycle management, credential discovery,
parameterized Cypher execution, and real CSV Knowledge Graph ingestion.
"""
import os
import time
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from neo4j import GraphDatabase, Driver, Session
from dotenv import load_dotenv

# Load local environment variables if available
load_dotenv()


class Neo4jConnection:
    _instance: Optional["Neo4jConnection"] = None
    _driver: Optional[Driver] = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
        return cls._instance

    def __init__(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        # Allow dynamic credential overrides or load from secrets/env
        self.uri = uri or self._get_config("uri", "bolt://127.0.0.1:7687")
        self.username = username or self._get_config("username", "neo4j")
        self.password = password or self._get_config("password", "")
        self.database = database or self._get_config("database", "neo4j")

    def _get_config(self, key: str, default: str = "") -> str:
        """Fetch configuration value prioritizing Streamlit secrets, then ENV."""
        try:
            import streamlit as st
            if hasattr(st, "secrets") and "neo4j" in st.secrets:
                return str(st.secrets["neo4j"].get(key, ""))
            if hasattr(st, "secrets") and key in st.secrets:
                return str(st.secrets.get(key, ""))
        except Exception:
            pass

        # Environment variable fallback
        env_map = {
            "uri": ["NEO4J_URI", "NEO4J_URL", "BOLT_URL"],
            "username": ["NEO4J_USERNAME", "NEO4J_USER", "NEO4J_AUTH_USER"],
            "password": ["NEO4J_PASSWORD", "NEO4J_AUTH_PASSWORD", "NEO4J_PASS"],
            "database": ["NEO4J_DATABASE", "NEO4J_DB"],
        }
        for env_var in env_map.get(key, []):
            val = os.getenv(env_var)
            if val:
                return val

        return default

    def update_credentials(
        self,
        uri: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        """Update connection parameters and invalidate current driver."""
        if uri:
            self.uri = uri
        if username:
            self.username = username
        if password is not None:
            self.password = password
        if database:
            self.database = database
        self.close()

    def get_driver(self) -> Driver:
        """Retrieve active driver or create a new one."""
        if self._driver is None:
            # Handle neo4j:// or bolt://
            auth = (self.username, self.password) if self.password else None
            self._driver = GraphDatabase.driver(
                self.uri,
                auth=auth,
                max_connection_lifetime=30 * 60,
                max_connection_pool_size=50,
                connection_acquisition_timeout=15.0,
            )
        return self._driver

    def _get_session(self, driver: Driver) -> Session:
        """Helper to create a session respecting optional database names."""
        if self.database and self.database.strip():
            return driver.session(database=self.database.strip())
        return driver.session()

    def verify_connection(self) -> Tuple[bool, str]:
        """Test active Neo4j connectivity and return (status, message)."""
        try:
            driver = self.get_driver()
            driver.verify_connectivity()
            # Perform a test lightweight Cypher ping
            with self._get_session(driver) as session:
                res = session.run("RETURN 1 AS ping").single()
                if res and res["ping"] == 1:
                    return True, "Connected successfully to Neo4j database!"
            return True, "Connected successfully to Neo4j!"
        except Exception as e:
            self.close()
            error_msg = str(e)
            if "Unauthorized" in error_msg or "authentication" in error_msg.lower():
                return False, "Authentication failed: Please check username and password."
            elif "Connection refused" in error_msg or "ServiceUnavailable" in error_msg:
                return False, f"Cannot reach Neo4j at {self.uri}. Ensure Neo4j is running or URI is accessible."
            return False, f"Connection failed: {error_msg}"

    def run_query(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        read_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Execute parameterized Cypher query and return list of result records as dictionaries.
        """
        driver = self.get_driver()
        parameters = parameters or {}

        def _execute(tx):
            result = tx.run(query, parameters)
            return [record.data() for record in result]

        with self._get_session(driver) as session:
            if read_only:
                return session.execute_read(_execute)
            else:
                return session.execute_write(_execute)

    def run_write(
        self,
        query: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute parameterized Cypher write transaction and return summary stats.
        """
        driver = self.get_driver()
        parameters = parameters or {}

        with self._get_session(driver) as session:
            result = session.run(query, parameters)
            consume = result.consume()
            return {
                "nodes_created": consume.counters.nodes_created,
                "nodes_deleted": consume.counters.nodes_deleted,
                "relationships_created": consume.counters.relationships_created,
                "relationships_deleted": consume.counters.relationships_deleted,
                "properties_set": consume.counters.properties_set,
                "labels_added": consume.counters.labels_added,
            }

    def create_constraints(self):
        """Create unique constraints and indexes on Knowledge Graph node entities."""
        constraints = [
            "CREATE CONSTRAINT state_name_unique IF NOT EXISTS FOR (s:State) REQUIRE s.name IS UNIQUE",
            "CREATE CONSTRAINT city_name_unique IF NOT EXISTS FOR (c:City) REQUIRE c.name IS UNIQUE",
            "CREATE CONSTRAINT station_id_unique IF NOT EXISTS FOR (st:MonitoringStation) REQUIRE st.station_id IS UNIQUE",
            "CREATE CONSTRAINT pollutant_name_unique IF NOT EXISTS FOR (p:Pollutant) REQUIRE p.name IS UNIQUE",
            "CREATE INDEX reading_year_idx IF NOT EXISTS FOR (r:Reading) ON (r.year)",
            "CREATE INDEX datetime_value_idx IF NOT EXISTS FOR (d:DateTime) ON (d.value)"
        ]
        driver = self.get_driver()
        with self._get_session(driver) as session:
            for c in constraints:
                try:
                    session.run(c)
                except Exception:
                    pass

    def ingest_dataset_csv(
        self,
        csv_path: Optional[str] = None,
        clear_existing: bool = False
    ) -> Tuple[bool, str, Dict[str, int]]:
        """
        Ingest the real ap_air_pollution_2021_2023.csv dataset into Neo4j using
        the exact Knowledge Graph schema with parameterized Cypher batches.
        """
        if csv_path is None:
            # Locate default CSV
            current_dir = os.path.dirname(os.path.abspath(__file__))
            candidate = os.path.abspath(os.path.join(current_dir, "..", "data", "ap_air_pollution_2021_2023.csv"))
            if os.path.exists(candidate):
                csv_path = candidate
            else:
                csv_path = "data/ap_air_pollution_2021_2023.csv"

        if not os.path.exists(csv_path):
            return False, f"Dataset file not found at: {csv_path}", {}

        try:
            df = pd.read_csv(csv_path)
            # Ensure valid numeric values
            df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0)
            df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(2021).astype(int)
            records = df.to_dict("records")
        except Exception as e:
            return False, f"Failed to parse CSV dataset: {e}", {}

        try:
            # 1. Apply Schema
            self.create_constraints()

            driver = self.get_driver()
            with self._get_session(driver) as session:
                if clear_existing:
                    session.run("MATCH (n) DETACH DELETE n")

                # Ingestion Cypher query matching the exact knowledge graph structure
                ingest_cypher = """
                UNWIND $batch AS row
                MERGE (state:State {name: row.state})
                MERGE (city:City {name: row.city})
                MERGE (state)-[:HAS_CITY]->(city)
                
                MERGE (station:MonitoringStation {station_id: row.station_id})
                SET station.station_type = row.station_type
                MERGE (city)-[:HAS_STATION]->(station)
                
                MERGE (pollutant:Pollutant {name: row.pollutant})
                MERGE (date:DateTime {value: row.observation_date})
                
                CREATE (reading:Reading {
                    value: toFloat(row.value),
                    unit: row.unit,
                    measurement_type: row.measurement_type,
                    frequency: row.frequency,
                    year: toInteger(row.year),
                    source: row.source
                })
                CREATE (station)-[:HAS_READING]->(reading)
                CREATE (reading)-[:MEASURES]->(pollutant)
                CREATE (reading)-[:RECORDED_AT]->(date)
                """

                # Execute in batches
                batch_size = 50
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    session.run(ingest_cypher, batch=batch)

                # Fetch updated counts
                stats = {}
                labels = ["State", "City", "MonitoringStation", "Reading", "Pollutant", "DateTime"]
                for lbl in labels:
                    res = session.run(f"MATCH (n:{lbl}) RETURN count(n) AS cnt").single()
                    stats[lbl] = res["cnt"] if res else 0

                rels = ["HAS_CITY", "HAS_STATION", "HAS_READING", "MEASURES", "RECORDED_AT"]
                for r in rels:
                    res = session.run(f"MATCH ()-[rel:{r}]->() RETURN count(rel) AS cnt").single()
                    stats[f"REL_{r}"] = res["cnt"] if res else 0

                return True, f"Successfully ingested {len(records)} records into Neo4j Knowledge Graph!", stats

        except Exception as e:
            return False, f"Ingestion error: {str(e)}", {}

    def close(self):
        """Close driver connection pool safely."""
        if self._driver is not None:
            try:
                self._driver.close()
            except Exception:
                pass
            self._driver = None
