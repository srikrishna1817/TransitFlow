import streamlit as st
import os
import sys
import time
import platform
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth

from utils.ui_theme import apply_theme

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide", initial_sidebar_state="collapsed")
apply_theme()
user = require_auth('Settings')
st.title("⚙️ System Configuration")
st.caption("Administrative controls, operational parameters, and system health information.")
st.divider()

# ── System Info Card (always visible, read-only) ────────────────────────────
st.subheader("🖥️ System Information")
col_sys1, col_sys2, col_sys3 = st.columns(3)

# Python version
py_ver = platform.python_version()
col_sys1.metric("🐍 Python Version", py_ver)

# DB connection status
db_status = "Unknown"
try:
    from utils.db_utils import db
    test = db.fetch_dataframe("SELECT 1 AS ping")
    db_status = "Connected ✅" if test is not None else "Disconnected ❌"
except Exception:
    db_status = "Disconnected ❌"
col_sys2.metric("🗄️ DB Connection", db_status)

# Last model training date
try:
    model_time = os.path.getmtime("models/maintenance_predictor_advanced.pkl")
    last_model_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(model_time))
except Exception:
    last_model_str = "Not found"
col_sys3.metric("🤖 Last Model Trained", last_model_str)

st.divider()

admin_pin = st.text_input("Enter Admin PIN to unlock settings:", type="password")

if admin_pin == "1234":
    st.success("✅ Settings Unlocked")
    
    st.header("Operational Parameters")
    col1, col2 = st.columns(2)
    with col1:
        default_req = st.number_input("Default Daily Train Requirement", min_value=10, max_value=60, value=45)
        maint_threshold = st.number_input("Maintenance Mileage Threshold (km)", min_value=5000, max_value=30000, value=15000, step=1000)
    with col2:
        cert_validity = st.selectbox("Default Certificate Validity (Months)", [3, 6, 12])
        
    st.info("ℹ️ These parameters apply to the current session only and are not persisted across sessions.")

    st.divider()

    st.header("Administrative Actions")

    if st.button("🔄 Retrain ML Model"):
        with st.spinner("🤖 Computing ML predictions — retraining model using current historical data..."):
            try:
                from train_model import train_model
                acc = train_model()
                st.success(f"✅ Model retrained successfully! New Test Accuracy: {acc*100:.2f}%")
            except Exception as e:
                st.error(f"❌ Error retraining model: {e}")

    st.markdown("---")

    st.caption("**Data Management**")
    if st.button("♻️ Refresh Synthetic Databases"):
        with st.spinner("🔄 Regenerating all synthetic CSV data files..."):
            try:
                import subprocess
                subprocess.run(["python", "generate_data.py"], check=True)
                st.cache_data.clear()
                st.success("✅ Synthetic data refreshed successfully!")
            except Exception as e:
                st.error(f"❌ Failed to generate data: {e}")

else:
    if admin_pin:
        st.error("❌ Incorrect PIN. Access Denied.")
    else:
        st.info("ℹ️ Please enter the admin PIN to view and change system configurations.")

from components.custom_widgets import render_page_nav
render_page_nav('pages/09_📄_Reports.py', '📄 Reports', None, None)
