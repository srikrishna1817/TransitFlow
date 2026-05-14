import streamlit as st
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from auth.permissions import can_perform_action

from utils.ui_theme import apply_theme

st.set_page_config(page_title="Maintenance Tracking", page_icon="🔧", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
user = require_auth('Maintenance')
st.title("🔧 Maintenance Tracking")
st.caption("Monitor, filter, and update maintenance job cards across the entire fleet.")
st.divider()

from utils.data_loader import load_maintenance_jobs
from utils.db_utils import db

with st.spinner("🔄 Loading maintenance jobs..."):
    try:
        maint_df = load_maintenance_jobs()
    except Exception:
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        csv_path = os.path.join(BASE_DIR, "data/maintenance_jobs.csv")
        if os.path.exists(csv_path):
            maint_df = pd.read_csv(csv_path)
        else:
            maint_df = None

if maint_df is None:
    st.error("❌ maintenance_jobs.csv not found! Check your data directory.")
else:
    # ── Live job counts (metric row) ─────────────────────────────
    open_total   = len(maint_df[maint_df['Status'] == 'Open'])
    in_progress  = len(maint_df[maint_df['Status'] == 'In Progress'])
    closed_total = len(maint_df[maint_df['Status'] == 'Closed'])

    m1, m2, m3 = st.columns(3)
    m1.metric("🔴 Open Jobs",        open_total)
    m2.metric("🟡 In Progress",      in_progress)
    m3.metric("✅ Closed Jobs",      closed_total)

    st.divider()

    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        pri_filter = st.multiselect("Filter by Priority", options=maint_df['Priority'].unique(), default=maint_df['Priority'].unique())
    with col2:
        status_filter = st.multiselect("Filter by Status", options=maint_df['Status'].unique(), default=maint_df['Status'].unique())
        
    filtered_df = maint_df[(maint_df['Priority'].isin(pri_filter)) & (maint_df['Status'].isin(status_filter))]

    # Table — show first 10, expander for all
    with st.expander("📋 Show All Maintenance Jobs", expanded=False):
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)
    
    st.dataframe(filtered_df.head(10), use_container_width=True, hide_index=True)
    
    st.divider()
    st.subheader("Update Job Status")
    
    open_jobs = filtered_df[filtered_df['Status'] == 'Open']['Job_Card_ID'].tolist()
    
    if open_jobs:
        job_to_update = st.selectbox("Select Job Card to close", open_jobs)
        if can_perform_action(user['role'], 'update_maintenance'):
            if st.button("✅ Mark as Closed") and job_to_update:
                maint_df.loc[maint_df['Job_Card_ID'] == job_to_update, 'Status'] = 'Closed'
                try:
                    db.update_record('maintenance_jobs', "status = 'Closed'", "job_id = %s", (job_to_update,))
                except Exception:
                    pass
                maint_df.to_csv("data/maintenance_jobs.csv", index=False)
                st.cache_data.clear()
                st.success(f"✅ Job {job_to_update} marked as closed!")
                st.rerun()
        else:
            st.info("ℹ️ You don't have permission to close jobs (Maintenance Team role required).")
    else:
        st.info("ℹ️ No open jobs available to close under current filters.")
from components.custom_widgets import render_page_nav
render_page_nav('pages/02_📅_Schedule.py', '📅 Schedule', 'pages/04_🚨_Alerts.py', '🚨 Alerts')
