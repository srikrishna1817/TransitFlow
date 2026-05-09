import streamlit as st
import pandas as pd
import plotly.express as px
from scheduler import generate_schedule
import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from utils.ui_theme import apply_theme

st.set_page_config(page_title="Analytics", page_icon="📊", layout="wide")
apply_theme()
user = require_auth('Analytics')
st.title("📊 Analytics Dashboard")

from utils.data_loader import load_trains_data, load_historical_operations, load_certificates_data

@st.cache_data
def load_all_data():
    try:
        return load_trains_data(), load_historical_operations(), load_certificates_data()
    except Exception:
        return (
            pd.read_csv("data/trains_master.csv"),
            pd.read_csv("data/historical_operations.csv"),
            pd.read_csv("data/fitness_certificates.csv")
        )

try:
    trains_df, hist_df, cert_df = load_all_data()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Fleet Status Distribution")
        status_counts = trains_df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_pie = px.pie(status_counts, names='Status', values='Count', hole=0.4, title="Current Fleet Assignment Status")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col2:
        st.subheader("Maintenance Risk Levels")
        # Generate schedule implicitly to get risk percentages
        with st.spinner("Generating AI risk profile..."):
            schedule_df, _ = generate_schedule(required_service_trains=45)
            
        risk_df = schedule_df[['Train_ID', 'AI_Risk_Percent']].sort_values('AI_Risk_Percent', ascending=False).head(15)
        fig_bar = px.bar(risk_df, x='Train_ID', y='AI_Risk_Percent', 
                         title="Top 15 Trains by AI Maintenance Risk (%)", 
                         labels={'Train_ID': 'Train', 'AI_Risk_Percent': 'Risk Score (%)'},
                         color='AI_Risk_Percent', color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)
    
    st.divider()
    
    col_hm, col_line = st.columns([1, 1.2])
    
    with col_hm:
        st.subheader("Interchange Bottleneck Heatmap")
        st.caption("Live train density at key network junctions.")
        
        station_counts = {s: 0 for s in ["Ameerpet", "Secunderabad", "JBS Parade Ground", "MGBS", "Miyapur", "LB Nagar", "Raidurg", "Nagole"]}
        sim_trains = st.session_state.get("sim_trains", [])
        for t in sim_trains:
            s = t["stations"][t["station_idx"]]
            if s in station_counts:
                station_counts[s] += 1
            elif "Secunderabad" in s:
                station_counts["Secunderabad"] += 1
            elif "MG Bus Station" in s:
                station_counts["MGBS"] += 1
                
        stations_list = list(station_counts.keys())
        counts_list = list(station_counts.values())
        
        z_vals = [counts_list[0:4], counts_list[4:8]]
        text_vals = [
            [f"{stations_list[i]}<br>{counts_list[i]} trains" for i in range(4)],
            [f"{stations_list[i]}<br>{counts_list[i]} trains" for i in range(4, 8)]
        ]
        
        colors = []
        for c in counts_list:
            if c <= 1: colors.append(0)
            elif c <= 3: colors.append(1)
            else: colors.append(2)
        z_colors = [colors[0:4], colors[4:8]]
        
        import plotly.graph_objects as go
        custom_colorscale = [[0.0, '#34D399'], [0.5, '#FBBF24'], [1.0, '#F87171']]
        
        fig_hm = go.Figure(data=go.Heatmap(
            z=z_colors,
            text=text_vals,
            texttemplate="%{text}",
            colorscale=custom_colorscale,
            showscale=False,
            zmin=0, zmax=2,
            xgap=5, ygap=5
        ))
        fig_hm.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, autorange="reversed"),
            height=300,
            margin=dict(t=10, b=10, l=10, r=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)"
        )
        st.plotly_chart(fig_hm, use_container_width=True)

    with col_line:
        st.subheader("Historical Mileage Trends (Last 90 Days)")
        # group by date
        hist_daily = hist_df.groupby('Date')['Kilometers_Run'].sum().reset_index()
        hist_daily['Date'] = pd.to_datetime(hist_daily['Date'])
        hist_daily = hist_daily.sort_values('Date')
        fig_line = px.line(hist_daily, x='Date', y='Kilometers_Run', 
                           title="Total Daily Kilometers Run Fleet-Wide",
                           markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    
    st.divider()
    
    st.subheader("Certificate Expiry Timeline")
    now = datetime.datetime.now()
    cert_df['Valid_Until'] = pd.to_datetime(cert_df['Valid_Until'])
    cert_df['Days_To_Expiry'] = (cert_df['Valid_Until'] - now).dt.days
    cert_timeline = cert_df[cert_df['Days_To_Expiry'] >= 0].sort_values('Days_To_Expiry')
    
    fig_hist = px.histogram(cert_timeline, x='Days_To_Expiry', nbins=20, 
                            title="Distribution of Upcoming Certificate Expiries", 
                            labels={'Days_To_Expiry': 'Days Until Expiry'},
                            color='Department')
    st.plotly_chart(fig_hist, use_container_width=True)

except Exception as e:
    st.error(f"Error loading analytics data: {e}. If Plotly is missing, install it with 'pip install plotly'.")
