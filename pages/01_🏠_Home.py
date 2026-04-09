import streamlit as st
import pandas as pd
import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from utils.ui_theme import apply_theme
from components.custom_widgets import metric_card, breadcrumb, status_badge
from utils.keyboard_shortcuts import register_shortcuts

st.set_page_config(page_title="HMRL Home", page_icon="🏠", layout="wide")
user = require_auth('Home')

apply_theme()
register_shortcuts()

breadcrumb(["TransitFlow Home", "Executive Dashboard"])
st.title(f"🏠 Welcome back, {user.get('username', 'User').capitalize()}!")
st.caption(f"Last interactive session: {datetime.datetime.now().strftime('%d %B %Y, %I:%M %p')}  |  🟢 Systems Operational")
try:
    from utils.data_loader import load_trains_data, load_maintenance_jobs, load_certificates_data
    trains_df = load_trains_data()
    maint_df = load_maintenance_jobs()
    cert_df = load_certificates_data()
except Exception as e:
    # Original fallback
    # @st.cache_data
    # def load_data():
    #     try:
    #         trains_df = pd.read_csv("data/trains_master.csv")
    #         maint_df = pd.read_csv("data/maintenance_jobs.csv")
    #         cert_df = pd.read_csv("data/fitness_certificates.csv")
    #         return trains_df, maint_df, cert_df
    #     except Exception as e:
    #         return None, None, None
    trains_df = pd.read_csv("data/trains_master.csv")
    maint_df = pd.read_csv("data/maintenance_jobs.csv")
    cert_df = pd.read_csv("data/fitness_certificates.csv")

if trains_df is None:
    st.error("Error loading data files. Please check the data/ directory.")
else:
    # KPIs
    total_fleet = len(trains_df)
    in_service = len(trains_df[trains_df['Status'] == 'Active'])
    in_maint = len(trains_df[trains_df['Status'] == 'Maintenance'])
    
    # Average health score (based on open maintenance priority)
    total_issues = len(maint_df[maint_df['Status'] == 'Open'])
    health_score = max(0.0, 100.0 - (total_issues / total_fleet) * 15.0)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Fleet Size", str(total_fleet), "+0", "#0066CC")
    with col2:
        metric_card("Trains in Service", str(in_service), "+2", "#00CC66")
    with col3:
        metric_card("Trains in Maintenance", str(in_maint), "-1", "#FF6B35")
    with col4:
        metric_card("Avg Fleet Health", f"{health_score:.1f}%", "+0.2%", "#00CC66" if health_score >= 80 else "#FF6B35")

    st.divider()
    
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        st.subheader("⚡ Quick Actions")
        if st.button("📅 Generate Today's Schedule", use_container_width=True, type="primary"):
            st.switch_page("pages/02_📅_Schedule.py")
        if st.button("🚨 View Critical Alerts", use_container_width=True):
            st.switch_page("pages/04_🚨_Alerts.py")
            
    with colB:
        st.subheader("🔧 Open High-Priority Jobs")
        high_pri_jobs = len(maint_df[(maint_df['Priority'] == 'High') & (maint_df['Status'] == 'Open')])
        if high_pri_jobs > 0:
            status_badge("Critical")
            st.markdown(f"**{high_pri_jobs} trains** currently demand immediate structural repair or assessment. Please contact Floor Management.")
        else:
            status_badge("Success")
            st.markdown("All high-priority jobs have been successfully resolved!")
        
    with colC:
        st.subheader("📜 Certificate Alerts")
        now = datetime.datetime.now()
        cert_df['Valid_Until'] = pd.to_datetime(cert_df['Valid_Until'])
        days_out = (cert_df['Valid_Until'] - now).dt.days
        
        expired_count = len(cert_df[days_out < 0])
        expiring_soon = len(cert_df[(days_out >= 0) & (days_out <= 15)])
        
        if expired_count > 0:
            st.error(f"❌ Certificates Completely Expired: {expired_count}")
        elif expiring_soon > 0:
            st.warning(f"⚠️ Certificates Expiring in ≤ 15 Days: {expiring_soon}")
        else:
            st.success("All Fleet certifications are up to date.")

    st.divider()
    
    st.markdown("### 📢 What's New inside TransitFlow v1.1")
    st.info("• Automated Data Quality Scanning\n• Machine Learning Heatmap Simulations\n• Advanced HMRL Branding Subsystem\n• Keyboard Actions (Ctrl+S / Generate)")
