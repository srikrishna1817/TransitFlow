import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="TransitFlow", page_icon="🔐", layout="wide", initial_sidebar_state="collapsed")

# ── Redirect if already logged in ────────────────────────────────────────────
if st.session_state.get('user'):
    st.switch_page("pages/01_🏠_Home.py")

# ── Styling ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
  html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }

  .stApp {
      background: radial-gradient(circle at center, #1E1B4B 0%, #0F172A 50%, #020617 100%);
  }

  /* Hide chrome */
  [data-testid="collapsedControl"] { display: none; }
  header { visibility: hidden; }
  footer { visibility: hidden; }
  div[data-testid="InputInstructions"] { display: none !important; }

  /* Input fields */
  .stTextInput > div > div > input {
      background-color: rgba(30, 41, 59, 0.5) !important;
      border: 1px solid rgba(255, 255, 255, 0.1) !important;
      color: white !important;
      border-radius: 12px !important;
      padding: 14px 16px !important;
      transition: all 0.3s ease !important;
  }
  .stTextInput > div > div > input:focus {
      border-color: #3B82F6 !important;
      box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3) !important;
      background-color: rgba(30, 41, 59, 0.8) !important;
  }

  /* Button */
  .stButton > button {
      background: linear-gradient(135deg, #3B82F6 0%, #6366F1 100%) !important;
      border: none !important;
      color: white !important;
      border-radius: 12px !important;
      padding: 10px 24px !important;
      font-weight: 600 !important;
      letter-spacing: 0.5px !important;
      font-size: 1.05rem !important;
      box-shadow: 0 10px 25px -5px rgba(59, 130, 246, 0.5) !important;
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
      margin-top: 1rem !important;
  }
  .stButton > button:hover {
      transform: translateY(-3px) scale(1.02) !important;
      box-shadow: 0 15px 35px -5px rgba(59, 130, 246, 0.6) !important;
  }

  /* Logo */
  .hmrl-logo {
      font-size: 3.8rem;
      text-align: center;
      margin-bottom: 0px;
      animation: float 6s ease-in-out infinite;
  }
  @keyframes float {
      0%   { transform: translateY(0px); }
      50%  { transform: translateY(-10px); }
      100% { transform: translateY(0px); }
  }

  .hmrl-title {
      font-size: 2.4rem;
      font-weight: 800;
      text-align: center;
      background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 0.4rem;
      letter-spacing: 1px;
  }

  /* ── Full-screen login transition overlay ──────────────── */
  @keyframes trainCross {
      0%   { left: -12%; }
      100% { left: 105%; }
  }

  @keyframes fadeInOverlay {
      0%   { opacity: 0; }
      20%  { opacity: 1; }
      100% { opacity: 1; }
  }

  @keyframes pulseText {
      0%, 100% { opacity: 0.5; }
      50%      { opacity: 1; }
  }

  @keyframes progressFill {
      0%   { width: 0%; }
      100% { width: 100%; }
  }

  .transit-overlay {
      position: fixed;
      top: 0; left: 0; right: 0; bottom: 0;
      z-index: 99999;
      background: radial-gradient(circle at center, #1E1B4B 0%, #020617 100%);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      animation: fadeInOverlay 0.5s ease-out forwards;
  }

  .transit-overlay-title {
      font-family: 'Outfit', sans-serif;
      font-size: 1.4rem;
      font-weight: 600;
      color: rgba(255,255,255,0.9);
      letter-spacing: 3px;
      text-transform: uppercase;
      margin-bottom: 12px;
      animation: pulseText 1.8s ease-in-out infinite;
  }

  .transit-overlay-greeting {
      font-family: 'Outfit', sans-serif;
      font-size: 0.95rem;
      color: rgba(255,255,255,0.4);
      letter-spacing: 1px;
      margin-bottom: 35px;
  }

  .transit-track-container {
      position: relative;
      width: 65vw;
      max-width: 650px;
      height: 85px;
      border-radius: 14px;
      background: rgba(255,255,255,0.025);
      border: 1px solid rgba(139,92,246,0.2);
      overflow: hidden;
  }

  .transit-track-line {
      position: absolute;
      bottom: 20px; left: 0; right: 0;
      text-align: center;
      font-size: 16px;
      color: rgba(255,255,255,0.08);
      letter-spacing: -1px;
      user-select: none;
  }

  .transit-progress {
      position: absolute;
      bottom: 0; left: 0;
      height: 3px;
      background: linear-gradient(90deg, #7C3AED, #3B82F6, #06B6D4);
      border-radius: 0 0 14px 14px;
      animation: progressFill 4.5s ease-out forwards;
  }

  .transit-train {
      position: absolute;
      top: 8px;
      font-size: 50px;
      animation: trainCross 4.5s cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
  }

  .transit-overlay-sub {
      font-family: 'Outfit', sans-serif;
      font-size: 0.8rem;
      color: rgba(255,255,255,0.25);
      margin-top: 28px;
      letter-spacing: 1.5px;
  }
</style>
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
col_l, col_m, col_r = st.columns([1, 2, 1])
with col_m:
    st.markdown('<div class="hmrl-logo">🚄</div>', unsafe_allow_html=True)
    st.markdown('<div class="hmrl-title">TransitFlow</div>', unsafe_allow_html=True)

    st.divider()

    DEMO_ROLES = {
        "— Select Role —": ("", ""),
        "👑 System Admin (admin)": ("admin", "admin123"),
        "📅 Fleet Scheduler (scheduler)": ("scheduler", "scheduler123"),
        "🔧 Maintenance Ops (maintenance)": ("maintenance", "maint123"),
        "👁️ Read-Only Viewer (viewer)": ("viewer", "viewer123")
    }

    if "login_user" not in st.session_state:
        st.session_state.login_user = ""
    if "login_pass" not in st.session_state:
        st.session_state.login_pass = ""

    def on_role_selected():
        sel = st.session_state.get("quick_role_select")
        if sel and sel in DEMO_ROLES and sel != "— Select Role —":
            u, p = DEMO_ROLES[sel]
            st.session_state.login_user = u
            st.session_state.login_pass = p

    st.selectbox(
        "Quick Fill",
        options=list(DEMO_ROLES.keys()),
        index=0,
        key="quick_role_select",
        on_change=on_role_selected
    )

    username = st.text_input("👤 Operator ID", placeholder="Enter your credentials", key="login_user")
    password = st.text_input("🔑 Security Key", placeholder="Enter your password", type="password", key="login_pass")

    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)
    login_btn = st.button("Authenticate & Enter System", use_container_width=True, type="primary")

    if login_btn:
        if not username or not password:
            st.error("Please enter both Operator ID and Security Key.")
        else:
            with st.spinner("Decrypting credentials..."):
                from auth.authenticator import login
                user = login(username.strip(), password)
            if user:
                import time
                st.success(f"✅ Clearance Granted: Welcome, {user['full_name']}")

                # Full-screen transition overlay — clean, no sparkles, slower
                st.markdown(f"""
                <div class="transit-overlay">
                    <div class="transit-overlay-title">Initializing Command Center</div>
                    <div class="transit-overlay-greeting">Welcome aboard, {user['full_name']}</div>
                    <div class="transit-track-container">
                        <div class="transit-track-line">━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━</div>
                        <div class="transit-train">🚄</div>
                        <div class="transit-progress"></div>
                    </div>
                    <div class="transit-overlay-sub">TransitFlow v1.1 — Secure Session Established</div>
                </div>
                """, unsafe_allow_html=True)
                time.sleep(4.8)

                st.switch_page("pages/01_🏠_Home.py")
            else:
                st.error("❌ Access Denied: Invalid credentials.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.caption("<div style='text-align: center; color: #64748B; font-size: 0.8rem;'>🔒 Authorized Personnel Only — End-to-End Encrypted</div>", unsafe_allow_html=True)

    with st.expander("🧪 Access Test Accounts (Reference)"):
        st.markdown("""
        <div style="font-size: 0.85rem; color: #cbd5e1;">
        <table style="width:100%; border-collapse: collapse; text-align: left;">
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.1);"><th>Role</th><th>ID</th><th>Key</th></tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td>System Admin</td><td><code>admin</code></td><td><code>admin123</code></td></tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td>Fleet Scheduler</td><td><code>scheduler</code></td><td><code>scheduler123</code></td></tr>
            <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);"><td>Maintenance Ops</td><td><code>maintenance</code></td><td><code>maint123</code></td></tr>
            <tr><td>Read-Only Viewer</td><td><code>viewer</code></td><td><code>viewer123</code></td></tr>
        </table>
        </div>
        """, unsafe_allow_html=True)