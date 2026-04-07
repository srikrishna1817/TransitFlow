import sys
sys.path.append('.')
from utils.db_utils import db
import pandas as pd

print("🚀 Starting SAFE data migration of Phase 1D Datasets to MySQL...")

# 1. Truncate all data tables (bypassing foreign key drops)
db.execute_query("SET FOREIGN_KEY_CHECKS = 0;")
tables_to_clear = ['maintenance_jobs', 'fitness_certificates', 'historical_operations', 'trains_master']
for t in tables_to_clear:
    db.execute_query(f"TRUNCATE TABLE {t};")
db.execute_query("SET FOREIGN_KEY_CHECKS = 1;")
print("🧹 Cleared existing operational data.")

# 2. Migrate Trains
try:
    df_t = pd.read_csv('data/trains_master.csv')
    df_t_db = pd.DataFrame({
        'train_id':              df_t['Train_ID'],
        'manufacturer':          'Alstom / BEML',
        'year_of_manufacture':   df_t['year_of_manufacture'],
        'total_mileage_km':      df_t['Current_Mileage'],
        'total_running_hours':   df_t['Running_Hours'],
        'last_maintenance_date': df_t['Last_Maintenance_Date'],
        'last_maintenance_km':   df_t['Current_Mileage'] - 2000,
        'health_score':          df_t['health_score'],
        'status':                df_t['Status'],
    })
    db.insert_dataframe(df_t_db, 'trains_master', if_exists='append')
    print(f"✅ Migrated {len(df_t_db)} trains.")
except Exception as e:
    print(f"❌ Trains fail: {e}")

# 3. Migrate Maintenance
try:
    df_m = pd.read_csv('data/maintenance_jobs.csv')
    df_m_db = pd.DataFrame({
        'job_id':                 df_m['Job_Card_ID'],
        'train_id':               df_m['Train_ID'],
        'status':                 df_m['Status'],
        'priority':               df_m['Priority'],
        'estimated_hours':        df_m['Estimated_Hours'],
        'issue_description':      df_m['Failure_Type'],
        'cost_inr':               df_m['Cost_INR'],
        'reported_date':          df_m['reported_date'],
        'actual_completion_date': df_m['actual_completion_date'],
        'assigned_to':            'Team Alpha'
    })
    db.insert_dataframe(df_m_db, 'maintenance_jobs', if_exists='append')
    print(f"✅ Migrated {len(df_m_db)} maintenance jobs.")
except Exception as e:
    print(f"❌ Maintenance fail: {e}")

# 4. Migrate Fitness Certs
try:
    df_c = pd.read_csv('data/fitness_certificates.csv')
    df_c_db = pd.DataFrame({
        'train_id':         df_c['Train_ID'],
        'certificate_type': df_c['Department'],
        'issue_date':       df_c['Valid_From'],
        'expiry_date':      df_c['Valid_Until'],
        'status':           df_c['Status']
    })
    db.insert_dataframe(df_c_db, 'fitness_certificates', if_exists='append')
    print(f"✅ Migrated {len(df_c_db)} fitness certificates.")
except Exception as e:
    print(f"❌ Certs fail: {e}")

# 5. Migrate Historical Ops
try:
    df_h = pd.read_csv('data/historical_operations.csv')
    df_h_db = pd.DataFrame({
        'operation_date':   df_h['Date'],
        'train_id':         df_h['Train_ID'],
        'kilometers_run':   df_h['Kilometers_Run'],
        'issues_reported':  df_h['Issues_Reported'],
        'route_assigned':   'Red Line',
        'shift_type':       'Day'
    })
    db.insert_dataframe(df_h_db, 'historical_operations', if_exists='append')
    print(f"✅ Migrated {len(df_h_db)} historical records.")
except Exception as e:
    print(f"❌ History fail: {e}")

print("----------\n🚀 Phase 1D Safe Migration Complete!")
