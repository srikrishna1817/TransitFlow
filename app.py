import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from utils.ui_theme import apply_theme
from utils.keyboard_shortcuts import register_shortcuts

st.set_page_config(
    page_title="TransitFlow",
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
          background: rgba(15, 23, 42, 0.65);
          backdrop-filter: blur(28px);
          -webkit-backdrop-filter: blur(28px);
          border: 1px solid rgba(255, 255, 255, 0.12);
          border-top: 1px solid rgba(255, 255, 255, 0.25);
          border-radius: 28px;
          padding: 4.5rem 3.5rem;
          box-shadow: 0 30px 60px -12px rgba(0, 0, 0, 0.6), 0 0 50px rgba(59, 130, 246, 0.25);
          margin-top: 6vh;
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
      .logo-icon { font-size: 5rem; filter: drop-shadow(0 0 20px rgba(59,130,246,0.7)); animation: float 6s ease-in-out infinite; }
      .welcome-title { font-size: 3.2rem; font-weight: 800; background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 12px 0 6px 0; letter-spacing: 1px; }
      .tagline-text { 
          font-size: 1.4rem; 
          font-weight: 600; 
          background: linear-gradient(90deg, #60A5FA 0%, #A78BFA 100%); 
          -webkit-background-clip: text; 
          -webkit-text-fill-color: transparent; 
          margin: 1.2rem 0 2.8rem 0; 
          letter-spacing: 2px;
          text-transform: uppercase;
      }
      @keyframes float {
          0% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
          100% { transform: translateY(0px); }
      }
    </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        st.markdown("""
        <div class="welcome-container">
            <div class="logo-icon">🚄</div>
            <div class="welcome-title">TransitFlow</div>
            <div class="tagline-text">Predict. Optimize. Operate.</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.button("🔐 Proceed to Secure Login", type="primary", use_container_width=True):
            st.switch_page("pages/00_🔐_Login.py")
            
        st.markdown("<p style='text-align: center; font-size: 0.85em; color: #64748B; margin-top: 2rem; letter-spacing: 0.5px;'>Authorized Personnel Only — End-to-End Encrypted</p>", unsafe_allow_html=True)
        
    st.stop()

user = st.session_state['user']

# ── Sidebar user info ──────────────────────────────────────────────────────────
from auth.permissions import get_role_color, get_role_label
from auth.authenticator import logout

role_color = get_role_color(user['role'])
role_label = get_role_label(user['role'])

st.sidebar.markdown("""
<div class="sidebar-brand">
    <span class="sidebar-brand-icon">🚄</span>
    <span class="sidebar-brand-title">TransitFlow</span>
</div>
<div class="sidebar-brand-divider"></div>
""", unsafe_allow_html=True)

st.sidebar.markdown(f"""
<div style="
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.75), rgba(30, 41, 59, 0.5));
    border-radius: 14px;
    padding: 12px 14px;
    margin-top: 10px;
    margin-bottom: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    border-left: 3px solid {role_color};
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
">
  <div style="font-size: 0.95rem; font-weight: 700; color: #F1F5F9; display: flex; align-items: center; justify-content: space-between;">
    <span>👤 {user['full_name']}</span>
    <span style="background: {role_color}25; border: 1px solid {role_color}70; color: {role_color}; padding: 2px 8px;
                 border-radius: 8px; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.5px;">
      {role_label}
    </span>
  </div>
  <div style="font-size: 0.78rem; color: #94A3B8; margin-top: 3px;">@{user['username']}</div>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Logout", use_container_width=True):
    logout()
    st.switch_page("pages/00_🔐_Login.py")

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
