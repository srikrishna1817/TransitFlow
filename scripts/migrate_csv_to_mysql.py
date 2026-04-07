import sys
import os
import pandas as pd
import numpy as np

# Add parent directory to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)
DATA_DIR = os.path.join(BASE_DIR, "data")

from utils.db_utils import db

def map_column_names(df, mapping):
    """Rename DataFrame columns safely"""
    return df.rename(columns=mapping)

def migrate_all_data():
    """Migrate all 4 CSV files to MySQL"""
    print("🚀 Starting data migration from CSV to MySQL...")
    total_records = 0
    
    # 1. trains_master
    try:
        print("\nMigrating trains_master.csv...")
        df_trains = pd.read_csv(os.path.join(DATA_DIR, "trains_master.csv"))
        df_trains['Last_Maintenance_Date'] = pd.to_datetime(df_trains['Last_Maintenance_Date'])
        mapping_trains = {
            'Train_ID': 'train_id',
            'Current_Mileage': 'total_mileage_km', 
            'Running_Hours': 'total_running_hours',
            'Last_Maintenance_Date': 'last_maintenance_date',
            'Status': 'status'
        }
        df_trains = map_column_names(df_trains, mapping_trains)
        
        # Add missing columns requested
        if 'manufacturer' not in df_trains.columns:
            df_trains['manufacturer'] = 'HMRL Corp'
        if 'year_of_manufacture' not in df_trains.columns:
            df_trains['year_of_manufacture'] = 2018
        if 'last_maintenance_km' not in df_trains.columns:
            df_trains['last_maintenance_km'] = df_trains['total_mileage_km'] - 2000
        if 'health_score' not in df_trains.columns:
            df_trains['health_score'] = 100
            
        success = db.insert_dataframe(df_trains, 'trains_master', 'replace')
        if success:
            print(f"✅ Successfully migrated {len(df_trains)} trains.")
            total_records += len(df_trains)
    except Exception as e:
        print(f"❌ Error migrating trains: {e}")

    # 2. fitness_certificates
    try:
        print("\nMigrating fitness_certificates.csv...")
        df_certs = pd.read_csv(os.path.join(DATA_DIR, "fitness_certificates.csv"))
        df_certs['Valid_From'] = pd.to_datetime(df_certs['Valid_From'])
        df_certs['Valid_Until'] = pd.to_datetime(df_certs['Valid_Until'])
        mapping_certs = {
            'Train_ID': 'train_id',
            'Department': 'certificate_type',
            'Status': 'status',
            'Valid_From': 'issue_date',
            'Valid_Until': 'expiry_date'
        }
        df_certs = map_column_names(df_certs, mapping_certs)
        if 'certificate_id' in df_certs.columns:
            df_certs = df_certs.drop(columns=['certificate_id'])
            
        success = db.insert_dataframe(df_certs, 'fitness_certificates', 'replace')
        if success:
            print(f"✅ Successfully migrated {len(df_certs)} certificates.")
            total_records += len(df_certs)
    except Exception as e:
        print(f"❌ Error migrating certificates: {e}")

    # 3. maintenance_jobs
    try:
        print("\nMigrating maintenance_jobs.csv...")
        df_jobs = pd.read_csv(os.path.join(DATA_DIR, "maintenance_jobs.csv"))
        mapping_jobs = {
            'Job_Card_ID': 'job_id',
            'Train_ID': 'train_id',
            'Status': 'status',
            'Priority': 'priority',
            'Estimated_Hours': 'estimated_hours'
        }
        df_jobs = map_column_names(df_jobs, mapping_jobs)
        
        if 'reported_date' in df_jobs.columns:
            df_jobs['reported_date'] = pd.to_datetime(df_jobs['reported_date'])
        else:
            df_jobs['reported_date'] = pd.to_datetime('today') - pd.to_timedelta(np.random.randint(1, 10, len(df_jobs)), unit='D')
            
        if 'estimated_completion_date' not in df_jobs.columns:
            df_jobs['estimated_completion_date'] = df_jobs['reported_date'] + pd.to_timedelta(2, unit='D')
        if 'actual_completion_date' not in df_jobs.columns:
            df_jobs['actual_completion_date'] = None
        if 'issue_description' not in df_jobs.columns:
            df_jobs['issue_description'] = 'Routine Maintenance'
        if 'assigned_to' not in df_jobs.columns:
            df_jobs['assigned_to'] = 'Team Alpha'
            
        success = db.insert_dataframe(df_jobs, 'maintenance_jobs', 'replace')
        if success:
            print(f"✅ Successfully migrated {len(df_jobs)} maintenance jobs.")
            total_records += len(df_jobs)
    except Exception as e:
        print(f"❌ Error migrating maintenance jobs: {e}")

    # 4. historical_operations
    try:
        print("\nMigrating historical_operations.csv...")
        df_ops = pd.read_csv(os.path.join(DATA_DIR, "historical_operations.csv"))
        df_ops['Date'] = pd.to_datetime(df_ops['Date'])
        mapping_ops = {
            'Date': 'operation_date',
            'Train_ID': 'train_id',
            'Kilometers_Run': 'kilometers_run',
            'Issues_Reported': 'issues_reported'
        }
        df_ops = map_column_names(df_ops, mapping_ops)
        
        df_ops['route_assigned'] = 'Red Line'
        df_ops['shift_type'] = 'Day'
        if 'operation_id' in df_ops.columns:
            df_ops = df_ops.drop(columns=['operation_id'])
            
        success = db.insert_dataframe(df_ops, 'historical_operations', 'replace')
        if success:
            print(f"✅ Successfully migrated {len(df_ops)} historical operations.")
            total_records += len(df_ops)
    except Exception as e:
        print(f"❌ Error migrating historical operations: {e}")

    print(f"\n🎉 Migration Complete! Total nested records migrated: {total_records}")

if __name__ == "__main__":
    migrate_all_data()
