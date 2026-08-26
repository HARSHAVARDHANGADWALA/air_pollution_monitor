"""
Air Pollution Monitor Using Streamlit + Neo4j Knowledge Graph
Main Multi-Page Interactive Web Application

Architecture:
User -> Streamlit UI -> Python Driver -> Parameterized Cypher -> Neo4j Knowledge Graph -> Real Data -> Streamlit UI
"""
import os
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from src.neo4j_connection import Neo4jConnection
from src.queries import (
    KPI_COUNTS_CYPHER,
    READINGS_BY_POLLUTANT_CYPHER,
    READINGS_BY_YEAR_CYPHER,
    CITY_WISE_POLLUTION_CYPHER,
    STATE_WISE_OVERVIEW_CYPHER,
    GET_ALL_STATES_CYPHER,
    GET_ALL_CITIES_CYPHER,
    GET_ALL_STATIONS_CYPHER,
    GET_ALL_POLLUTANTS_CYPHER,
    GET_ALL_YEARS_CYPHER,
    CITY_POLLUTION_BAR_CYPHER,
    YEAR_OVER_YEAR_CYPHER,
    POLLUTANT_COMPARISON_CYPHER,
    TOP_CITIES_RANKING_CYPHER,
    KNOWLEDGE_GRAPH_EXPLORER_CYPHER,
    ADD_READING_CYPHER,
    build_search_query,
    validate_custom_query,
)
from src.graph_visualizer import generate_pyvis_html, generate_plotly_graph, NODE_COLORS, NODE_ICONS
from src.ppt_export import generate_presentation_pptx, SLIDES_CONTENT

# ==========================================
# 1. PAGE CONFIGURATION & STYLING
# ==========================================
st.set_page_config(
    page_title="Air Pollution Monitor | Neo4j Knowledge Graph",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Executive Dark CSS Styling
st.markdown("""
<style>
    /* Global styles */
    .main {
        background-color: #0f172a;
    }
    
    /* Header title gradient */
    .app-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #34d399 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .app-subtitle {
        color: #94a3b8;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
        font-weight: 500;
    }
    
    /* Metric Cards */
    div[data-testid="metric-container"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        padding: 16px 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="metric-container"] label {
        color: #94a3b8 !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }
    
    /* Card Container */
    .glass-card {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 22px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    
    /* Cypher Snippet Box */
    .cypher-box {
        background-color: #090d16;
        border-left: 4px solid #38bdf8;
        border-radius: 6px;
        padding: 12px 16px;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 13px;
        color: #7dd3fc;
        margin-top: 10px;
        margin-bottom: 10px;
    }
    
    /* Entity Badge */
    .badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 600;
        margin-right: 5px;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. STATE & CONNECTION INITIALIZATION
# ==========================================

@st.cache_resource
def get_db_connection() -> Neo4jConnection:
    return Neo4jConnection()

conn = get_db_connection()

# ==========================================
# 3. SIDEBAR CONTROLS & CONNECTION STATUS
# ==========================================

st.sidebar.markdown("### 🌍 Project Controls")

is_connected, conn_msg = conn.verify_connection()

if is_connected:
    st.sidebar.success("🟢 Neo4j Connected")
else:
    st.sidebar.error("🔴 Neo4j Connection Failed")
    st.sidebar.caption(conn_msg)

with st.sidebar.expander("⚙️ Connection Settings", expanded=not is_connected):
    uri_input = st.text_input("Neo4j URI", value=conn.uri, help="e.g. bolt://127.0.0.1:7687 or neo4j://127.0.0.1:7687")
    user_input = st.text_input("Username", value=conn.username)
    pass_input = st.text_input("Password", value=conn.password, type="password")
    db_input = st.text_input("Database", value=conn.database)

    col_c1, col_c2 = st.columns(2)
    with col_c1:
        if st.button("Connect / Save", use_container_width=True):
            conn.update_credentials(uri=uri_input, username=user_input, password=pass_input, database=db_input)
            st.cache_data.clear()
            st.rerun()

    with col_c2:
        if st.button("Sync CSV to KG", use_container_width=True, help="Ingest real ap_air_pollution_2021_2023.csv"):
            with st.spinner("Ingesting dataset into Knowledge Graph..."):
                success, msg, stats = conn.ingest_dataset_csv(clear_existing=False)
                if success:
                    st.sidebar.success(msg)
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.sidebar.error(msg)

st.sidebar.markdown("---")
page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Dashboard",
        "🔍 Search",
        "📈 Data Visualization",
        "🕸️ Knowledge Graph",
        "⚡ Custom Query",
        "➕ Add Data",
        "📑 Presentation Deck"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    **Project Info**  
    • Dataset: `CPCB NAMP AP (2021-2023)`  
    • Graph Model: `6 Labels, 5 Rel Types`  
    • Engine: `Neo4j Desktop + Cypher`  
    """
)

# ==========================================
# 4. APP HEADER
# ==========================================
st.markdown('<div class="app-title">🌍 AIR POLLUTION MONITOR</div>', unsafe_allow_html=True)
st.markdown('<div class="app-subtitle">Interactive Neo4j Knowledge Graph Dashboard & Real-Time Analytics</div>', unsafe_allow_html=True)

# ==========================================
# 5. PAGE: DASHBOARD
# ==========================================
if page == "📊 Dashboard":
    st.markdown("### 📊 Knowledge Graph Metrics & Pollution Overview")
    st.markdown("Live summary statistics queried directly from the Neo4j Knowledge Graph.")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Please configure your credentials in the sidebar to view live dashboard metrics.")
    else:
        with st.spinner("Executing KPI queries in Neo4j..."):
            try:
                kpi_data = conn.run_query(KPI_COUNTS_CYPHER)
                if kpi_data:
                    kpi = kpi_data[0]
                    total_states = kpi.get("total_states", 0)
                    total_cities = kpi.get("total_cities", 0)
                    total_stations = kpi.get("total_stations", 0)
                    total_pollutants = kpi.get("total_pollutants", 0)
                    total_readings = kpi.get("total_readings", 0)
                else:
                    total_states = total_cities = total_stations = total_pollutants = total_readings = 0
            except Exception as e:
                st.error(f"Error fetching KPIs: {e}")
                total_states = total_cities = total_stations = total_pollutants = total_readings = 0

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total States", f"{total_states:,}", help="Count of (:State) nodes in Neo4j")
        c2.metric("Total Cities", f"{total_cities:,}", help="Count of (:City) nodes in Neo4j")
        c3.metric("Monitoring Stations", f"{total_stations:,}", help="Count of (:MonitoringStation) nodes in Neo4j")
        c4.metric("Pollutants Tracked", f"{total_pollutants:,}", help="Count of (:Pollutant) nodes in Neo4j")
        c5.metric("Total Readings", f"{total_readings:,}", help="Count of (:Reading) nodes in Neo4j")

        if total_readings == 0:
            st.info("💡 Your Neo4j database has 0 readings. Click **'Sync CSV to KG'** in the sidebar settings to load the Andhra Pradesh 2021-2023 dataset!")

        st.markdown("---")

        col_ch1, col_ch2 = st.columns(2)

        with col_ch1:
            st.markdown("#### 🌫️ Average Concentration by Pollutant")
            try:
                pollutant_df = pd.DataFrame(conn.run_query(READINGS_BY_POLLUTANT_CYPHER))
                if not pollutant_df.empty:
                    fig_pol = px.bar(
                        pollutant_df,
                        x="pollutant",
                        y="avg_value",
                        color="pollutant",
                        text="avg_value",
                        color_discrete_map={"PM10": "#f59e0b", "PM2.5": "#ef4444", "NO2": "#3b82f6", "SO2": "#10b981"},
                        title="Average Measured Concentration (µg/m³)",
                        labels={"avg_value": "Avg Value (µg/m³)", "pollutant": "Pollutant"}
                    )
                    fig_pol.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                    fig_pol.update_traces(texttemplate='%{text:.1f} µg/m³', textposition='outside')
                    st.plotly_chart(fig_pol, use_container_width=True)
                else:
                    st.info("No pollutant readings found.")
            except Exception as e:
                st.error(f"Error querying pollutant averages: {e}")

        with col_ch2:
            st.markdown("#### 📅 Readings by Year & Pollutant")
            try:
                year_df = pd.DataFrame(conn.run_query(READINGS_BY_YEAR_CYPHER))
                if not year_df.empty:
                    fig_yr = px.bar(
                        year_df,
                        x="year",
                        y="reading_count",
                        color="pollutant",
                        barmode="group",
                        color_discrete_map={"PM10": "#f59e0b", "PM2.5": "#ef4444", "NO2": "#3b82f6", "SO2": "#10b981"},
                        title="Reading Observation Counts by Year",
                        labels={"reading_count": "Number of Observations", "year": "Year"}
                    )
                    fig_yr.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                    st.plotly_chart(fig_yr, use_container_width=True)
                else:
                    st.info("No yearly records found.")
            except Exception as e:
                st.error(f"Error querying yearly records: {e}")

        st.markdown("#### 🏙️ City-Wise Pollution Level Matrix")
        try:
            city_df = pd.DataFrame(conn.run_query(CITY_WISE_POLLUTION_CYPHER))
            if not city_df.empty:
                fig_city = px.bar(
                    city_df,
                    x="city",
                    y="avg_value",
                    color="pollutant",
                    barmode="group",
                    facet_row="year",
                    color_discrete_map={"PM10": "#f59e0b", "PM2.5": "#ef4444", "NO2": "#3b82f6", "SO2": "#10b981"},
                    title="Comparative City Pollution Concentrations Across Years",
                    height=520,
                    labels={"avg_value": "Concentration (µg/m³)", "city": "City"}
                )
                fig_city.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                st.plotly_chart(fig_city, use_container_width=True)
            else:
                st.info("No city data found.")
        except Exception as e:
            st.error(f"Error querying city pollution matrix: {e}")

# ==========================================
# 6. PAGE: SEARCH
# ==========================================
elif page == "🔍 Search":
    st.markdown("### 🔍 Interactive Dynamic Search")
    st.markdown("Filter knowledge graph readings by State, City, Station, Pollutant, and Year. All filters are queried dynamically from Neo4j.")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Connect in sidebar to enable dynamic search.")
    else:
        try:
            states_res = conn.run_query(GET_ALL_STATES_CYPHER)
            cities_res = conn.run_query(GET_ALL_CITIES_CYPHER)
            stations_res = conn.run_query(GET_ALL_STATIONS_CYPHER)
            pollutants_res = conn.run_query(GET_ALL_POLLUTANTS_CYPHER)
            years_res = conn.run_query(GET_ALL_YEARS_CYPHER)

            state_opts = ["All"] + [r["state"] for r in states_res if r.get("state")]
            city_opts = ["All"] + [r["city"] for r in cities_res if r.get("city")]
            station_opts = ["All"] + [r["station_id"] for r in stations_res if r.get("station_id")]
            pollutant_opts = ["All"] + [r["pollutant"] for r in pollutants_res if r.get("pollutant")]
            year_opts = ["All"] + [str(r["year"]) for r in years_res if r.get("year")]
        except Exception as e:
            st.error(f"Error populating search filters from Neo4j: {e}")
            state_opts = city_opts = station_opts = pollutant_opts = year_opts = ["All"]

        with st.form("search_form"):
            col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
            with col_f1:
                sel_state = st.selectbox("State", state_opts)
            with col_f2:
                sel_city = st.selectbox("City", city_opts)
            with col_f3:
                sel_station = st.selectbox("Station ID", station_opts)
            with col_f4:
                sel_pollutant = st.selectbox("Pollutant", pollutant_opts)
            with col_f5:
                sel_year = st.selectbox("Year", year_opts)

            search_btn = st.form_submit_button("🔍 Execute Search", use_container_width=True)

        if search_btn or "last_search" in st.session_state:
            if search_btn:
                st.session_state["last_search"] = {
                    "state": sel_state, "city": sel_city, "station": sel_station,
                    "pollutant": sel_pollutant, "year": sel_year
                }

            filters = st.session_state["last_search"]
            cypher_query, params = build_search_query(
                state=filters["state"],
                city=filters["city"],
                station_id=filters["station"],
                pollutant=filters["pollutant"],
                year=filters["year"]
            )

            start_t = time.time()
            try:
                results = conn.run_query(cypher_query, parameters=params)
                elapsed_ms = (time.time() - start_t) * 1000

                st.markdown(f"**Found {len(results):,} Records** (Execution Time: `{elapsed_ms:.2f} ms`)")

                if results:
                    res_df = pd.DataFrame(results)
                    st.dataframe(
                        res_df,
                        use_container_width=True,
                        column_config={
                            "value": st.column_config.NumberColumn("Concentration", format="%.2f"),
                            "year": st.column_config.NumberColumn("Year", format="%d"),
                        }
                    )

                    csv_bytes = res_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Search Results as CSV",
                        data=csv_bytes,
                        file_name=f"air_pollution_search_{filters['city']}_{filters['pollutant']}.csv",
                        mime="text/csv"
                    )
                else:
                    st.info("No matching records found in Neo4j Knowledge Graph for selected parameters.")

                with st.expander("🔎 Inspect Executed Parameterized Cypher Query"):
                    st.code(cypher_query, language="cypher")
                    st.json(params)

            except Exception as e:
                st.error(f"Search query failed: {e}")

# ==========================================
# 7. PAGE: DATA VISUALIZATION
# ==========================================
elif page == "📈 Data Visualization":
    st.markdown("### 📈 Multi-Dimensional Data Visualization")
    st.markdown("Analyze atmospheric pollutant distributions, city rankings, and temporal shifts using interactive Plotly charts.")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Connect in sidebar to load visualization data.")
    else:
        cities_res = conn.run_query(GET_ALL_CITIES_CYPHER)
        pollutants_res = conn.run_query(GET_ALL_POLLUTANTS_CYPHER)
        years_res = conn.run_query(GET_ALL_YEARS_CYPHER)

        city_list = [r["city"] for r in cities_res if r.get("city")]
        pollutant_list = [r["pollutant"] for r in pollutants_res if r.get("pollutant")]
        year_list = [r["year"] for r in years_res if r.get("year")]

        col_v1, col_v2, col_v3 = st.columns(3)
        with col_v1:
            v_pollutant = st.selectbox("Select Pollutant", pollutant_list if pollutant_list else ["PM2.5", "PM10", "NO2", "SO2"])
        with col_v2:
            v_year = st.selectbox("Select Year", [None] + year_list, format_func=lambda x: "All Years" if x is None else str(x))
        with col_v3:
            v_city = st.selectbox("Focus City (for Trends)", city_list if city_list else ["Amaravati", "Visakhapatnam"])

        st.markdown("---")

        st.markdown(f"#### 1. City Comparison for {v_pollutant} ({v_year if v_year else 'All Years'})")
        try:
            city_bar_data = conn.run_query(CITY_POLLUTION_BAR_CYPHER, {"pollutant": v_pollutant, "year": v_year})
            if city_bar_data:
                cb_df = pd.DataFrame(city_bar_data)
                fig_cb = px.bar(
                    cb_df,
                    x="city",
                    y="value",
                    color="value",
                    color_continuous_scale="Reds" if "PM" in v_pollutant else "Blues",
                    text="value",
                    title=f"Air Concentration Levels of {v_pollutant} Across Cities (µg/m³)",
                    labels={"value": f"{v_pollutant} (µg/m³)", "city": "City"}
                )
                fig_cb.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                fig_cb.update_traces(texttemplate='%{text:.1f}', textposition='outside')
                st.plotly_chart(fig_cb, use_container_width=True)
            else:
                st.info("No data returned for selected pollutant.")
        except Exception as e:
            st.error(f"Error querying city bar chart: {e}")

        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.markdown(f"#### 2. Year-over-Year Trend for {v_city}")
            try:
                yoy_data = conn.run_query(YEAR_OVER_YEAR_CYPHER, {"pollutant": v_pollutant, "city": v_city})
                if yoy_data:
                    yoy_df = pd.DataFrame(yoy_data)
                    fig_yoy = px.bar(
                        yoy_df,
                        x="year",
                        y="value",
                        color="year",
                        text="value",
                        title=f"{v_pollutant} Trend in {v_city}",
                        labels={"value": "Concentration (µg/m³)", "year": "Year"}
                    )
                    fig_yoy.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                    st.plotly_chart(fig_yoy, use_container_width=True)
                else:
                    st.info("No trend records available.")
            except Exception as e:
                st.error(f"Error querying trend: {e}")

        with col_t2:
            st.markdown(f"#### 3. All Pollutants in {v_city}")
            try:
                comp_data = conn.run_query(POLLUTANT_COMPARISON_CYPHER, {"city": v_city, "year": v_year})
                if comp_data:
                    comp_df = pd.DataFrame(comp_data)
                    fig_comp = px.bar(
                        comp_df,
                        x="pollutant",
                        y="value",
                        color="pollutant",
                        color_discrete_map={"PM10": "#f59e0b", "PM2.5": "#ef4444", "NO2": "#3b82f6", "SO2": "#10b981"},
                        text="value",
                        title=f"All Pollutant Levels in {v_city}",
                        labels={"value": "Concentration (µg/m³)", "pollutant": "Pollutant"}
                    )
                    fig_comp.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"))
                    st.plotly_chart(fig_comp, use_container_width=True)
                else:
                    st.info("No comparison records found.")
            except Exception as e:
                st.error(f"Error querying pollutant comparison: {e}")

        st.markdown(f"#### 4. Top Most Polluted Cities Ranking ({v_pollutant})")
        try:
            target_year = v_year if v_year else (year_list[-1] if year_list else 2023)
            top_data = conn.run_query(TOP_CITIES_RANKING_CYPHER, {"pollutant": v_pollutant, "year": target_year, "limit": 10})
            if top_data:
                top_df = pd.DataFrame(top_data)
                fig_top = px.bar(
                    top_df,
                    x="value",
                    y="city",
                    orientation="h",
                    color="value",
                    color_continuous_scale="Viridis",
                    title=f"Top 10 Cities Ranked by Highest {v_pollutant} ({target_year})",
                    labels={"value": f"{v_pollutant} Concentration (µg/m³)", "city": "City"}
                )
                fig_top.update_layout(paper_bgcolor="#1e293b", plot_bgcolor="#1e293b", font=dict(color="#f8fafc"), yaxis=dict(autorange="reversed"))
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info("No ranking records found.")
        except Exception as e:
            st.error(f"Error querying top ranking: {e}")

# ==========================================
# 8. PAGE: KNOWLEDGE GRAPH VISUALIZATION
# ==========================================
elif page == "🕸️ Knowledge Graph":
    st.markdown("### 🕸️ Interactive Knowledge Graph Topology")
    st.markdown("Explore real Neo4j nodes and semantic relationships dynamically with physics-based graph rendering.")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Connect in sidebar to explore the Knowledge Graph.")
    else:
        cities_res = conn.run_query(GET_ALL_CITIES_CYPHER)
        pollutants_res = conn.run_query(GET_ALL_POLLUTANTS_CYPHER)
        years_res = conn.run_query(GET_ALL_YEARS_CYPHER)

        city_opts = ["All"] + [r["city"] for r in cities_res if r.get("city")]
        pollutant_opts = ["All"] + [r["pollutant"] for r in pollutants_res if r.get("pollutant")]
        year_opts = ["All"] + [str(r["year"]) for r in years_res if r.get("year")]

        col_g1, col_g2, col_g3, col_g4 = st.columns(4)
        with col_g1:
            kg_city = st.selectbox("Filter City", city_opts)
        with col_g2:
            kg_pollutant = st.selectbox("Filter Pollutant", pollutant_opts)
        with col_g3:
            kg_year = st.selectbox("Filter Year", year_opts)
        with col_g4:
            kg_limit = st.slider("Max Node Limit", min_value=10, max_value=200, value=60, step=10)

        st.markdown(
            """
            <div style="display:flex; flex-wrap:wrap; gap:8px; margin-top:8px; margin-bottom:14px;">
                <span class="badge" style="background-color:#10b981;">🏛️ State</span>
                <span class="badge" style="background-color:#0284c7;">🏙️ City</span>
                <span class="badge" style="background-color:#f59e0b;">📡 MonitoringStation</span>
                <span class="badge" style="background-color:#8b5cf6;">📊 Reading</span>
                <span class="badge" style="background-color:#ef4444;">🌫️ Pollutant</span>
                <span class="badge" style="background-color:#14b8a6;">📅 DateTime</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        load_kg = st.button("🔄 Load / Refresh Knowledge Graph", type="primary", use_container_width=True)

        if load_kg or "kg_data" in st.session_state:
            if load_kg or "kg_data" not in st.session_state:
                with st.spinner("Extracting Knowledge Graph subgraph from Neo4j..."):
                    kg_params = {
                        "city": kg_city,
                        "pollutant": kg_pollutant,
                        "year": int(kg_year) if kg_year != "All" else None,
                        "limit": int(kg_limit)
                    }
                    records = conn.run_query(KNOWLEDGE_GRAPH_EXPLORER_CYPHER, parameters=kg_params)
                    st.session_state["kg_data"] = records

            records = st.session_state.get("kg_data", [])

            if records:
                st.success(f"Extracted {len(records)} connected graph paths from Neo4j.")

                viz_mode = st.radio("Visualization Engine", ["🌐 PyVis Physics Canvas (Interactive HTML)", "📊 Plotly 2D Network Graph"], horizontal=True)

                if "PyVis" in viz_mode:
                    html_graph = generate_pyvis_html(records, height="620px")
                    components.html(html_graph, height=640, scrolling=True)
                else:
                    plotly_fig = generate_plotly_graph(records)
                    st.plotly_chart(plotly_fig, use_container_width=True)

                with st.expander("🔎 View Subgraph Schema & Relationships"):
                    st.markdown("""
                    **Ontology Structure:**
                    ```
                    (:State {name})
                       │
                       └──[:HAS_CITY]──► (:City {name})
                                            │
                                            └──[:HAS_STATION]──► (:MonitoringStation {station_id})
                                                                    │
                                                                    └──[:HAS_READING]──► (:Reading {value, unit, year})
                                                                                            ├──[:MEASURES]────► (:Pollutant {name})
                                                                                            └──[:RECORDED_AT]─► (:DateTime {value})
                    ```
                    """)
            else:
                st.info("No matching graph nodes found for selected filters.")

# ==========================================
# 9. PAGE: CUSTOM QUERY
# ==========================================
elif page == "⚡ Custom Query":
    st.markdown("### ⚡ Custom Cypher Query Console")
    st.markdown("Execute custom Cypher queries directly against the Neo4j Knowledge Graph. (Restricted to read-only queries for safety).")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Please connect in the sidebar.")
    else:
        templates = {
            "Select a preset template query...": "",
            "1. List Top 10 Highest PM2.5 Readings": """MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant {name: 'PM2.5'})
RETURN c.name AS city, s.station_id AS station, r.year AS year, r.value AS pm25_val, r.unit AS unit
ORDER BY r.value DESC
LIMIT 10""",
            "2. Count Stations & Readings per City": """MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)
OPTIONAL MATCH (s)-[:HAS_READING]->(r:Reading)
RETURN c.name AS city, count(DISTINCT s) AS stations_count, count(r) AS readings_count
ORDER BY readings_count DESC""",
            "3. Average Pollutant Concentrations in 2023": """MATCH (r:Reading)-[:MEASURES]->(p:Pollutant)
WHERE r.year = 2023
RETURN p.name AS pollutant, round(avg(r.value), 2) AS avg_value, round(max(r.value), 2) AS max_value, head(collect(r.unit)) AS unit
ORDER BY avg_value DESC""",
            "4. Traverse Full Knowledge Graph Paths": """MATCH path = (st:State)-[:HAS_CITY]->(c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN c.name AS city, s.station_id AS station, p.name AS pollutant, r.value AS value, r.year AS year
LIMIT 20"""
        }

        sel_template = st.selectbox("📚 Sample Cypher Templates", list(templates.keys()))
        default_query = templates[sel_template] if sel_template in templates and templates[sel_template] else """MATCH (c:City)-[:HAS_STATION]->(s:MonitoringStation)-[:HAS_READING]->(r:Reading)-[:MEASURES]->(p:Pollutant)
RETURN c.name AS city, s.station_id AS station, r.year AS year, p.name AS pollutant, r.value AS value, r.unit AS unit
LIMIT 20"""

        user_cypher = st.text_area("Enter Cypher Query", value=default_query, height=180)

        col_q1, col_q2 = st.columns([1, 4])
        with col_q1:
            run_query_btn = st.button("⚡ Run Query", type="primary", use_container_width=True)

        if run_query_btn:
            is_valid, validation_msg = validate_custom_query(user_cypher)
            if not is_valid:
                st.error(f"⛔ Safety Warning: {validation_msg}")
            else:
                start_t = time.time()
                try:
                    query_res = conn.run_query(user_cypher, read_only=True)
                    elapsed_ms = (time.time() - start_t) * 1000

                    st.success(f"✅ Query executed successfully in **{elapsed_ms:.2f} ms** | Returned **{len(query_res):,} records**")

                    if query_res:
                        res_df = pd.DataFrame(query_res)
                        st.dataframe(res_df, use_container_width=True)

                        with st.expander("📦 View Raw JSON Response"):
                            st.json(query_res[:10])
                    else:
                        st.info("Query returned 0 rows.")

                except Exception as e:
                    st.error(f"❌ Cypher Execution Error: {str(e)}")

# ==========================================
# 10. PAGE: ADD DATA
# ==========================================
elif page == "➕ Add Data":
    st.markdown("### ➕ Add New Air Pollution Reading")
    st.markdown("Insert a new real-world pollution observation into the Neo4j Knowledge Graph via parameterized Cypher.")

    if not is_connected:
        st.warning("⚠️ Neo4j is not connected. Connect in sidebar to add data.")
    else:
        with st.form("add_reading_form", clear_on_submit=False):
            st.markdown("#### 📝 Observation Details")
            c_a1, c_a2, c_a3 = st.columns(3)
            with c_a1:
                in_state = st.text_input("State", value="Andhra Pradesh")
            with c_a2:
                in_city = st.text_input("City", value="Amaravati")
            with c_a3:
                in_station_id = st.text_input("Station ID", value="AP_AMARAVATI_INTEGRATED")

            c_b1, c_b2, c_b3 = st.columns(3)
            with c_b1:
                in_station_type = st.text_input("Station Type", value="Integrated city-level NAMP record")
            with c_b2:
                in_pollutant = st.selectbox("Pollutant", ["PM2.5", "PM10", "NO2", "SO2"])
            with c_b3:
                in_obs_date = st.text_input("Observation Date (ISO)", value="2023-12-31T23:59:59")

            c_c1, c_c2, c_c3 = st.columns(3)
            with c_c1:
                in_year = st.number_input("Year", min_value=2000, max_value=2030, value=2023, step=1)
            with c_c2:
                in_value = st.number_input("Measured Value", min_value=0.0, max_value=2000.0, value=35.0, step=0.1)
            with c_c3:
                in_unit = st.text_input("Unit", value="µg/m³")

            c_d1, c_d2 = st.columns(2)
            with c_d1:
                in_mtype = st.text_input("Measurement Type", value="Annual Average")
            with c_d2:
                in_freq = st.text_input("Frequency", value="Annual")

            in_source = st.text_input("Source", value="CPCB NAMP Ambient Air Quality Status")

            submit_data = st.form_submit_button("🚀 Add Reading to Neo4j Knowledge Graph", type="primary", use_container_width=True)

        if submit_data:
            if not in_state or not in_city or not in_station_id or not in_pollutant:
                st.error("Please fill in all mandatory fields (State, City, Station ID, Pollutant).")
            else:
                params = {
                    "state": in_state.strip(),
                    "city": in_city.strip(),
                    "station_id": in_station_id.strip(),
                    "station_type": in_station_type.strip(),
                    "pollutant": in_pollutant.strip(),
                    "observation_date": in_obs_date.strip(),
                    "year": int(in_year),
                    "value": float(in_value),
                    "unit": in_unit.strip(),
                    "measurement_type": in_mtype.strip(),
                    "frequency": in_freq.strip(),
                    "source": in_source.strip(),
                }

                with st.spinner("Executing parameterized Cypher write transaction in Neo4j..."):
                    try:
                        summary = conn.run_write(ADD_READING_CYPHER, parameters=params)
                        st.success(f"🎉 Reading successfully added to Knowledge Graph! (Nodes created: {summary['nodes_created']}, Relationships created: {summary['relationships_created']})")
                        st.cache_data.clear()

                        with st.expander("🔎 View Executed Write Cypher & Parameters"):
                            st.code(ADD_READING_CYPHER, language="cypher")
                            st.json(params)

                    except Exception as e:
                        st.error(f"Failed to write reading to Neo4j: {e}")

# ==========================================
# 11. PAGE: PRESENTATION DECK (8 SLIDES)
# ==========================================
elif page == "📑 Presentation Deck":
    st.markdown("### 📑 Academic Evaluation & Defense Presentation (8 Slides)")
    st.markdown("Complete 8-slide presentation deck covering Problem Statement, Graph Modeling, Cypher Queries, and Live Results.")

    pptx_bytes = generate_presentation_pptx()
    st.download_button(
        label="📥 Download Complete Presentation (.pptx)",
        data=pptx_bytes,
        file_name="air_pollution_monitor_presentation.pptx",
        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        type="primary"
    )

    st.markdown("---")

    slide_tabs = st.tabs([f"Slide {s['slide_num']}: {s['title'][:20]}..." for s in SLIDES_CONTENT])

    for i, tab in enumerate(slide_tabs):
        slide = SLIDES_CONTENT[i]
        with tab:
            st.markdown(f"## Slide {slide['slide_num']}: {slide['title']}")
            st.markdown(f"**{slide['subtitle']}**")
            st.markdown("---")

            col_s1, col_s2 = st.columns(2)
            sections = slide["sections"]

            for j, (h, b) in enumerate(sections):
                target_col = col_s1 if j % 2 == 0 else col_s2
                with target_col:
                    with st.container():
                        st.markdown(f"### 📌 {h}")
                        st.markdown(b)
                        st.markdown("<br>", unsafe_allow_html=True)
