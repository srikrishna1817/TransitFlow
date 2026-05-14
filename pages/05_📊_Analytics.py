import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from utils.ui_theme import apply_theme

st.set_page_config(page_title="Analytics Dashboard", page_icon="📊", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
user = require_auth('Analytics')
st.title("📊 Analytics Dashboard")
st.caption("Fleet status distribution, maintenance risk profiles, and certificate expiry timelines.")
st.divider()

from utils.data_loader import load_trains_data, load_historical_operations, load_certificates_data
from scheduler import generate_schedule

@st.cache_data(ttl=600)
def load_all_data():
    try:
        return load_trains_data(), load_historical_operations(), load_certificates_data()
    except Exception:
        import os
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return (
            pd.read_csv(os.path.join(BASE_DIR, "data/trains_master.csv")),
            pd.read_csv(os.path.join(BASE_DIR, "data/historical_operations.csv")),
            pd.read_csv(os.path.join(BASE_DIR, "data/fitness_certificates.csv"))
        )

@st.cache_data(ttl=600)
def get_cached_schedule():
    """Cache the schedule so it doesn't regenerate on every page interaction."""
    return generate_schedule(required_service_trains=45)

try:
    with st.spinner("🔄 Loading fleet data..."):
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
        with st.spinner("📊 Loading risk profile..."):
            schedule_df, _ = get_cached_schedule()
            
        risk_df = schedule_df[['Train_ID', 'AI_Risk_Percent']].sort_values('AI_Risk_Percent', ascending=False).head(15)
        fig_bar = px.bar(risk_df, x='Train_ID', y='AI_Risk_Percent', 
                         title="Top 15 Trains by AI Maintenance Risk (%)", 
                         labels={'Train_ID': 'Train', 'AI_Risk_Percent': 'Risk Score (%)'},
                         color='AI_Risk_Percent', color_continuous_scale='Reds')
        st.plotly_chart(fig_bar, use_container_width=True)
    


except Exception as e:
    st.error(f"⚠️ Error loading analytics data: {e}. If Plotly is missing, install it with 'pip install plotly'.")

from components.custom_widgets import render_page_nav
render_page_nav('pages/04_🚨_Alerts.py', '🚨 Alerts', 'pages/06_📈_Predictive_Analytics.py', '📈 Predictive Analytics')
