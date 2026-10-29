"""
auth/page_guard.py
Call require_auth(page_name) at the top of every Streamlit page.
"""
import streamlit as st
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def require_auth(page_name: str):
    """
    Check login + page permission. Stops the page if either fails.
    Returns the user dict on success.
    """
    from auth.authenticator import get_current_user
    from auth.permissions import can_access_page, get_role_label, get_role_color

    user = get_current_user()

    if not user:
        st.warning("🔐 Please login to access this page.")
        if st.button("Go to Login"):
            st.switch_page("pages/00_🔐_Login.py")
        st.stop()

    if not can_access_page(user['role'], page_name):
        st.error(f"⛔ Access Denied — your role ({get_role_label(user['role'])}) "
                 f"does not have permission to view **{page_name}**.")
        st.stop()

    # Render sidebar user widget on every page
    _render_sidebar(user)
    return user


def _render_sidebar(user):
    from auth.permissions import get_role_color, get_role_label
    from auth.authenticator import logout

    role_color = get_role_color(user['role'])
    role_label = get_role_label(user['role'])

    # Brand header with icon & thin divider at top of sidebar
    st.sidebar.markdown("""
    <div class="sidebar-brand">
        <span class="sidebar-brand-icon">🚄</span>
        <span class="sidebar-brand-title">TransitFlow</span>
    </div>
    <div class="sidebar-brand-divider"></div>
    """, unsafe_allow_html=True)

    # User profile & role badge card in sidebar
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

    if st.sidebar.button("🚪 Logout", key=f"logout_{user['username']}", use_container_width=True):
        logout()
        st.switch_page("pages/00_🔐_Login.py")
