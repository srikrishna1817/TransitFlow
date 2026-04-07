"""auth/authenticator.py — Login, logout, session helpers."""
import logging
import streamlit as st
from datetime import datetime

logger = logging.getLogger(__name__)


def hash_password(plain: str) -> str:
    import bcrypt
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def check_password(plain: str, hashed: str) -> bool:
    import bcrypt
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except Exception:
        return False


def login(username: str, password: str):
    """Try to log in. Returns user dict on success, None on failure."""
    from auth.user_manager import get_user
    user = get_user(username)
    if user is None:
        return None
    if not user.get('is_active', True):
        return None
    if not check_password(password, user['password_hash']):
        return None
    # Save to session
    st.session_state['user'] = {
        'user_id':   user['user_id'],
        'username':  user['username'],
        'full_name': user['full_name'],
        'email':     user['email'],
        'role':      user['role'],
    }
    # Update last_login in DB
    try:
        from utils.db_utils import db
        db.execute_query(
            "UPDATE users SET last_login=%s WHERE user_id=%s",
            (datetime.now(), user['user_id'])
        )
    except Exception:
        pass
    return st.session_state['user']


def logout():
    """Clear session."""
    st.session_state.pop('user', None)
    # Clear any other cached state keys
    for key in list(st.session_state.keys()):
        if key not in ('_pages',):
            st.session_state.pop(key, None)


def get_current_user():
    """Return logged-in user dict, or None."""
    return st.session_state.get('user', None)
