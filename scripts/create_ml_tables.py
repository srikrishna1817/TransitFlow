"""
Script to create ML-specific database tables (model_deployments).
Run from project root: python scripts/create_ml_tables.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import mysql.connector
from config.db_config import DB_CONFIG


def create_ml_tables():
    print("=" * 55)
    print("  Creating ML Tables in transitflow_db")
    print("=" * 55)

    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # model_deployments
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_deployments (
            deployment_id INT AUTO_INCREMENT PRIMARY KEY,
            model_version VARCHAR(50),
            accuracy DECIMAL(5,4),
            precision_score DECIMAL(5,4),
            recall_score DECIMAL(5,4),
            f1_score DECIMAL(5,4),
            time_mae DECIMAL(6,2),
            severity_mae DECIMAL(6,2),
            cost_mae DECIMAL(10,2),
            deployed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    print("✓ model_deployments table ready")

    # Extend ml_predictions if failure_type / cost cols missing
    try:
        cursor.execute("ALTER TABLE ml_predictions ADD COLUMN IF NOT EXISTS failure_type VARCHAR(50) DEFAULT 'Unknown'")
        cursor.execute("ALTER TABLE ml_predictions ADD COLUMN IF NOT EXISTS time_to_failure_days INT DEFAULT 30")
        cursor.execute("ALTER TABLE ml_predictions ADD COLUMN IF NOT EXISTS severity_score DECIMAL(5,1) DEFAULT 50")
        cursor.execute("ALTER TABLE ml_predictions ADD COLUMN IF NOT EXISTS model_version VARCHAR(50) DEFAULT 'v1'")
        print("✓ ml_predictions table extended with advanced columns")
    except Exception as e:
        print(f"  (ml_predictions extension note: {e})")

    conn.commit()
    cursor.close()
    conn.close()
    print("\n✅ ML tables ready!")

if __name__ == "__main__":
    create_ml_tables()
