import sys
import os
import pandas as pd
import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

def log_fix(message):
    with open("fixes_applied.log", "a") as f:
        f.write(f"[{datetime.datetime.now().isoformat()}] {message}\n")
    print(f"ℹ️ {message}")

def fix_common_bugs():
    print("========== TRANSITFLOW BUG FIXING ENGINE ==========\n")
    confirm = input("⚠️ Are you sure you want to apply automated common fixes directly to the LIVE database? (y/n): ")
    if confirm.lower() != 'y':
        print("Aborting.")
        return

    # Fix 1: Negative metrics
    try:
        db.execute_query("UPDATE trains_master SET total_mileage_km = 0 WHERE total_mileage_km < 0")
        db.execute_query("UPDATE trains_master SET total_running_hours = 0 WHERE total_running_hours < 0")
        log_fix("Fixed any negative mileage and running hours by resetting them strictly to 0.")
    except Exception as e:
        print(f"Failed Fix 1: {e}")

    # Fix 2: Orphaned maintenance records
    try:
        orphans = db.fetch_dataframe("SELECT job_id FROM maintenance_jobs WHERE train_id NOT IN (SELECT train_id FROM trains_master)")
        if orphans is not None and not orphans.empty:
            count = 0
            for job in orphans['job_id']:
                db.execute_query("DELETE FROM maintenance_jobs WHERE job_id = %s", (job,))
                count += 1
            log_fix(f"Removed {count} orphaned maintenance jobs belonging to deleted trains.")
        else:
            log_fix("No orphaned records detected in maintenance_jobs.")
    except Exception as e:
        print(f"Failed Fix 2: {e}")
        
    # Fix 3: Format standardisation 
    try:
        db.execute_query("UPDATE users SET email = LOWER(TRIM(email)) WHERE email IS NOT NULL")
        db.execute_query("UPDATE users SET username = TRIM(username) WHERE username IS NOT NULL")
        log_fix("Standardized whitespace and letter-casing across username and email string columns.")
    except Exception as e:
        print(f"Failed Fix 3: {e}")

    # Fix 4: Date sanity repairs
    try:
        db.execute_query("UPDATE maintenance_jobs SET actual_completion_date = reported_date + INTERVAL 1 DAY WHERE actual_completion_date IS NOT NULL AND actual_completion_date < reported_date")
        log_fix("Repaired chronologically conflicting maintenance closure dates.")
    except Exception as e:
        print(f"Failed Fix 4: {e}")

    print("\n✅ All automated bug fixes complete! View fixes_applied.log for a complete audit trail.")

if __name__ == "__main__":
    fix_common_bugs()
