import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(page_title="TransitFlow Login", page_icon="🔐", layout="centered", initial_sidebar_state="collapsed")

# ── Redirect if already logged in ────────────────────────────────────────────
if st.session_state.get('user'):
    st.switch_page("pages/01_🏠_Home.py")

# ── Premium Glassmorphism Styling ──────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&display=swap');
  
  html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
  
  .stApp {
      background: radial-gradient(circle at center, #1E1B4B 0%, #0F172A 50%, #020617 100%);
      background-size: cover;
      background-attachment: fixed;
  }
  
  /* Hide the sidebar completely on the login page */
  [data-testid="collapsedControl"] { display: none; }
  header { visibility: hidden; }
  footer { visibility: hidden; }
  
  /* Hide the 'Press Enter to apply' text in text inputs */
  div[data-testid="InputInstructions"] { display: none !important; }

  /* Premium Glassmorphism Container */
  [data-testid="column"]:nth-of-type(2) {
      background: rgba(15, 23, 42, 0.4);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.1);
      border-top: 1px solid rgba(255, 255, 255, 0.2);
      border-radius: 24px;
      padding: 2.5rem 2rem;
      box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 40px rgba(59, 130, 246, 0.2);
      margin-top: 5vh;
      position: relative;
      overflow: hidden;
  }
  
  /* Glowing accent line at top */
  [data-testid="column"]:nth-of-type(2)::before {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; height: 3px;
      background: linear-gradient(90deg, transparent, #3B82F6, #8B5CF6, transparent);
  }

  .hmrl-logo { 
      font-size: 3.5rem; 
      text-align: center; 
      margin-bottom: 0px; 
      filter: drop-shadow(0 0 15px rgba(59,130,246,0.6));
      animation: float 6s ease-in-out infinite;
  }
  
  @keyframes float {
      0% { transform: translateY(0px); }
      50% { transform: translateY(-10px); }
      100% { transform: translateY(0px); }
  }

  .hmrl-title { 
      font-size: 2.2rem; 
      font-weight: 800; 
      text-align: center; 
      background: linear-gradient(135deg, #FFFFFF 0%, #94A3B8 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 5px;
      letter-spacing: 1px;
  }
  
  .hmrl-sub { 
      color: #94A3B8; 
      text-align: center; 
      font-size: 0.95rem; 
      font-weight: 400;
      letter-spacing: 0.5px;
      margin-bottom: 2rem; 
  }

  /* Input Field Overrides */
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

  /* Button Overrides */
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
</style>

<!-- Injecting the container div purely for visual wrapping using Streamlit columns trick -->
""", unsafe_allow_html=True)

# ── Layout ────────────────────────────────────────────────────────────────────
st.markdown("<div style='height: 5vh;'></div>", unsafe_allow_html=True)

col_l, col_m, col_r = st.columns([1.5, 1.2, 1.5])
with col_m:
    # We target the column directly with CSS
    
    st.markdown('<div class="hmrl-logo">🚄</div>', unsafe_allow_html=True)
    st.markdown('<div class="hmrl-title">TransitFlow</div>', unsafe_allow_html=True)
    st.markdown('<div class="hmrl-sub">Hyderabad Metro Rail Command Center</div>', unsafe_allow_html=True)
    
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

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
                with st.spinner("Establishing secure handshake with HMRL Core..."):
                    time.sleep(1)
                st.switch_page("pages/01_🏠_Home.py")
            else:
                st.error("❌ Access Denied: Invalid credentials.")

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    st.caption("<div style='text-align: center; color: #64748B; font-size: 0.8rem;'>🔒 Authorized Personnel Only — End-to-End Encrypted</div>", unsafe_allow_html=True)

    # Demo credentials hint inside a sleek expander
    with st.expander("🧪 Access Test Accounts"):
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


