"""auth/user_manager.py — CRUD for the users table."""
import logging
import pandas as pd
logger = logging.getLogger(__name__)


def _db():
    from utils.db_utils import db
    return db


def get_user(username: str):
    try:
        rows = _db().execute_query(
            "SELECT * FROM users WHERE username=%s AND is_active=1", (username,), fetch=True
        )
        return dict(rows[0]) if rows else None
    except Exception as e:
        logger.error(f"get_user error: {e}")
        return None


def get_user_by_id(user_id: int):
    try:
        rows = _db().execute_query(
            "SELECT * FROM users WHERE user_id=%s", (user_id,), fetch=True
        )
        return dict(rows[0]) if rows else None
    except Exception as e:
        logger.error(f"get_user_by_id error: {e}")
        return None


def create_user(username, password, full_name, email, role):
    from auth.authenticator import hash_password
    pw_hash = hash_password(password)
    try:
        result = _db().execute_query(
            """INSERT INTO users (username, password_hash, full_name, email, role)
               VALUES (%s, %s, %s, %s, %s)""",
            (username, pw_hash, full_name, email, role)
        )
        return result is not False and result is not None
    except Exception as e:
        logger.error(f"create_user error: {e}")
        return False


def list_users():
    try:
        rows = _db().execute_query(
            "SELECT user_id,username,full_name,email,role,is_active,created_at,last_login FROM users",
            fetch=True
        )
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        logger.error(f"list_users error: {e}")
        return pd.DataFrame()


def update_user(user_id, fields: dict):
    if not fields:
        return False
    cols = ', '.join(f"{k}=%s" for k in fields)
    vals = list(fields.values()) + [user_id]
    try:
        return _db().execute_query(f"UPDATE users SET {cols} WHERE user_id=%s", vals)
    except Exception as e:
        logger.error(f"update_user error: {e}")
        return False


def delete_user(user_id):
    try:
        return _db().execute_query("UPDATE users SET is_active=0 WHERE user_id=%s", (user_id,))
    except Exception as e:
        logger.error(f"delete_user error: {e}")
        return False


def log_activity(user_id, action, page):
    try:
        _db().execute_query(
            "INSERT INTO user_activity_log (user_id, action, page) VALUES (%s,%s,%s)",
            (user_id, action, page)
        )
    except Exception:
        pass
