import streamlit as st
import os
import time
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from auth.page_guard import require_auth

st.set_page_config(page_title="Settings", page_icon="⚙️", layout="wide")
user = require_auth('Settings')
st.title("⚙️ System Configuration")

st.header("Operational Parameters")
col1, col2 = st.columns(2)
with col1:
    default_req = st.number_input("Default Daily Train Requirement", min_value=10, max_value=60, value=45)
    maint_threshold = st.number_input("Maintenance Mileage Threshold (km)", min_value=5000, max_value=30000, value=15000, step=1000)
with col2:
    cert_validity = st.selectbox("Default Certificate Validity (Months)", [3, 6, 12])
    
if st.button("💾 Save Parameters"):
    st.success("Parameters saved successfully! (Note: changes are temporary for this session)")

st.divider()

st.header("Administrative Actions")
try:
    model_time = os.path.getmtime("models/maintenance_predictor_advanced.pkl")
    last_updated_time = time.ctime(model_time)
except:
    last_updated_time = "Unknown"

st.caption(f"**ML Model Last Updated:** {last_updated_time}")

if st.button("🔄 Retrain ML Model"):
    with st.spinner("Retraining model using current historical data..."):
        try:
            from train_model import train_model
            acc = train_model()
            st.success(f"Model retrained successfully! New Test Accuracy: {acc*100:.2f}%")
        except Exception as e:
            st.error(f"Error retraining model: {e}")

st.markdown("---")

st.caption("**Data Management**")
if st.button("♻️ Refresh Synthetic Databases"):
    with st.spinner("Regenerating all synthetic CSV data files..."):
        try:
            import subprocess
            subprocess.run(["python", "generate_data.py"], check=True)
            st.cache_data.clear()
            st.success("Synthetic data refreshed successfully!")
        except Exception as e:
            st.error(f"Failed to generate data: {e}")

st.divider()

st.header("System Information")
st.json({
    "System Version": "1.1.0 (Multi-Page)",
    "Environment": "Production",
    "Model Engine": "RandomForestClassifier",
    "Max Fleet Capacity": 60,
    "Status": "Healthy"
})
