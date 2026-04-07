import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="TransitFlow Login", page_icon="🔐", layout="centered")

# ── Redirect if already logged in ────────────────────────────────────────────
if st.session_state.get('user'):
    st.switch_page("pages/01_🏠_Home.py")

# ── Page styling ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .login-card {
    background: linear-gradient(135deg, #0d1b2a 0%, #1b2d3e 100%);
    border-radius: 18px;
    padding: 2.5rem 2rem;
    box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    border: 1px solid rgba(255,255,255,0.07);
  }
  .hmrl-logo { font-size: 2.8rem; text-align: center; margin-bottom: 0.2rem; }
  .hmrl-title { font-size: 1.6rem; font-weight: 700; color: #e8f4fd; text-align: center; }
  .hmrl-sub { color: #7fb3d3; text-align: center; font-size: 0.9rem; margin-bottom: 1.5rem; }
  section[data-testid="stVerticalBlock"] > div { gap: 0.5rem; }
</style>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
col_l, col_m, col_r = st.columns([1, 2.5, 1])
with col_m:
    st.markdown('<div class="hmrl-logo">🚇</div>', unsafe_allow_html=True)
    st.markdown('<div class="hmrl-title">TransitFlow</div>', unsafe_allow_html=True)
    st.markdown('<div class="hmrl-sub">Hyderabad Metro Rail — AI Scheduling System</div>', unsafe_allow_html=True)
    st.divider()

    username = st.text_input("👤 Username", placeholder="Enter your username", key="login_user")
    password = st.text_input("🔑 Password", placeholder="Enter your password",
                              type="password", key="login_pass")

    st.markdown("<br>", unsafe_allow_html=True)
    login_btn = st.button("🚀 Login to TransitFlow", use_container_width=True, type="primary")

    if login_btn:
        if not username or not password:
            st.error("Please enter both username and password.")
        else:
            with st.spinner("Verifying credentials…"):
                from auth.authenticator import login
                user = login(username.strip(), password)
            if user:
                import time
                st.success(f"✅ Authentication Verified: Welcome, {user['full_name']}!")
                with st.spinner("Establishing secure connection to HMRL Core Servers..."):
                    time.sleep(1)
                st.switch_page("pages/01_🏠_Home.py")
            else:
                st.error("❌ Incorrect username or password. Please try again.")

    st.divider()
    st.caption("🔒 Secure access — HMRL internal system only")

    # Demo credentials hint
    with st.expander("🧪 Demo Credentials"):
        st.markdown("""
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `admin123` |
| Scheduler | `scheduler` | `scheduler123` |
| Maintenance | `maintenance` | `maint123` |
| Viewer | `viewer` | `viewer123` |
        """)
