import streamlit as st
import pandas as pd
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth
from auth.permissions import can_perform_action

st.set_page_config(page_title="Maintenance", page_icon="🔧", layout="wide")
user = require_auth('Maintenance')
st.title("🔧 Maintenance Tracking")

from utils.data_loader import load_maintenance_jobs
from utils.db_utils import db

try:
    maint_df = load_maintenance_jobs()
except Exception:
    if os.path.exists("data/maintenance_jobs.csv"):
        maint_df = pd.read_csv("data/maintenance_jobs.csv")
    else:
        maint_df = None

if maint_df is None:
    st.error("maintenance_jobs.csv not found! Check your data directory.")
else:
    # Filter controls
    col1, col2 = st.columns(2)
    with col1:
        pri_filter = st.multiselect("Filter by Priority", options=maint_df['Priority'].unique(), default=maint_df['Priority'].unique())
    with col2:
        status_filter = st.multiselect("Filter by Status", options=maint_df['Status'].unique(), default=maint_df['Status'].unique())
        
    filtered_df = maint_df[(maint_df['Priority'].isin(pri_filter)) & (maint_df['Status'].isin(status_filter))]
    
    total_open = len(filtered_df[filtered_df['Status'].isin(['Open', 'In Progress'])])
    high_pri_open = len(filtered_df[
        (filtered_df['Priority'] == 'High') &
        (filtered_df['Status'].isin(['Open', 'In Progress']))
    ])
    
    c1, c2 = st.columns(2)
    c1.metric("Total Open Jobs", total_open)
    c2.metric("High Priority Open Jobs", high_pri_open)
    
    st.dataframe(filtered_df, use_container_width=True)
    
    st.divider()
    st.subheader("Update Job Status")
    
    open_jobs = filtered_df[filtered_df['Status'] == 'Open']['Job_Card_ID'].tolist()
    
    if open_jobs:
        job_to_update = st.selectbox("Select Job Card to close", open_jobs)
        if can_perform_action(user['role'], 'update_maintenance'):
            if st.button("Mark as Closed") and job_to_update:
                maint_df.loc[maint_df['Job_Card_ID'] == job_to_update, 'Status'] = 'Closed'
                try:
                    db.update_record('maintenance_jobs', "status = 'Closed'", "job_id = %s", (job_to_update,))
                except Exception:
                    pass
                maint_df.to_csv("data/maintenance_jobs.csv", index=False)
                st.cache_data.clear()
                st.success(f"Job {job_to_update} marked as closed!")
                st.rerun()
        else:
            st.info("You don't have permission to close jobs (Maintenance Team role required).")
    else:
        st.info("No open jobs available to close under current filters.")
