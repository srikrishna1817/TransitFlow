import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

def repair_database():
    print("========== TRANSITFLOW DB REPAIR & OPTIMIZATION ==========\n")
    try:
        # Check all tables
        tables = db.fetch_dataframe("SHOW TABLES")
        success_count = 0
        
        if tables is not None and not tables.empty:
            for tbl in tables.iloc[:, 0]:
                print(f"⏳ Optimizing layout on table `{tbl}`...")
                try:
                    db.execute_query(f"OPTIMIZE TABLE {tbl}")
                    db.execute_query(f"ANALYZE TABLE {tbl}")
                    success_count += 1
                except Exception as ex:
                    print(f"  ❌ Cannot optimize `{tbl}`: {ex}")
        
        print(f"\n✅ Successfully rebuilt memory pages and compiled sequence statistics for {success_count} normalized tables.")
    except Exception as e:
        print(f"Database repair script severely failed: {e}")

if __name__ == "__main__":
    repair_database()
