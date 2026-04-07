import mysql.connector
from config.db_config import DB_CONFIG

def create_report_tables():
    conn = mysql.connector.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS report_history (
        report_id INT AUTO_INCREMENT PRIMARY KEY,
        report_type VARCHAR(100),
        report_date DATE,
        generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        generated_by INT,
        file_path VARCHAR(255),
        file_size_kb INT,
        FOREIGN KEY (generated_by) REFERENCES users(user_id) ON DELETE SET NULL
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scheduled_reports (
        schedule_id INT AUTO_INCREMENT PRIMARY KEY,
        report_type VARCHAR(100),
        frequency VARCHAR(20),
        is_enabled BOOLEAN DEFAULT TRUE,
        last_generated TIMESTAMP NULL,
        next_scheduled TIMESTAMP NULL
    );
    """)

    conn.commit()
    print("Report tables created successfully.")
    cur.close()
    conn.close()

if __name__ == "__main__":
    create_report_tables()
