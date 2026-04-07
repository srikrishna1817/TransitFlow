import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db
from utils.data_loader import load_trains_data

def run_tests():
    print("🧪 RUNNING DATABASE TESTS...")
    
    # 1. Test Connection
    conn = db.connect()
    if conn:
        print("✅ Connection Test: SUCCESS")
    else:
        print("❌ Connection Test: FAILED")
        
    # 2. Test DataLoader
    try:
        df = load_trains_data()
        if not df.empty:
            print(f"✅ Data Loader Test: SUCCESS ({len(df)} records fetched)")
        else:
            print("❌ Data Loader Test: FAILED (Empty DataFrame)")
    except Exception as e:
        print(f"❌ Data Loader Test: FAILED ({e})")
        
    print("\nTests finished.")

if __name__ == "__main__":
    run_tests()
