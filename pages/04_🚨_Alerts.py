import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
from utils.data_loader import load_trains_data, load_maintenance_jobs, load_certificates_data, log_alert, get_active_alerts
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth

# Page Config
st.set_page_config(page_title="Alerts Dashboard", page_icon="🚨", layout="wide", initial_sidebar_state="collapsed")
user = require_auth('Alerts')

# Header
st.title("🚨 Real-Time Alerts & Notifications")
curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"Last System Scan: {curr_time}")

# --- DATA SCANNING ENGINE ---
@st.cache_data(ttl=120)
def scan_for_alerts():
    try:
        trains_df = load_trains_data()
        maint_df  = load_maintenance_jobs()
        cert_df   = load_certificates_data()
        
        all_alerts = []
        now = datetime.datetime.now()
        
        # 1. SCAN CERTIFICATES — vectorized
        cert_df['Valid_Until'] = pd.to_datetime(cert_df['Valid_Until'], errors='coerce')
        cert_df['Days_Until']  = (cert_df['Valid_Until'] - now).dt.days
        
        for _, row in cert_df[cert_df['Days_Until'] < 31].iterrows():
            d = int(row['Days_Until'])
            if d < 0:
                all_alerts.append({'Severity': 'CRITICAL', 'Category': 'Expired Certificate',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} certificate expired {-d} days ago.",
                    'Action': 'Ground train immediately', 'Timestamp': row['Valid_Until'].strftime('%Y-%m-%d')})
            elif d <= 7:
                all_alerts.append({'Severity': 'WARNING', 'Category': 'Certificate Expiry',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} cert expires in {d} days.",
                    'Action': 'Schedule renewal inspection', 'Timestamp': row['Valid_Until'].strftime('%Y-%m-%d')})
            else:
                all_alerts.append({'Severity': 'INFO', 'Category': 'Certificate Expiry',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} cert valid for {d} more days.",
                    'Action': 'Monitor for renewal', 'Timestamp': row['Valid_Until'].strftime('%Y-%m-%d')})

        # 2. SCAN MAINTENANCE JOBS — vectorized
        open_jobs = maint_df[maint_df['Status'] == 'Open']
        for _, row in open_jobs[open_jobs['Priority'] == 'High'].iterrows():
            all_alerts.append({'Severity': 'CRITICAL', 'Category': 'Critical Maintenance',
                'Train_ID': row['Train_ID'], 'Description': f"High-priority job {row['Job_Card_ID']} is still OPEN.",
                'Action': 'Assign technician immediately', 'Timestamp': 'N/A'})
        for _, row in open_jobs[open_jobs['Priority'] == 'Medium'].iterrows():
            all_alerts.append({'Severity': 'WARNING', 'Category': 'Open Maintenance',
                'Train_ID': row['Train_ID'], 'Description': f"Medium-priority job {row['Job_Card_ID']} pending.",
                'Action': 'Resolve within 48 hours', 'Timestamp': 'N/A'})

        # 3. SCAN MILEAGE — vectorized (skip slow schedule AI call)
        mileage_col = 'Current_Mileage' if 'Current_Mileage' in trains_df.columns else 'total_mileage_km'
        for _, row in trains_df[trains_df[mileage_col] > 13500].iterrows():
            m = int(row[mileage_col])
            sev = 'CRITICAL' if m > 14250 else 'WARNING'
            all_alerts.append({'Severity': sev, 'Category': 'Mileage Limit' if sev == 'CRITICAL' else 'Mileage Warning',
                'Train_ID': row['Train_ID'], 'Description': f"Train at {m:,} km — {'approaching overhaul limit' if sev == 'WARNING' else 'must go for overhaul'}.",
                'Action': 'Ground for maintenance' if sev == 'CRITICAL' else 'Priority scheduling', 'Timestamp': 'Telemetry'})

        # 4. CAPACITY CHECK — use train status directly, no ML call needed
        active_count = len(trains_df[trains_df['Status'].str.lower() == 'active'])
        if active_count < 30:
            all_alerts.append({'Severity': 'CRITICAL', 'Category': 'Fleet Capacity',
                'Train_ID': 'FLEET-WIDE', 'Description': f"Only {active_count} trains active. Required: 30.",
                'Action': 'Activate emergency fleet protocol', 'Timestamp': 'N/A'})

        schedule_df = pd.DataFrame()  # no longer computed here

        # Synchronize with Database to avoid endless duplicates
        db_alerts_now = get_active_alerts()
        existing_descs = db_alerts_now['description'].tolist() if db_alerts_now is not None and not db_alerts_now.empty else []
        
        for al in all_alerts:
            if al['Description'] not in existing_descs:
                log_alert(al['Train_ID'], al['Severity'], al['Category'], al['Description'])

        # Now pull active state from DB
        db_alerts = get_active_alerts()
        if (db_alerts is None or db_alerts.empty) and all_alerts:
            # Fallback to local memory map when DB unassigned
            db_alerts = pd.DataFrame(all_alerts)
        elif db_alerts is not None and not db_alerts.empty:
            mapping = {'severity': 'Severity', 'category': 'Category', 'train_id': 'Train_ID', 'description': 'Description', 'id': 'Alert_ID'}
            db_alerts = db_alerts.rename(columns=mapping)

        return db_alerts, trains_df
    except Exception as e:
        st.error(f"Scan failed: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Execute Scan
alert_data, trains_df = scan_for_alerts()

if alert_data is None or alert_data.empty:
    st.success("✅ System check complete. No active health alerts found.")
else:
    # --- METRICS BAR ---
    crit_count = len(alert_data[alert_data['Severity'] == 'CRITICAL'])
    warn_count = len(alert_data[alert_data['Severity'] == 'WARNING'])
    info_count = len(alert_data[alert_data['Severity'] == 'INFO'])
    healthy_pct = int(((len(trains_df) - crit_count) / len(trains_df)) * 100)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("🔴 Critical", crit_count)
    mcol2.metric("🟠 Warnings", warn_count)
    mcol3.metric("🟡 Informational", info_count)
    mcol4.metric("✅ Fleet Health Indicator", f"{healthy_pct}%")

    st.divider()

    # --- TABS ---
    t1, t2, t3, t4 = st.tabs(["🔴 Critical", "🟠 Warnings", "🟡 Informational", "📊 All Alerts"])

    with t1:
        st.subheader("Massive Action Required")
        crit_alerts = alert_data[alert_data['Severity'] == 'CRITICAL']
        if crit_alerts is not None and not crit_alerts.empty:
            for cat in crit_alerts['Category'].unique():
                with st.expander(f"❌ {cat}", expanded=True):
                    st.dataframe(crit_alerts[crit_alerts['Category'] == cat], use_container_width=True)
                    if st.button(f"Ground all {cat} trains", key=f"btn_{cat}"):
                        st.info("Broadcast signal sent to ground control...")
        else:
            st.success("No active critical alerts.")

    with t2:
        st.subheader("Operational Warnings")
        warn_alerts = alert_data[alert_data['Severity'] == 'WARNING']
        if warn_alerts is not None and not warn_alerts.empty:
            for cat in warn_alerts['Category'].unique():
                with st.expander(f"⚠️ {cat}"):
                    st.table(warn_alerts[warn_alerts['Category'] == cat])
        else:
            st.success("No active warnings.")

    with t3:
        st.subheader("System Awareness")
        inf_alerts = alert_data[alert_data['Severity'] == 'INFO']
        if inf_alerts is not None and not inf_alerts.empty:
            st.dataframe(inf_alerts, use_container_width=True)
        else:
            st.info("No informational alerts.")

    with t4:
        st.subheader("Master Alert Log")
        
        # Simple Filter
        search = st.text_input("Search by Train ID or Category")
        filtered_log = alert_data.copy()
        if search:
            filtered_log = filtered_log[
                (filtered_log['Train_ID'].str.contains(search, case=False)) | 
                (filtered_log['Category'].str.contains(search, case=False))
            ]
        
        st.dataframe(filtered_log, use_container_width=True)
        
        if 'Alert_ID' in filtered_log.columns and filtered_log is not None and not filtered_log.empty:
            st.divider()
            st.subheader("✓ Acknowledge Alerts")
            ack_id = st.selectbox("Select Alert ID to Mark as Resolved", filtered_log['Alert_ID'].tolist())
            if st.button("Acknowledge Highlighted Alert"):
                from utils.data_loader import acknowledge_alert
                success = acknowledge_alert(ack_id, acknowledged_by="System Admin")
                if success:
                    st.success(f"Alert {ack_id} was successfully acknowledged/resolved.")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.warning("Could not close alert due to a database exception - please retry.")
        
        # Export
        csv = filtered_log.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Current Alerts to CSV", csv, "active_alerts.csv", "text/csv")

# --- TOP ACTIONABLE ALERTS (Dynamic) ---
st.divider()
st.subheader("⚡ Top Active Alerts Requiring Attention")

if alert_data is not None and not alert_data.empty:
    # Show top 3 critical alerts first, then warnings
    top_alerts = pd.DataFrame()
    crit_subset = alert_data[alert_data['Severity'] == 'CRITICAL'].head(3)
    warn_subset = alert_data[alert_data['Severity'] == 'WARNING'].head(3)
    
    if not crit_subset.empty:
        for _, row in crit_subset.iterrows():
            st.error(f"🔴 **[{row.get('Category', 'Alert')}]** {row.get('Train_ID', '')} — {row.get('Description', '')}")
    
    if not warn_subset.empty:
        for _, row in warn_subset.iterrows():
            st.warning(f"🟠 **[{row.get('Category', 'Alert')}]** {row.get('Train_ID', '')} — {row.get('Description', '')}")
    
    if crit_subset.empty and warn_subset.empty:
        st.success("No critical or warning alerts active.")
else:
    st.success("No alerts to display.")
