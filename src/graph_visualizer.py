"""
Knowledge Graph Visualizer for Air Pollution Monitor
Generates interactive, physics-based network visualizations using PyVis and Plotly
directly from live Neo4j nodes and relationships.
"""
import os
import json
import networkx as nx
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional

NODE_COLORS = {
    "State": "#10b981",              # Emerald Green
    "City": "#0284c7",               # Sky Blue
    "MonitoringStation": "#f59e0b",  # Amber Orange
    "Reading": "#8b5cf6",            # Violet / Purple
    "Pollutant": "#ef4444",          # Crimson Red
    "DateTime": "#14b8a6",           # Teal
}

NODE_ICONS = {
    "State": "🏛️",
    "City": "🏙️",
    "MonitoringStation": "📡",
    "Reading": "📊",
    "Pollutant": "🌫️",
    "DateTime": "📅",
}


def build_networkx_graph(records: List[Dict[str, Any]]) -> nx.DiGraph:
    """Build a NetworkX DiGraph from Neo4j query records."""
    G = nx.DiGraph()

    for row in records:
        state = row.get("state_name") or "Andhra Pradesh"
        city = row.get("city_name")
        station = row.get("station_id")
        station_type = row.get("station_type", "NAMP Station")
        reading_id = str(row.get("reading_id", ""))
        val = row.get("reading_value")
        unit = row.get("reading_unit", "µg/m³")
        year = row.get("reading_year")
        pollutant = row.get("pollutant_name")
        date_str = str(row.get("datetime_value", ""))

        # 1. State Node
        state_id = f"State:{state}"
        if not G.has_node(state_id):
            G.add_node(state_id, label=state, group="State", title=f"State: {state}<br>Region: South India", size=30)

        # 2. City Node
        if city:
            city_id = f"City:{city}"
            if not G.has_node(city_id):
                G.add_node(city_id, label=city, group="City", title=f"City: {city}<br>State: {state}", size=24)
            G.add_edge(state_id, city_id, label="HAS_CITY", title="State contains City")

            # 3. Station Node
            if station:
                st_id = f"Station:{station}"
                if not G.has_node(st_id):
                    G.add_node(st_id, label=station.replace("AP_", "").replace("_INTEGRATED", ""), group="MonitoringStation",
                               title=f"Station ID: {station}<br>Type: {station_type}", size=18)
                G.add_edge(city_id, st_id, label="HAS_STATION", title="City operates Station")

                # 4. Reading Node
                if reading_id and val is not None:
                    rd_node_id = f"Reading:{reading_id}"
                    rd_label = f"{val} {unit}"
                    if not G.has_node(rd_node_id):
                        G.add_node(rd_node_id, label=rd_label, group="Reading",
                                   title=f"Reading: {val} {unit}<br>Year: {year}<br>Pollutant: {pollutant}", size=14)
                    G.add_edge(st_id, rd_node_id, label="HAS_READING", title="Station recorded Reading")

                    # 5. Pollutant Node
                    if pollutant:
                        pol_id = f"Pollutant:{pollutant}"
                        if not G.has_node(pol_id):
                            G.add_node(pol_id, label=pollutant, group="Pollutant",
                                       title=f"Pollutant: {pollutant}<br>Standard: CPCB Guidelines", size=22)
                        G.add_edge(rd_node_id, pol_id, label="MEASURES", title="Reading measures Pollutant")

                    # 6. DateTime Node
                    if date_str:
                        dt_id = f"DateTime:{date_str[:10]}"
                        if not G.has_node(dt_id):
                            G.add_node(dt_id, label=date_str[:10], group="DateTime",
                                       title=f"Timestamp: {date_str}", size=14)
                        G.add_edge(rd_node_id, dt_id, label="RECORDED_AT", title="Reading recorded at Date")

    return G


def generate_pyvis_html(records: List[Dict[str, Any]], height: str = "600px") -> str:
    """Generate standalone interactive PyVis physics graph HTML string."""
    from pyvis.network import Network

    G = build_networkx_graph(records)
    net = Network(height=height, width="100%", bgcolor="#0f172a", font_color="#f8fafc", directed=True)

    for node_id, data in G.nodes(data=True):
        group = data.get("group", "State")
        color = NODE_COLORS.get(group, "#94a3b8")
        net.add_node(
            node_id,
            label=f"{NODE_ICONS.get(group, '')} {data.get('label', node_id)}",
            title=data.get("title", node_id),
            color=color,
            size=data.get("size", 20),
            font={"size": 12, "color": "#f8fafc", "face": "sans-serif"}
        )

    for u, v, data in G.edges(data=True):
        net.add_edge(
            u, v,
            label=data.get("label", ""),
            title=data.get("title", ""),
            color={"color": "#64748b", "highlight": "#38bdf8"},
            arrows="to",
            font={"size": 9, "color": "#94a3b8", "align": "middle"}
        )

    # Configure physics for smooth organic clustering
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "shadow": true
      },
      "edges": {
        "smooth": {
          "type": "continuous",
          "roundness": 0.2
        },
        "shadow": false
      },
      "physics": {
        "forceAtlas2Based": {
          "gravitationalConstant": -60,
          "centralGravity": 0.01,
          "springLength": 90,
          "springConstant": 0.08,
          "damping": 0.95
        },
        "minVelocity": 0.75,
        "solver": "forceAtlas2Based",
        "timestep": 0.35,
        "stabilization": { "iterations": 150 }
      },
      "interaction": {
        "hover": true,
        "navigationButtons": true,
        "zoomView": true,
        "tooltipDelay": 150
      }
    }
    """)

    return net.generate_html()


def generate_plotly_graph(records: List[Dict[str, Any]]) -> go.Figure:
    """Generate an alternative Plotly 2D interactive spring-layout network graph."""
    G = build_networkx_graph(records)
    if len(G.nodes) == 0:
        fig = go.Figure()
        fig.add_annotation(text="No Graph Data Found Matching Filters", showarrow=False, font=dict(size=16, color="#94a3b8"))
        fig.update_layout(paper_bgcolor="#0f172a", plot_bgcolor="#0f172a")
        return fig

    pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

    # Edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1.2, color="#475569"),
        hoverinfo="none",
        mode="lines"
    )

    # Node traces grouped by entity type
    node_traces = []
    for group_name, color in NODE_COLORS.items():
        node_x = []
        node_y = []
        node_text = []
        node_labels = []

        for node in G.nodes():
            if G.nodes[node].get("group") == group_name:
                x, y = pos[node]
                node_x.append(x)
                node_y.append(y)
                data = G.nodes[node]
                node_labels.append(data.get("label", node))
                node_text.append(data.get("title", node).replace("<br>", "<br>"))

        if node_x:
            trace = go.Scatter(
                x=node_x, y=node_y,
                mode="markers+text",
                name=f"{NODE_ICONS.get(group_name, '')} {group_name}",
                marker=dict(
                    color=color,
                    size=[G.nodes[n].get("size", 16) for n in G.nodes() if G.nodes[n].get("group") == group_name],
                    line=dict(width=2, color="#ffffff"),
                    shadow=dict(color="rgba(0,0,0,0.5)", blur=4)
                ),
                text=node_labels,
                textposition="bottom center",
                textfont=dict(size=10, color="#f8fafc"),
                hoverinfo="text",
                hovertext=node_text
            )
            node_traces.append(trace)

    fig = go.Figure(
        data=[edge_trace] + node_traces,
        layout=go.Layout(
            title=dict(text="Interactive Knowledge Graph Topology", font=dict(color="#f8fafc", size=18)),
            showlegend=True,
            legend=dict(font=dict(color="#94a3b8"), bgcolor="rgba(15,23,42,0.8)", bordercolor="#334155"),
            hovermode="closest",
            margin=dict(b=20, l=10, r=10, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor="#0f172a",
            plot_bgcolor="#0f172a"
        )
    )
    return fig
