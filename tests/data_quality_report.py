import sys
import os
import pandas as pd
from datetime import datetime
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_utils import db

def run_quality_checks():
    print("========== TRANSITFLOW DATA QUALITY REPORT ==========\n")
    report_lines = []
    
    # 1. Null Checks in trains_master
    tm_df = db.fetch_dataframe("SELECT * FROM trains_master")
    if tm_df is not None and not tm_df.empty:
        null_health = tm_df['health_score'].isnull().sum()
        if null_health > 0:
            report_lines.append(f"[CRITICAL] Found {null_health} trains with NULL health scores.")
        else:
            report_lines.append("[INFO] All trains have valid health scores.")
            
        mileage_outliers = tm_df[tm_df['kilometers_run'] > 2000000]
        if not mileage_outliers.empty:
            report_lines.append(f"[WARNING] {len(mileage_outliers)} trains have unrealistic mileage (> 2,000,000 km).")
    else:
        report_lines.append("[WARNING] trains_master table is empty.")

    # 2. Maintenance Jobs Validation
    mj_df = db.fetch_dataframe("SELECT * FROM maintenance_jobs")
    if mj_df is not None and not mj_df.empty:
        invalid_dates = mj_df[(mj_df['actual_completion_date'].notna()) & (mj_df['reported_date'] > mj_df['actual_completion_date'])]
        if not invalid_dates.empty:
            report_lines.append(f"[CRITICAL] {len(invalid_dates)} jobs found with actual_completion_date occurring before reported_date.")
        
        missing_trains = mj_df[~mj_df['train_id'].isin(tm_df['train_id'] if tm_df is not None else [])]
        if not missing_trains.empty:
            report_lines.append(f"[CRITICAL] {len(missing_trains)} orphaned maintenance jobs reference missing Train IDs.")
    else:
        report_lines.append("[INFO] maintenance_jobs table check skipped (empty).")

    # 3. Duplicate Schedule Checks
    sc_df = db.fetch_dataframe("SELECT train_id, date, count(*) as c FROM schedule_master GROUP BY train_id, date HAVING c > 1")
    if sc_df is not None and not sc_df.empty:
        report_lines.append(f"[WARNING] {len(sc_df)} instances of trains doubly scheduled on the same date.")
    else:
        report_lines.append("[INFO] No duplicate schedule assignments found.")

    for line in report_lines:
        print(line)

    print("\nData Quality Scan Complete.")

if __name__ == "__main__":
    run_quality_checks()
