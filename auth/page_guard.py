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

    st.sidebar.markdown(f"""
<div style="
    background:linear-gradient(135deg, rgba(13,27,42,0.8), rgba(27,45,62,0.8));
    border-radius:12px;
    padding:12px 14px;
    margin-bottom:10px;
    border: 1px solid rgba(255,255,255,0.1);
    border-top: 3px solid {role_color};
">
  <div style="font-size:1.1rem;font-weight:700;color:#e8f4fd; display: flex; align-items: center; gap: 8px;">
    👤 <span>{user['full_name']}</span>
  </div>
  <div style="font-size:0.8rem;color:#94a3b8; margin-top: 2px;">@{user['username']}</div>
  <div style="margin-top:8px;">
    <span style="background: {role_color}20; border: 1px solid {role_color}60; color: {role_color}; padding:3px 10px;
                 border-radius:12px;font-size:0.75rem;font-weight:700;letter-spacing:0.5px;">
      {role_label}
    </span>
  </div>
</div>
""", unsafe_allow_html=True)

    if st.sidebar.button("🚪 Logout", key=f"logout_{user['username']}", use_container_width=True):
        logout()
        st.switch_page("pages/00_🔐_Login.py")

    st.sidebar.divider()
