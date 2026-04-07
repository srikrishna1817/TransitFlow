import json
from utils.db_utils import db

def load_user_preferences(user_id):
    """Loads a dictionary of saved user preferences from the database"""
    default_prefs = {
        "theme": "light",
        "dashboard_layout": "standard",
        "notifications_enabled": True,
        "default_horizon_days": 30
    }
    try:
        res = db.fetch_dataframe(f"SELECT preferences FROM user_preferences WHERE user_id={user_id}")
        if res is not None and not res.empty:
            saved = json.loads(res.iloc[0]['preferences'])
            default_prefs.update(saved)
            return default_prefs
    except Exception:
        pass
    return default_prefs

def save_user_preferences(user_id, prefs_dict):
    """Serializes and upserts the preference dict to JSON inside MySQL"""
    try:
        pref_str = json.dumps(prefs_dict)
        q = "INSERT INTO user_preferences (user_id, preferences) VALUES (%s, %s) ON DUPLICATE KEY UPDATE preferences=%s"
        db.execute_query(q, (user_id, pref_str, pref_str))
        return True
    except Exception as e:
        print(f"Failed to save preferences: {e}")
        return False
