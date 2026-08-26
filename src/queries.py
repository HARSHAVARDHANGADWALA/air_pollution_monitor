"""
Cypher Queries Repository for Air Pollution Knowledge Graph
Contains all parameterized Cypher query templates and safety validators.
"""
import re
from typing import Any, Dict, List, Optional, Tuple

# ==========================================
# 1. KPI & STATISTICAL QUERIES
# ==========================================

KPI_COUNTS_CYPHER = """
MATCH (s:State)
WITH count(s) AS total_states
MATCH (c:City)
WITH total_states, count(c) AS total_cities
MATCH (st:MonitoringStation)
WITH total_states, total_cities, count(st) AS total_stations
MATCH (p:Pollutant)
WITH total_states, total_cities, total_stations, count(p) AS total_pollutants
MATCH (r:Reading)
RETURN 
    total_states,
    total_cities,
    total_stations,
    total_pollutants,
    count(r) AS total_readings
"""

COUNT_STATES_CYPHER = "MATCH (s:State) RETURN count(s) AS total_states"
COUNT_CITIES_CYPHER = "MATCH (c:City) RETURN count(c) AS total_cities"
COUNT_STATIONS_CYPHER = "MATCH (st:MonitoringStation) RETURN count(st) AS total_stations"
COUNT_POLLUTANTS_CYPHER = "MATCH (p:Pollutant) RETURN count(p) AS total_pollutants"
COUNT_READINGS_CYPHER = "MATCH (r:Reading) RETURN count(r) AS total_readings"

# ==========================================
# 2. DASHBOARD AGGREGATION QUERIES
# ==========================================

# Readings distribution and statistics by pollutant
READINGS_BY_POLLUTANT_CYPHER = """
MATCH (r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN 
    p.name AS pollutant,
    count(r) AS total_readings,
    round(avg(r.value), 2) AS avg_value,
    round(min(r.value), 2) AS min_value,
    round(max(r.value), 2) AS max_value,
    head(collect(r.unit)) AS unit
ORDER BY avg_value DESC
"""

# Pollution trends over years
READINGS_BY_YEAR_CYPHER = """
MATCH (r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN 
    r.year AS year,
    p.name AS pollutant,
    count(r) AS reading_count,
    round(avg(r.value), 2) AS avg_value,
    head(collect(r.unit)) AS unit
ORDER BY year ASC, pollutant ASC
"""

# City-wise average pollution comparison
CITY_WISE_POLLUTION_CYPHER = """
MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN 
    c.name AS city,
    p.name AS pollutant,
    r.year AS year,
    round(avg(r.value), 2) AS avg_value,
    head(collect(r.unit)) AS unit
ORDER BY c.name ASC, year ASC, pollutant ASC
"""

# State-wise overview
STATE_WISE_OVERVIEW_CYPHER = """
MATCH (st:State)-[:HAS_CITY]->(c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN 
    st.name AS state,
    p.name AS pollutant,
    round(avg(r.value), 2) AS avg_value,
    round(max(r.value), 2) AS max_value,
    count(r) AS readings_count,
    head(collect(r.unit)) AS unit
ORDER BY pollutant ASC
"""

# ==========================================
# 3. DYNAMIC DROPDOWN SELECTORS (FROM NEO4J)
# ==========================================

GET_ALL_STATES_CYPHER = """
MATCH (s:State)
RETURN DISTINCT s.name AS state
ORDER BY state ASC
"""

GET_ALL_CITIES_CYPHER = """
MATCH (c:City)
RETURN DISTINCT c.name AS city
ORDER BY city ASC
"""

GET_ALL_STATIONS_CYPHER = """
MATCH (st:MonitoringStation)
RETURN DISTINCT st.station_id AS station_id, st.station_type AS station_type
ORDER BY station_id ASC
"""

GET_ALL_POLLUTANTS_CYPHER = """
MATCH (p:Pollutant)
RETURN DISTINCT p.name AS pollutant
ORDER BY pollutant ASC
"""

GET_ALL_YEARS_CYPHER = """
MATCH (r:Reading)
RETURN DISTINCT r.year AS year
ORDER BY year ASC
"""

# ==========================================
# 4. PARAMETERIZED SEARCH QUERY
# ==========================================

def build_search_query(
    state: Optional[str] = None,
    city: Optional[str] = None,
    station_id: Optional[str] = None,
    pollutant: Optional[str] = None,
    year: Optional[int] = None
) -> Tuple[str, Dict[str, Any]]:
    """
    Build a dynamic parameterized Cypher query based on user filter selections.
    Guarantees no raw string interpolation for values to protect against injection.
    """
    clauses = [
        "MATCH (st:State)-[:HAS_CITY]->(c:City)-[:HAS_STATION]->(s:MonitoringStation)",
        "      -[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)",
        "MATCH (r)-[:RECORDED_AT]->(d:DateTime)"
    ]
    
    where_conditions = []
    params = {}

    if state and state != "All":
        where_conditions.append("st.name = $state")
        params["state"] = state

    if city and city != "All":
        where_conditions.append("c.name = $city")
        params["city"] = city

    if station_id and station_id != "All":
        where_conditions.append("s.station_id = $station_id")
        params["station_id"] = station_id

    if pollutant and pollutant != "All":
        where_conditions.append("p.name = $pollutant")
        params["pollutant"] = pollutant

    if year and year != "All":
        where_conditions.append("r.year = $year")
        params["year"] = int(year)

    query_parts = clauses
    if where_conditions:
        query_parts.append("WHERE " + " AND ".join(where_conditions))

    query_parts.append("""
    RETURN
        st.name AS state,
        c.name AS city,
        s.station_id AS station_id,
        s.station_type AS station_type,
        p.name AS pollutant,
        r.value AS value,
        r.unit AS unit,
        r.year AS year,
        r.measurement_type AS measurement_type,
        r.frequency AS frequency,
        d.value AS observation_date,
        r.source AS source
    ORDER BY city ASC, year DESC, pollutant ASC
    """)

    return "\n".join(query_parts), params

# ==========================================
# 5. DATA VISUALIZATION QUERIES
# ==========================================

# 1. City vs Pollution Value for a specific pollutant & year
CITY_POLLUTION_BAR_CYPHER = """
MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
WHERE p.name = $pollutant AND ($year IS NULL OR r.year = $year)
RETURN 
    c.name AS city,
    r.year AS year,
    round(avg(r.value), 2) AS value,
    head(collect(r.unit)) AS unit
ORDER BY value DESC
"""

# 2. Year-over-Year comparison by City
YEAR_OVER_YEAR_CYPHER = """
MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
WHERE p.name = $pollutant AND ($city IS NULL OR c.name = $city)
RETURN 
    c.name AS city,
    r.year AS year,
    round(avg(r.value), 2) AS value,
    head(collect(r.unit)) AS unit
ORDER BY city ASC, year ASC
"""

# 3. Pollutant Comparison for a specific City & Year
POLLUTANT_COMPARISON_CYPHER = """
MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
WHERE c.name = $city AND ($year IS NULL OR r.year = $year)
RETURN 
    p.name AS pollutant,
    r.year AS year,
    round(avg(r.value), 2) AS value,
    head(collect(r.unit)) AS unit
ORDER BY pollutant ASC, year ASC
"""

# 4. Top Polluted Cities ranking
TOP_CITIES_RANKING_CYPHER = """
MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
WHERE p.name = $pollutant AND r.year = $year
RETURN 
    c.name AS city,
    round(avg(r.value), 2) AS value,
    head(collect(r.unit)) AS unit
ORDER BY value DESC
LIMIT $limit
"""

# ==========================================
# 6. KNOWLEDGE GRAPH EXTRACTION QUERY
# ==========================================

KNOWLEDGE_GRAPH_EXPLORER_CYPHER = """
MATCH (st:State)-[r1:HAS_CITY]->(c:City)-[r2:HAS_STATION]->(s:MonitoringStation)
      -[r3:HAS_READING]->(rd:Reading)-[r4:MEASURES]->(p:Pollutant)
MATCH (rd)-[r5:RECORDED_AT]->(d:DateTime)
WHERE ($city IS NULL OR $city = 'All' OR c.name = $city)
  AND ($pollutant IS NULL OR $pollutant = 'All' OR p.name = $pollutant)
  AND ($year IS NULL OR $year = 'All' OR rd.year = $year)
RETURN 
    st.name AS state_name,
    c.name AS city_name,
    s.station_id AS station_id,
    s.station_type AS station_type,
    id(rd) AS reading_id,
    rd.value AS reading_value,
    rd.unit AS reading_unit,
    rd.year AS reading_year,
    p.name AS pollutant_name,
    d.value AS datetime_value
LIMIT $limit
"""

# ==========================================
# 7. ADD DATA CYPHER (PARAMETERIZED)
# ==========================================

ADD_READING_CYPHER = """
MERGE (state:State {name: $state})

MERGE (city:City {name: $city})

MERGE (state)-[:HAS_CITY]->(city)

MERGE (station:MonitoringStation {
    station_id: $station_id
})
SET station.station_type = $station_type

MERGE (city)-[:HAS_STATION]->(station)

MERGE (pollutant:Pollutant {
    name: $pollutant
})

MERGE (date:DateTime {
    value: $observation_date
})

CREATE (reading:Reading {
    value: toFloat($value),
    unit: $unit,
    measurement_type: $measurement_type,
    frequency: $frequency,
    year: toInteger($year),
    source: $source
})

CREATE (station)-[:HAS_READING]->(reading)

CREATE (reading)-[:MEASURES]->(pollutant)

CREATE (reading)-[:RECORDED_AT]->(date)
"""

# ==========================================
# 8. CUSTOM CYPHER SAFETY VALIDATION
# ==========================================

FORBIDDEN_WRITE_KEYWORDS = [
    r"\bDELETE\b",
    r"\bDETACH\b",
    r"\bDROP\b",
    r"\bCREATE\b",
    r"\bMERGE\b",
    r"\bSET\b",
    r"\bREMOVE\b",
    r"\bALTER\b",
    r"\bCALL\s+apoc\.",
    r"\bCALL\s+dbms\."
]

def validate_custom_query(query: str) -> Tuple[bool, str]:
    """
    Validate that the user-submitted custom Cypher query is read-only.
    Blocks destructive DDL and DML operations.
    """
    trimmed = query.strip()
    if not trimmed:
        return False, "Query cannot be empty."

    # Remove single line comments // and multi-line comments /* */
    cleaned = re.sub(r"//.*?\n", " ", trimmed)
    cleaned = re.sub(r"/\*.*?\*/", " ", cleaned, flags=re.DOTALL)

    for pattern in FORBIDDEN_WRITE_KEYWORDS:
        if re.search(pattern, cleaned, re.IGNORECASE):
            match = re.search(pattern, cleaned, re.IGNORECASE).group(0)
            return False, f"Destructive keyword '{match.strip()}' is blocked in Custom Query mode for safety. Use the 'Add Data' page to write new readings."

    if not re.search(r"\bMATCH\b|\bRETURN\b|\bSHOW\b|\bEXPLAIN\b|\bPROFILE\b", cleaned, re.IGNORECASE):
        return False, "Query must contain a valid MATCH, RETURN, or SHOW clause."

    return True, "Query is valid and read-only."
