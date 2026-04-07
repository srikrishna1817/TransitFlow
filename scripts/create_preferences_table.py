import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

def build_tables():
    print("Building UX Tables...")
    try:
        db.execute_query("""
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INT PRIMARY KEY,
            preferences JSON,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );
        """)
        print("✅ User Preferences table initialized successfully.")
    except Exception as e:
        print(f"❌ Failed to build preference table: {e}")

if __name__ == "__main__":
    build_tables()
