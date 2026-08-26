# 🌍 AIR POLLUTION MONITOR USING STREAMLIT + NEO4J KNOWLEDGE GRAPH

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/)
[![Neo4j](https://img.shields.io/badge/Neo4j-Graph_Database-008CC1?logo=neo4j)](https://neo4j.com/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An interactive, production-grade academic project combining **Streamlit** and a native **Neo4j Knowledge Graph** to monitor, query, visualize, and analyze real atmospheric air quality across major urban centers in **Andhra Pradesh, India** using real data from the **Central Pollution Control Board (CPCB) National Air Quality Monitoring Programme (NAMP)** for **2021** and **2023**.

---

## 📌 Project Links & Demo Placeholders

- **GitHub Repository**: `https://github.com/HARSHAVARDHANGADWALA/air-pollution-monitor`
- **Live Streamlit App**: `https://air-pollution-monitor-kg.streamlit.app`

---

## 📖 Table of Contents
1. [Problem Statement](#-problem-statement)
2. [Key Features](#-key-features)
3. [Technology Stack](#-technology-stack)
4. [Knowledge Graph Ontology & Schema](#-knowledge-graph-ontology--schema)
5. [End-to-End System Architecture](#-end-to-end-system-architecture)
6. [Dataset Information](#-dataset-information)
7. [Installation & Setup Guide](#-installation--setup-guide)
8. [Neo4j Credential Configuration](#-neo4j-credential-configuration)
9. [How to Run the Application](#-how-to-run-the-application)
10. [Cypher Query Catalog](#-cypher-query-catalog)
11. [Academic Presentation (8-Slide Outline)](#-academic-presentation-8-slide-outline)
12. [Verification & Acceptance Testing](#-verification--acceptance-testing)
13. [License](#-license)

---

## 🎯 Problem Statement

Air pollution is a critical public health and environmental crisis in rapidly urbanizing regions. Traditional environmental monitoring applications rely on flat relational database tables (RDBMS) where spatial, institutional, temporal, and chemical relationships are fragmented across foreign-key tables. Querying multi-pollutant trends across hierarchical station networks results in complex, computationally expensive SQL `JOIN` operations that degrade performance and obscure interconnected insights.

**Solution:**
This project models air quality data as a **Native Knowledge Graph** in Neo4j. By storing entities (`State`, `City`, `MonitoringStation`, `Reading`, `Pollutant`, `DateTime`) as interconnected nodes and relationships, the system delivers index-free adjacency graph traversals, flexible dynamic multi-criteria search, sub-millisecond query execution, and rich physics-based topological visualizations through an interactive Streamlit interface.

---

## ✨ Key Features

1. **📊 Real-Time KPI Dashboard**:
   - Dynamic Cypher-computed statistics: Total States, Total Cities, Total Stations, Total Readings, Total Pollutants.
   - Pollutant reading distribution and concentration averages against national air quality standards.
   - City-level and year-over-year multi-bar comparison matrix.

2. **🔍 Dynamic Multi-Filter Search**:
   - Filter dropdowns dynamically loaded from live Neo4j nodes (State, City, Station ID, Pollutant, Year).
   - Parameterized Cypher query generation with strict Cypher injection prevention.
   - Latency metrics, interactive data table, and one-click CSV export.

3. **📈 Multi-Dimensional Data Visualization**:
   - City vs. Pollution concentration rankings.
   - Temporal Year-over-Year (2021 vs. 2023) trend analysis.
   - Comparative multi-pollutant profiles for selected urban centers.
   - Leaderboard of the top most polluted cities.

4. **🕸️ Interactive Knowledge Graph Topology**:
   - Physics-based interactive canvas powered by PyVis and Plotly 2D network graphs.
   - Color-coded node taxonomy (State, City, Station, Reading, Pollutant, DateTime).
   - Dynamic subgraph extraction filtered by City, Pollutant, Year, and Max Node limits.

5. **⚡ Safe Custom Cypher Terminal**:
   - Execute custom Cypher queries directly against the graph database.
   - Preset query templates for academic demonstration.
   - Safety validation engine blocking destructive DDL/DML clauses (`DELETE`, `DROP`, `DETACH`, `MERGE`, `CREATE`, `SET`, `REMOVE`).

6. **➕ Knowledge Graph Ingestion & Add Data**:
   - Full input form for adding new pollution readings via parameterized `MERGE` and `CREATE` Cypher transactions.
   - Built-in one-click ingestion tool to sync `ap_air_pollution_2021_2023.csv` to the Knowledge Graph.

7. **📑 Academic Evaluation Presentation (8 Slides)**:
   - Interactive slide viewer right inside the Streamlit web application.
   - One-click `.pptx` PowerPoint presentation exporter generated via `python-pptx`.

---

## 🛠️ Technology Stack

| Layer | Technology | Description |
| :--- | :--- | :--- |
| **Frontend UI** | Streamlit (Python) | High-performance reactive web application framework |
| **Graph Database** | Neo4j Desktop 5+ | Native labeled-property graph database engine |
| **Query Language** | Cypher | Declarative graph query language |
| **Database Driver** | Official `neo4j` Python Driver | Thread-safe connection pooling and binary Bolt protocol |
| **Data Processing** | Pandas | Tabular hydration and serialization |
| **Visualization** | Plotly & PyVis | Interactive charting and physics-based network canvas |
| **Presentation** | Python-PPTX | Programmatic 8-slide PowerPoint generation |

---

## 🕸️ Knowledge Graph Ontology & Schema

### Entity Node Labels:
- `(:State {name: String})`
- `(:City {name: String})`
- `(:MonitoringStation {station_id: String, station_type: String})`
- `(:Reading {value: Float, unit: String, measurement_type: String, frequency: String, year: Integer, source: String})`
- `(:Pollutant {name: String})`
- `(:DateTime {value: String})`

### Relationship Graph:
```
(State)
   │
   └──[:HAS_CITY]──► (City)
                        │
                        └──[:HAS_STATION]──► (MonitoringStation)
                                                │
                                                └──[:HAS_READING]──► (Reading)
                                                                        ├──[:MEASURES]────► (Pollutant)
                                                                        └──[:RECORDED_AT]─► (DateTime)
```

---

## 🔄 End-to-End System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                       │
│       Streamlit Dashboard, Search & Visualizations      │
└────────────────────────────┬────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                     │
│    Python Driver, Parameterized Cypher & Query Router   │
└────────────────────────────┬────────────────────────────┘
                             │ (Bolt Protocol :7687)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                  KNOWLEDGE GRAPH (NEO4J)                │
│    (State)->(City)->(Station)->(Reading)->(Pollutant)   │
└─────────────────────────────────────────────────────────┘
```

---

## 📊 Dataset Information

The application strictly utilizes the real Central Pollution Control Board (CPCB) National Ambient Air Quality Monitoring Programme (NAMP) dataset:

- **Filename**: `data/ap_air_pollution_2021_2023.csv`
- **Coverage**: Major Andhra Pradesh urban centers (`Amaravati`, `Visakhapatnam`, `Vijayawada`, `Tirupati`, `Guntur`, `Kurnool`, `Rajahmundry`, `Nellore`, `Kakinada`, `Anantapur`, `Kadapa`, `Eluru`, `Ongole`, `Srikakulam`, `Vizianagaram`).
- **Pollutants**: `PM10`, `PM2.5`, `NO2`, `SO2`.
- **Reporting Years**: `2021`, `2023`.
- **Metric Unit**: `µg/m³` (Annual Average).

---

## 🚀 Installation & Setup Guide

### 1. Clone the Repository
```bash
git clone https://github.com/HARSHAVARDHANGADWALA/air-pollution-monitor.git
cd air-pollution-monitor
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 🔑 Neo4j Credential Configuration

You can configure credentials using either **Streamlit Secrets**, an **Environment File (`.env`)**, or the **UI Connection Settings modal**:

### Option A: Streamlit Secrets (Recommended)
Create `.streamlit/secrets.toml`:
```toml
[neo4j]
uri = "bolt://127.0.0.1:7687"
username = "neo4j"
password = "YOUR_PASSWORD_HERE"
database = "neo4j"
```

### Option B: Environment Variables (`.env`)
Create `.env` in the project root:
```env
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=YOUR_PASSWORD_HERE
NEO4J_DATABASE=neo4j
```

---

## 💻 How to Run the Application

Start the Streamlit application:
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

If your Neo4j database is empty, open the sidebar expander **⚙️ Connection Settings** and click **Sync CSV to KG** to load the dataset directly into the Knowledge Graph.

---

## 📑 Academic Presentation (8-Slide Outline)

- **Slide 1**: *Title & Overview* — Project scope, academic context, and environmental analytics focus.
- **Slide 2**: *Problem Statement & Objectives* — Overcoming RDBMS JOIN bottlenecks with graph data models.
- **Slide 3**: *Knowledge Graph Schema* — Entities, node properties, and semantic relationships.
- **Slide 4**: *System Architecture* — Three-tier architecture (Streamlit, Python Driver, Neo4j Engine).
- **Slide 5**: *Execution Flow* — Parameterized Cypher execution and data hydration pipeline.
- **Slide 6**: *Key Cypher Queries* — Real-world Cypher queries for KPIs, Search, and Graph Ingestion.
- **Slide 7**: *Live Results & Findings* — Summary of 2021 vs 2023 air pollution patterns in Andhra Pradesh.
- **Slide 8**: *Challenges, Solutions & Future Scope* — Graph security, IoT sensor integration, and predictive forecasting.

*You can download the generated `.pptx` presentation deck directly from the "📑 Presentation Deck" tab in the application.*

---

## 🧪 Verification & Acceptance Testing

- [x] **Test 1**: Verify Neo4j connection shows `🟢 Neo4j Connected`.
- [x] **Test 2**: Verify Dashboard loads real node statistics (`Total States`, `Total Cities`, `Total Readings`).
- [x] **Test 3**: Execute Search with `City = Amaravati`, `Pollutant = PM2.5`, `Year = 2023`.
- [x] **Test 4**: Change search parameters and verify dynamic query output changes accordingly.
- [x] **Test 5**: Inspect Data Visualization charts for multi-city comparisons.
- [x] **Test 6**: Run read-only query in Custom Query console.
- [x] **Test 7**: Load Knowledge Graph visualizer and inspect physics canvas.
- [x] **Test 8**: Add new reading in Add Data form and confirm immediate appearance in Search.

---

## 📄 License
This project is licensed under the MIT License.
