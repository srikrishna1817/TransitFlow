import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time
import random
import sys, os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from utils.ui_theme import apply_theme

st.set_page_config(page_title="HMRL Live Simulation", page_icon="🚇", layout="wide")
apply_theme()
user = require_auth('Simulation')

# ─────────────────────────────────────────────────────────────────────────────
# NETWORK DATA — Real HMRL Metro Station Topology
# ─────────────────────────────────────────────────────────────────────────────
RED_STATIONS = [
    "Miyapur", "JNTU College", "KPHB Colony", "Kukatpally",
    "Dr. B. R. Ambedkar Balanagar", "Moosapet", "Bharat Nagar",
    "Erragadda", "ESI Hospital", "S.R. Nagar", "Ameerpet",
    "Punjagutta", "Irrum Manzil", "Khairatabad", "Lakdi-ka-pul",
    "Assembly", "Nampally", "Gandhi Bhavan", "Osmania Medical College",
    "MG Bus Station", "Malakpet", "New Market", "Musarambagh",
    "Dilsukhnagar", "Chaitanyapuri", "Victoria Memorial", "LB Nagar"
]

BLUE_STATIONS = [
    "Raidurg", "HITEC City", "Durgam Cheruvu", "Madhapur",
    "Peddamma Gudi", "Jubilee Hills Check Post", "Road No.5 Jubilee Hills", "Yusufguda",
    "Madhura Nagar", "Ameerpet", "Begumpet", "Prakash Nagar", "Rasoolpura",
    "Paradise", "JBS Parade Ground", "Secunderabad East", "Mettuguda",
    "Tarnaka", "Habsiguda", "NGRI", "Stadium", "Uppal", "Nagole"
]

GREEN_STATIONS = [
    "JBS Parade Ground", "Secunderabad West", "Gandhi Hospital", 
    "Musheerabad", "RTC X Roads", "Chikkadpally", "Narayanaguda", 
    "Sultan Bazaar", "MG Bus Station"
]

INTERCHANGE_STATIONS = {
    "Ameerpet": "Red + Blue",
    "JBS Parade Ground": "Blue + Green",
    "MG Bus Station": "Red + Green"
}

LINE_COLORS = {
    "Red":   "#E63946",
    "Blue":  "#457B9D",
    "Green": "#52b788", # Made slightly brighter for better contrast on dark map
}

SPEED_MAP = {"Slow": 3.0, "Normal": 2.0, "Fast": 1.0}

# ─────────────────────────────────────────────────────────────────────────────
# GEOGRAPHIC COORDINATE INTERPOLATION TO MIMIC REAL MAP
# ─────────────────────────────────────────────────────────────────────────────
def build_station_coords():
    coords = {}
    
    def interp(p_start, p_end, n):
        if n == 1: return [p_start]
        pts = []
        dx = (p_end[0] - p_start[0]) / (n - 1)
        dy = (p_end[1] - p_start[1]) / (n - 1)
        for i in range(n):
            pts.append((p_start[0] + dx * i, p_start[1] + dy * i))
        return pts

    # Red Line: Diagonal from top-left to bottom-right
    red_pts = interp((-10, 8), (-2, 2), 11) + interp((-2, 2), (2.5, -2.5), 10)[1:] + interp((2.5, -2.5), (9.5, -8.5), 8)[1:]
    for i, s in enumerate(RED_STATIONS):
        coords[("Red", s)] = red_pts[i]
        
    # Blue Line: Winding left to right crossing Red at Ameerpet
    blue_pts = interp((-11, 2), (-2, 2), 10) + interp((-2, 2), (3, 6), 6)[1:] + interp((3, 6), (12, 1), 9)[1:]
    for i, s in enumerate(BLUE_STATIONS):
        coords[("Blue", s)] = blue_pts[i]
        
    # Green Line: Straight down from JBS Parade Ground to MG Bus Station
    green_pts = interp((3, 6), (2.5, -2.5), 9)
    for i, s in enumerate(GREEN_STATIONS):
        coords[("Green", s)] = green_pts[i]
        
    return coords

STATION_COORDS = build_station_coords()

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISATION
# ─────────────────────────────────────────────────────────────────────────────
def _make_trains():
    trains = []
    # Red: 6 trains
    for i in range(6):
        start = i * 4 % len(RED_STATIONS)
        trains.append({
            "id": f"R-{i+1:02d}", "line": "Red",
            "stations": RED_STATIONS, "station_idx": start, "direction": 1,
            "status": "On Time", "skip_ticks": 0, "disrupted_ticks": 0,
        })
    # Blue: 4 trains
    for i in range(4):
        start = i * 5 % len(BLUE_STATIONS)
        trains.append({
            "id": f"B-{i+1:02d}", "line": "Blue",
            "stations": BLUE_STATIONS, "station_idx": start, "direction": 1,
            "status": "On Time", "skip_ticks": 0, "disrupted_ticks": 0,
        })
    # Green: 3 trains
    for i in range(3):
        start = i * 2 % len(GREEN_STATIONS)
        trains.append({
            "id": f"G-{i+1:02d}", "line": "Green",
            "stations": GREEN_STATIONS, "station_idx": start, "direction": 1,
            "status": "On Time", "skip_ticks": 0, "disrupted_ticks": 0,
        })
    return trains

def _init_state():
    if "sim_trains" not in st.session_state:
        st.session_state.sim_trains = _make_trains()
    if "sim_running" not in st.session_state:
        st.session_state.sim_running = False
    if "sim_tick" not in st.session_state:
        st.session_state.sim_tick = 0
    if "sim_speed" not in st.session_state:
        st.session_state.sim_speed = "Normal"
    if "stat_delays" not in st.session_state:
        st.session_state.stat_delays = {"Red": 0, "Blue": 0, "Green": 0}
    if "stat_disruptions" not in st.session_state:
        st.session_state.stat_disruptions = {"Red": 0, "Blue": 0, "Green": 0}
    if "stat_total_delays" not in st.session_state:
        st.session_state.stat_total_delays = 0
    if "stat_total_disruptions" not in st.session_state:
        st.session_state.stat_total_disruptions = 0

_init_state()

# ─────────────────────────────────────────────────────────────────────────────
# TRAIN STATE MACHINE
# ─────────────────────────────────────────────────────────────────────────────
def tick_trains():
    """Advance every train by one simulation tick with stochastic anomalies."""
    for t in st.session_state.sim_trains:
        n = len(t["stations"])

        if t["disrupted_ticks"] > 0:
            t["disrupted_ticks"] -= 1
            if t["disrupted_ticks"] == 0: t["status"] = "On Time"
            continue 

        if t["skip_ticks"] > 0:
            t["skip_ticks"] -= 1
            continue

        roll = random.random()
        if roll < 0.05 and t["status"] != "Disrupted":
            t["status"] = "Disrupted"
            t["disrupted_ticks"] = 3
            st.session_state.stat_disruptions[t["line"]] += 1
            st.session_state.stat_total_disruptions += 1
            continue
        elif roll < 0.15 and t["status"] == "On Time":
            t["status"] = "Delayed"
            t["skip_ticks"] = 1
            st.session_state.stat_delays[t["line"]] += 1
            st.session_state.stat_total_delays += 1
            continue
        else:
            if t["status"] == "Delayed": t["status"] = "On Time"

        new_idx = t["station_idx"] + t["direction"]
        if new_idx >= n:
            t["direction"] = -1
            new_idx = n - 2
        elif new_idx < 0:
            t["direction"] = 1
            new_idx = 1
        t["station_idx"] = new_idx

    st.session_state.sim_tick += 1

# ─────────────────────────────────────────────────────────────────────────────
# MAP BUILDER
# ─────────────────────────────────────────────────────────────────────────────
def build_map_figure():
    fig = go.Figure()

    # Track Paths
    for line_name, stations in [("Red", RED_STATIONS), ("Blue", BLUE_STATIONS), ("Green", GREEN_STATIONS)]:
        xs = [STATION_COORDS[(line_name, s)][0] for s in stations]
        ys = [STATION_COORDS[(line_name, s)][1] for s in stations]

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="lines",
            line=dict(color=LINE_COLORS[line_name], width=4, shape='spline', smoothing=1.3),
            name=f"{line_name} Line", hoverinfo="skip", showlegend=True,
        ))

        # Station Nodes
        colors, sizes, symbols, hover_texts = [], [], [], []
        for s in stations:
            is_xchange = s in INTERCHANGE_STATIONS
            colors.append("#FFD700" if is_xchange else LINE_COLORS[line_name])
            sizes.append(14 if is_xchange else 8)
            symbols.append("circle-open" if is_xchange else "circle")
            if is_xchange:
                hover_texts.append(f"<b>🔄 {s}</b><br>Interchange: {INTERCHANGE_STATIONS[s]}")
            else:
                hover_texts.append(f"<b>{s}</b><br>{line_name} Line")

        fig.add_trace(go.Scatter(
            x=xs, y=ys, mode="markers",
            marker=dict(color=colors, size=sizes, symbol=symbols, line=dict(color="white", width=1.5)),
            text=hover_texts, hovertemplate="%{text}<extra></extra>", showlegend=False,
        ))

    # Live Trains
    status_color = {"On Time": "#00FF88", "Delayed": "#FFD700", "Disrupted": "#FF4444"}
    for t in st.session_state.sim_trains:
        station_name = t["stations"][t["station_idx"]]
        xpos, ypos = STATION_COORDS.get((t["line"], station_name), (0, 0))

        arrow = "➜" if t["direction"] == 1 else "⬅"
        hover = (f"<b>{t['id']}</b><br>Station: {station_name}<br>"
                 f"Direction: {arrow}<br>Status: {t['status']}")
                 
        fig.add_trace(go.Scatter(
            x=[xpos], y=[ypos], mode="markers+text",
            marker=dict(color=status_color.get(t["status"], "#fff"), size=18, symbol="square", line=dict(color="white", width=1.5)),
            text=[t["id"]], textposition="top center", textfont=dict(size=10, color="white"),
            name=t["id"], hovertemplate=hover + "<extra></extra>", showlegend=False,
        ))

    fig.update_layout(
        title=dict(text="🚇 Geographical HMRL Metro Network — Active Fleet Dispatch", font=dict(size=18, color="#e8f4fd"), x=0.5),
        paper_bgcolor="#0b1727", plot_bgcolor="#0b1727", font=dict(color="#e8f4fd"),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-12, 13]),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, range=[-11, 10], scaleanchor="x", scaleratio=1),
        legend=dict(bgcolor="rgba(0,0,0,0.6)", bordercolor="#457B9D", borderwidth=1, font=dict(color="#e8f4fd"), x=0.02, y=0.98),
        margin=dict(l=20, r=20, t=60, b=20),
        height=650,
    )

    fig.add_annotation(
        text="🟡 Gold rings = Interchange Stations | 🟩 Green Sq = On Time | 🟨 Sq = Delayed | 🟥 Sq = Disrupted",
        xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False, font=dict(size=12, color="#94a3b8"), align="center",
    )

    return fig

# ─────────────────────────────────────────────────────────────────────────────
# PAGE DECORATION & LAYOUT
# ─────────────────────────────────────────────────────────────────────────────
st.title("🚇 HMRL Metro Live Simulation")

st.info("""
**📖 Overview & Purpose:**  
Welcome to the Live Simulation interface. This module visually validates your fleet assignments by translating statistical data into a real-time tracking interface mirroring the true physical geography of the Hyderabad Metro. 

By observing the network with stochastic real-world anomalies (like 5% disruption rates), dispatchers can identify bottleneck stress points near interchanges (Ameerpet / Parade Ground) and track how delays cascade across different routes dynamically.
""")

# Sidebar
with st.sidebar:
    st.markdown("### ⚙️ Engine Controls")

    col_start, col_reset = st.columns(2)
    with col_start:
        btn_label = "⏹ Pause" if st.session_state.sim_running else "▶ Play"
        btn_type = "secondary" if st.session_state.sim_running else "primary"
        if st.button(btn_label, use_container_width=True, type=btn_type):
            st.session_state.sim_running = not st.session_state.sim_running
            
    with col_reset:
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.sim_trains = _make_trains()
            st.session_state.sim_tick = 0
            st.session_state.sim_running = False
            st.session_state.stat_delays = {"Red": 0, "Blue": 0, "Green": 0}
            st.session_state.stat_disruptions = {"Red": 0, "Blue": 0, "Green": 0}
            st.session_state.stat_total_delays = 0
            st.session_state.stat_total_disruptions = 0

    st.session_state.sim_speed = st.select_slider(
        "Simulation Speed", options=["Slow", "Normal", "Fast"],
        value=st.session_state.sim_speed
    )
    
    st.divider()
    st.markdown(f"**🕐 Network Clock:** `T+{st.session_state.sim_tick}` updates")
    st.markdown(f"**Status:** {'🟢 Active Stream' if st.session_state.sim_running else '🔴 Standby'}")

# Main body placeholders
map_placeholder = st.empty()

# Placed directly underneath the map as requested to get it out of the side panel
st.divider()
col_left, col_right = st.columns([1, 1.3])

with col_left:
    st.subheader("🚦 Live Train Roster")
    status_placeholder = st.empty()

with col_right:
    st.subheader("📊 Network Anomaly Detection")
    stat_meta_placeholder = st.empty()
    stat_chart_placeholder = st.empty()

def build_status_df():
    rows = []
    for t in st.session_state.sim_trains:
        arrow = "➜" if t["direction"] == 1 else "⬅"
        rows.append({
            "Train": t["id"],
            "Line": t["line"],
            "Station Node": t["stations"][t["station_idx"]],
            "Dir": arrow,
            "Health Status": t["status"],
        })
    return pd.DataFrame(rows)

def style_status_row(val):
    if val == "On Time": return "background-color:#1a3a2a;color:#00FF88;font-weight:bold"
    if val == "Delayed": return "background-color:#3a3010;color:#FFD700;font-weight:bold"
    if val == "Disrupted": return "background-color:#3a1010;color:#FF4444;font-weight:bold"
    return ""

def render_frame():
    # 1. Map Render
    map_placeholder.plotly_chart(build_map_figure(), use_container_width=True, key=f"m_{st.session_state.sim_tick}")

    # 2. Status Table Render (Middle)
    status_df = build_status_df()
    styled = status_df.style.applymap(style_status_row, subset=["Health Status"])
    status_placeholder.dataframe(styled, use_container_width=True, height=360)

    # 3. Disruption Block Render
    on_time_count = sum(1 for t in st.session_state.sim_trains if t["status"] == "On Time")
    with stat_meta_placeholder.container():
        m1, m2, m3 = st.columns(3)
        m1.metric("✅ Trains Active", on_time_count, delta=f"{on_time_count}/{len(st.session_state.sim_trains)}")
        m2.metric("⚠️ Total Delays", st.session_state.stat_total_delays)
        m3.metric("🚨 Fleet Disruptions", st.session_state.stat_total_disruptions)

    chart_df = pd.DataFrame({
        "Line": list(st.session_state.stat_disruptions.keys()),
        "Disruptions": list(st.session_state.stat_disruptions.values()),
        "Delays": list(st.session_state.stat_delays.values()),
    })
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(x=chart_df["Line"], y=chart_df["Disruptions"], name="Disruptions", marker_color=["#E63946", "#457B9D", "#52b788"]))
    fig_bar.add_trace(go.Bar(x=chart_df["Line"], y=chart_df["Delays"], name="Delays", marker_color=["#ff8fa3", "#a8c7da", "#95d5b2"]))
    fig_bar.update_layout(
        barmode="group",
        paper_bgcolor="#0b1727", plot_bgcolor="#0b1727", font=dict(color="#e8f4fd"),
        margin=dict(l=10, r=10, t=10, b=20), height=255,
        legend=dict(bgcolor="rgba(0,0,0,0.3)"),
    )
    stat_chart_placeholder.plotly_chart(fig_bar, use_container_width=True, key=f"b_{st.session_state.sim_tick}")

# ─────────────────────────────────────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────────────────────────────────────
try:
    if st.session_state.sim_running:
        tick_trains()
        render_frame()
        time.sleep(SPEED_MAP.get(st.session_state.sim_speed, 2.0))
        st.rerun()
    else:
        render_frame()
except Exception as e:
    st.error(f"Simulation suspended: {e}")
    st.session_state.sim_running = False
    render_frame()
