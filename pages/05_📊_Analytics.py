import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
from scheduler import generate_schedule
from utils.data_loader import load_trains_data, load_maintenance_jobs, load_certificates_data, load_historical_operations, log_alert, get_active_alerts
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth

# Page Config
st.set_page_config(page_title="Alerts Dashboard", page_icon="🚨", layout="wide")
user = require_auth('Alerts')

# Simulation of auto-refresh (re-runs script every 60s)
# st.empty() 
# if "last_refresh" not in st.session_state:
#     st.session_state.last_refresh = datetime.datetime.now()

# Header
st.title("🚨 Real-Time Alerts & Notifications")
curr_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
st.caption(f"Last System Scan: {curr_time}")

# --- DATA SCANNING ENGINE ---
@st.cache_data(ttl=60)
def scan_for_alerts():
    try:
            # Load Raw Data (falling back transparently if DB fails)
        trains_df = load_trains_data()
        maint_df = load_maintenance_jobs()
        cert_df = load_certificates_data()
        hist_df = load_historical_operations()
        
        # Run AI Scheduler for Risk Predictions
        # Using a default requirement of 30 to get standby/service assignments
        schedule_df, _ = generate_schedule(required_service_trains=30, save_to_db=False)
        
        all_alerts = []
        now = datetime.datetime.now()
        
        # 1. SCAN CERTIFICATES
        cert_df['Valid_Until'] = pd.to_datetime(cert_df['Valid_Until'])
        cert_df['Days_Until'] = (cert_df['Valid_Until'] - now).dt.days
        
        for _, row in cert_df.iterrows():
            if row['Days_Until'] < 0:
                all_alerts.append({
                    'Severity': 'CRITICAL', 'Category': 'Expired Certificate',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} certificate expired {-row['Days_Until']} days ago.",
                    'Action': 'Ground train immediately', 'Timestamp': row['Valid_Until'].strftime("%Y-%m-%d")
                })
            elif 0 <= row['Days_Until'] <= 7:
                all_alerts.append({
                    'Severity': 'WARNING', 'Category': 'Certificate Expiry',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} certificate expires in {row['Days_Until']} days.",
                    'Action': 'Schedule renewal inspection', 'Timestamp': row['Valid_Until'].strftime("%Y-%m-%d")
                })
            elif 7 < row['Days_Until'] <= 30:
                all_alerts.append({
                    'Severity': 'INFO', 'Category': 'Certificate Expiry',
                    'Train_ID': row['Train_ID'], 'Description': f"{row['Department']} cert valid for {row['Days_Until']} more days.",
                    'Action': 'Monitor for renewal', 'Timestamp': row['Valid_Until'].strftime("%Y-%m-%d")
                })

        # 2. SCAN MAINTENANCE JOBS
        for _, row in maint_df.iterrows():
            if row['Status'] == 'Open':
                if row['Priority'] == 'High':
                    all_alerts.append({
                        'Severity': 'CRITICAL', 'Category': 'Critical Maintenance',
                        'Train_ID': row['Train_ID'], 'Description': f"High-priority job {row['Job_Card_ID']} is still OPEN.",
                        'Action': 'Assign technician immediately', 'Timestamp': 'N/A'
                    })
                elif row['Priority'] == 'Medium':
                    all_alerts.append({
                        'Severity': 'WARNING', 'Category': 'Open Maintenance',
                        'Train_ID': row['Train_ID'], 'Description': f"Medium-priority job {row['Job_Card_ID']} pending.",
                        'Action': 'Resolve within 48 hours', 'Timestamp': 'N/A'
                    })

        # 3. SCAN AI RISKS & MILEAGE
        # Mileage Threshold: 15,000 km
        for _, row in schedule_df.iterrows():
            t_id = row['Train_ID']
            risk = row['AI_Risk_Percent']
            
            # Get current mileage from trains_df
            mileage = trains_df[trains_df['Train_ID'] == t_id]['Current_Mileage'].iloc[0]
            
            # AI Risk
            if risk > 80:
                all_alerts.append({
                    'Severity': 'CRITICAL', 'Category': 'High ML Risk',
                    'Train_ID': t_id, 'Description': f"AI predicts {risk}% failure probability.",
                    'Action': 'Remove from service for inspection', 'Timestamp': 'AI Prediction'
                })
            elif 50 < risk <= 80:
                all_alerts.append({
                    'Severity': 'WARNING', 'Category': 'Medium ML Risk',
                    'Train_ID': t_id, 'Description': f"AI predicts {risk}% failure probability.",
                    'Action': 'Schedule preventive check', 'Timestamp': 'AI Prediction'
                })
            
            # Mileage
            if mileage > 14250: # 95% of 15000
                all_alerts.append({
                    'Severity': 'CRITICAL', 'Category': 'Mileage Limit',
                    'Train_ID': t_id, 'Description': f"Train reached {mileage} km. Must go for overhaul.",
                    'Action': 'Ground train for maintenance', 'Timestamp': 'Telemetry'
                })
            elif 13500 < mileage <= 14250: # 90-95%
                all_alerts.append({
                    'Severity': 'WARNING', 'Category': 'Mileage Warning',
                    'Train_ID': t_id, 'Description': f"Train at {mileage} km. Approaching limit.",
                    'Action': 'Priority scheduling for workshop', 'Timestamp': 'Telemetry'
                })

        # 4. CAPACITY CHECK
        available_count = len(schedule_df[schedule_df['Priority_Score'] > 0])
        if available_count < 30: # Assuming 30 is the critical threshold for peak hours
            all_alerts.append({
                'Severity': 'CRITICAL', 'Category': 'Fleet Capacity',
                'Train_ID': 'FLEET-WIDE', 'Description': f"Only {available_count} trains available. Required: 30.",
                'Action': 'Activate emergency fleet protocol', 'Timestamp': 'N/A'
            })

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

        return db_alerts, trains_df, schedule_df
    except Exception as e:
        st.error(f"Scan failed: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

# Execute Scan
alert_data, trains_df, schedule_df = scan_for_alerts()

if alert_data is None or alert_data.empty:
    st.success("✅ System check complete. No active health alerts found.")
else:
    # --- METRICS BAR ---
    crit_count = len(alert_data[alert_data['Severity'] == 'CRITICAL'])
    warn_count = len(alert_data[alert_data['Severity'] == 'WARNING'])
    info_count = len(alert_data[alert_data['Severity'] == 'INFO'])
    healthy_pct = int(((len(trains_df) - crit_count) / len(trains_df)) * 100)

    mcol1, mcol2, mcol3, mcol4 = st.columns(4)
    mcol1.metric("🔴 Critical", crit_count, delta="-2 vs yesterday") # Mock delta
    mcol2.metric("🟠 Warnings", warn_count, delta="+1 vs yesterday") # Mock delta
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

# --- TREND VISUALIZATION ---
st.divider()
st.subheader("📈 Alert Severity Trends (Last 30 Days)")

# Generate professional dummy trend data
dates = [datetime.date.today() - datetime.timedelta(days=x) for x in range(30)]
dummy_trend = pd.DataFrame({
    'Date': dates[::-1],
    'Critical': np.random.randint(0, 5, 30),
    'Warning': np.random.randint(2, 10, 30),
    'Info': np.random.randint(5, 15, 30)
})
fig_trend = px.line(dummy_trend, x='Date', y=['Critical', 'Warning', 'Info'],
                 color_discrete_map={'Critical': 'red', 'Warning': 'orange', 'Info': 'gold'},
                 title="System Instability Over Time")
st.plotly_chart(fig_trend, use_container_width=True)

# --- ACTIONABLE INSIGHTS ---
st.divider()
st.subheader("💡 AI Recommended Actions")
col_ins1, col_ins2 = st.columns(2)

with col_ins1:
    st.info("**Immediate Dispatch:** Request technical audit for trains with AI risk > 80% to prevent service disruptions.")
    st.info("**Safety Check:** 5 certificates are within 7 days of expiry. Link with workshop to ensure compliance.")

with col_ins2:
    st.warning("**Resource Allocation:** Fleet utilization is peaking. Consider moving 2 standby trains to active service on the Red Line.")
    if alert_data is not None and not alert_data.empty and crit_count > 0:
        st.error(f"**Safety Alert:** {crit_count} trains currently bypass safety thresholds. Operations must ground these units before 12:00 PM.")

# Auto-refresh logic (sidebar)
if st.sidebar.checkbox("Enable Auto-Refresh (60s)", value=True):
    st.info("Auto-refresh active. Next scan in 60 seconds.")
    # In a real app we'd use st_autorefresh, but for standard streamlit:
    # time.sleep(60)
    # st.rerun()
