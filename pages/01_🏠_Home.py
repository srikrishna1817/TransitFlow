import streamlit as st
import pandas as pd
import datetime
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from utils.ui_theme import apply_theme
from components.custom_widgets import metric_card, breadcrumb, status_badge
from utils.keyboard_shortcuts import register_shortcuts

st.set_page_config(page_title="TransitFlow Home", page_icon="🚄", layout="wide", initial_sidebar_state="collapsed")
user = require_auth('Home')

apply_theme()
register_shortcuts()

# Breadcrumb
breadcrumb(["TransitFlow Home", "Executive Dashboard"])

# Hero Banner
now_ts = datetime.datetime.now()
st.markdown(f"""
<div class="hero-banner">
    <div>
        <h1 class="hero-title">Welcome back, {user.get('username', 'Executive').capitalize()}!</h1>
        <p class="hero-subtitle">Metro Rail Command Center — Fleet Operations Overview</p>
    </div>
    <div style="text-align: right;">
        <div style="color: #10B981; font-weight: 600; font-size: 1.1rem; display: flex; align-items: center; justify-content: flex-end; gap: 8px;">
            <div style="width:10px;height:10px;background:#10B981;border-radius:50%;box-shadow:0 0 10px #10B981;animation:pulse 2s infinite;"></div>
            Systems Operational
        </div>
        <div style="color: #64748B; font-size: 0.9rem; margin-top: 5px;">Last updated: {now_ts.strftime('%H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

st.caption("Real-time fleet health, maintenance status, and quick actions for operations staff.")
st.divider()

from utils.data_loader import load_trains_data, load_maintenance_jobs, load_certificates_data
trains_df = load_trains_data()
maint_df = load_maintenance_jobs()
cert_df = load_certificates_data()

if trains_df is None or trains_df.empty:
    st.error("❌ Error loading data files. Please check the data/ directory.")
else:
    # KPIs
    total_fleet = len(trains_df)
    in_service = len(trains_df[trains_df['Status'] == 'Active'])
    in_maint = len(trains_df[trains_df['Status'] == 'Maintenance'])
    
    # Average health score (based on open maintenance priority)
    total_issues = len(maint_df[maint_df['Status'] == 'Open'])
    health_score = max(0.0, 100.0 - (total_issues / total_fleet) * 15.0)

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Total Fleet Size", str(total_fleet), None, "#3B82F6")
    with col2:
        metric_card("Trains in Service", str(in_service), None, "#10B981")
    with col3:
        metric_card("Trains in Maintenance", str(in_maint), None, "#F59E0B")
    with col4:
        metric_card("Avg Fleet Health", f"{health_score:.1f}%", None, "#10B981" if health_score >= 80 else "#F59E0B")

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    
    colA, colB, colC = st.columns([1.2, 1, 1])
    with colA:
        st.markdown("<div class='panel-title'>⚡ Quick Actions</div>", unsafe_allow_html=True)
        st.markdown("<div style='margin-bottom:15px; color:#94A3B8;'>Select an operation to jump directly to the module.</div>", unsafe_allow_html=True)
        
        ac1, ac2 = st.columns(2)
        with ac1:
            if st.button("📅 Generate Schedule", use_container_width=True, type="primary"):
                st.switch_page("pages/02_📅_Schedule.py")
        with ac2:
            if st.button("🚨 View Alerts", use_container_width=True):
                st.switch_page("pages/04_🚨_Alerts.py")
                
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🤖 Launch ML Diagnostics", use_container_width=True):
            st.switch_page("pages/07_🤖_ML_Insights.py")
            
    with colB:
        st.markdown("<div class='panel-title'>🔧 High-Priority Jobs</div>", unsafe_allow_html=True)
        high_pri_jobs = len(maint_df[(maint_df['Priority'] == 'High') & (maint_df['Status'] == 'Open')])
        if high_pri_jobs > 0:
            status_badge("Critical")
            st.markdown(f"""
            <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3); padding: 15px; border-radius: 12px; margin-top: 15px;">
                <h4 style="color:#F8FAFC;margin:0 0 5px 0;">Attention Required</h4>
                <p style="color:#E2E8F0;margin:0;"><b>{high_pri_jobs} trains</b> demand immediate structural repair or assessment.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            status_badge("Success")
            st.markdown("""
            <div style="background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.3); padding: 15px; border-radius: 12px; margin-top: 15px;">
                <p style="color:#E2E8F0;margin:0;">All high-priority jobs have been successfully resolved. The fleet is stable.</p>
            </div>
            """, unsafe_allow_html=True)
        
    with colC:
        st.markdown("<div class='panel-title'>📜 Certificate Alerts</div>", unsafe_allow_html=True)
        cert_df['Valid_Until'] = pd.to_datetime(cert_df['Valid_Until'])
        days_out = (cert_df['Valid_Until'] - now_ts).dt.days
        
        expired_count = len(cert_df[days_out < 0])
        expiring_soon = len(cert_df[(days_out >= 0) & (days_out <= 15)])
        
        if expired_count > 0:
            st.error(f"❌ Certificates Expired: {expired_count}")
        elif expiring_soon > 0:
            st.warning(f"⚠️ Expiring in ≤ 15 Days: {expiring_soon}")
        else:
            st.success("✅ All fleet certifications are up to date.")
            
        st.markdown("""
        <div style="background: rgba(30,41,59,0.5); padding: 12px; border-radius: 8px; font-size: 0.85rem; color: #94A3B8; margin-top: 15px; border-left: 3px solid #60A5FA;">
            Ensuring rolling stock compliance prevents operational halting and safety violations.
        </div>
        """, unsafe_allow_html=True)

    # Injecting the pulsing animation keyframes directly
    st.markdown("""
    <style>
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
        100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    </style>
    """, unsafe_allow_html=True)

from components.custom_widgets import render_page_nav
render_page_nav(None, None, 'pages/02_📅_Schedule.py', '📅 Schedule')
