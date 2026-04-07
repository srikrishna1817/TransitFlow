"""Create users and user_activity_log tables."""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mysql.connector
from config.db_config import DB_CONFIG

conn = mysql.connector.connect(**DB_CONFIG)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id       INT AUTO_INCREMENT PRIMARY KEY,
    username      VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name     VARCHAR(100),
    email         VARCHAR(100),
    role          VARCHAR(20) NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login    TIMESTAMP NULL
);
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS user_activity_log (
    log_id    INT AUTO_INCREMENT PRIMARY KEY,
    user_id   INT,
    action    VARCHAR(100),
    page      VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);
""")

try:
    cur.execute("CREATE INDEX idx_username ON users(username);")
except Exception:
    pass  # Index already exists
conn.commit()
cur.close()
conn.close()
print("Auth tables created successfully.")
