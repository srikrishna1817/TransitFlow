import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.ui_theme import apply_theme
from utils.keyboard_shortcuts import register_shortcuts

st.set_page_config(
    page_title="TransitFlow — HMRL",
    page_icon="🚆",
    layout="wide",
)

try:
    apply_theme()
    register_shortcuts()
except:
    pass

# ── Auth guard ────────────────────────────────────────────────────────────────
if 'user' not in st.session_state:
    st.switch_page("pages/00_🔐_Login.py")

user = st.session_state['user']

# ── Sidebar user info ──────────────────────────────────────────────────────────
from auth.permissions import get_role_color, get_role_label

role_color = get_role_color(user['role'])
role_label = get_role_label(user['role'])

st.sidebar.markdown(f"""
<div style="
    background: linear-gradient(135deg, #0d1b2a, #1b2d3e);
    border-radius: 12px;
    padding: 14px 16px;
    margin-bottom: 12px;
    border-left: 4px solid {role_color};
">
  <div style="font-size:1.2rem; font-weight:700; color:#e8f4fd;">
    👤 {user['full_name']}
  </div>
  <div style="font-size:0.82rem; color:#94a3b8; margin-top:2px;">@{user['username']}</div>
  <div style="margin-top:8px;">
    <span style="background:{role_color};color:white;padding:2px 10px;
                 border-radius:10px;font-size:0.78rem;font-weight:600;">
      {role_label}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    from auth.authenticator import logout
    logout()
    st.switch_page("pages/00_🔐_Login.py")

st.sidebar.divider()

# ── Main content ──────────────────────────────────────────────────────────────
st.title("🚆 TransitFlow — HMRL")
st.subheader("AI-Driven Train Induction Planning & Scheduling System")
st.divider()

st.markdown(f"""
### Welcome, {user['full_name']}! 👋

TransitFlow is an AI-powered system for Hyderabad Metro Rail operations.

**Navigation Guide:**
- 🏠 **Home:** Fleet KPI overview
- 📅 **Schedule:** Daily scheduling & Gantt charts
- 🔧 **Maintenance:** Job cards & train health
- 📊 **Analytics:** Deep-dive fleet analytics
- 🚨 **Alerts:** Real-time operational alerts
- ⚙️ **Settings:** System configuration *(Admin only)*
- 🤖 **ML Insights:** AI predictions & SHAP explanations
- 📈 **Predictive Analytics:** Forecasting, trends & optimization
- 📄 **Reports:** Automated multi-tab PDF generation & history

**System Status:** 🟢 All Systems Operational
""")

st.info("👈 Use the sidebar to navigate.")