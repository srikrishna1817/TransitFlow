import sys
import os
import pandas as pd

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

def verify_migration():
    print("🔍 VERIFYING DATABASE MIGRATION\n" + "="*40)
    
    tables = [
        'trains_master', 'fitness_certificates', 'maintenance_jobs', 
        'historical_operations', 'daily_schedules', 'alerts_log', 'ml_predictions'
    ]
    
    print("\n1. RECORD COUNTS:")
    for table in tables:
        try:
            res = db.execute_query(f"SELECT COUNT(*) as count FROM {table}", fetch=True)
            if res:
                print(f"   {table.ljust(25)}: {res[0]['count']} records")
        except:
            print(f"   {table.ljust(25)}: TABLE NOT FOUND or ERROR")

    print("\n2. SAMPLE QUERY: Trains with health_score < 70")
    try:
        q = """SELECT train_id, manufacturer, health_score, status 
               FROM trains_master 
               WHERE health_score < 70 
               ORDER BY health_score ASC 
               LIMIT 5"""
        df = db.fetch_dataframe(q)
        if df is not None and not df.empty:
            print(df.to_string(index=False))
        else:
            print("   No trains found matching criteria (or table is empty/missing).")
    except Exception as e:
        print(f"   Query failed: {e}")
        
    db.close()
    print("\n✅ Verification complete.")

if __name__ == "__main__":
    verify_migration()
