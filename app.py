import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.ui_theme import apply_theme
from utils.keyboard_shortcuts import register_shortcuts

st.set_page_config(
    page_title="TransitFlow — HMRL",
    page_icon="🚆",
    layout="wide",
    initial_sidebar_state="collapsed"
)

try:
    apply_theme()
    register_shortcuts()
except:
    pass

# ── Auth guard ────────────────────────────────────────────────────────────────
# Check if user is logged in via session state
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated or 'user' not in st.session_state:
    st.markdown("""
    <style>
      .welcome-container {
          background: rgba(30, 41, 59, 0.4);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border: 1px solid rgba(255, 255, 255, 0.1);
          border-top: 1px solid rgba(255, 255, 255, 0.2);
          border-radius: 24px;
          padding: 4rem 3rem;
          box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(59, 130, 246, 0.2);
          margin-top: 10vh;
          text-align: center;
          position: relative;
          overflow: hidden;
      }
      .welcome-container::before {
          content: '';
          position: absolute;
          top: 0; left: 0; right: 0; height: 3px;
          background: linear-gradient(90deg, transparent, #3B82F6, #8B5CF6, transparent);
      }
      .logo-icon { font-size: 4rem; filter: drop-shadow(0 0 15px rgba(59,130,246,0.6)); animation: float 6s ease-in-out infinite; }
      .welcome-title { font-size: 2.5rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 10px 0; }
      .welcome-sub { color: #94A3B8; font-size: 1.1rem; margin-bottom: 2rem; }
      @keyframes float {
          0% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
          100% { transform: translateY(0px); }
      }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown("""
        <div class="welcome-container">
            <div class="logo-icon">🚄</div>
            <div class="welcome-title">TransitFlow</div>
            <div class="welcome-sub">AI-Powered Fleet Intelligence & Scheduling System</div>
            <div style="background: rgba(59, 130, 246, 0.1); border-left: 4px solid #3B82F6; padding: 15px; border-radius: 8px; text-align: left; margin-bottom: 2rem; color: #E2E8F0;">
                👋 <b>Hello!</b> You are currently viewing the guest portal. Please log in to securely access the full operational dashboard, fleet metrics, and advanced scheduling AI.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🔐 Proceed to Secure Login", type="primary", use_container_width=True):
            st.switch_page("pages/00_🔐_Login.py")
            
        st.markdown("<p style='text-align: center; font-size: 0.8em; color: #64748B; margin-top: 2rem;'>TransitFlow v1.1 | Authorized Personnel Only</p>", unsafe_allow_html=True)
        
    st.stop()

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
