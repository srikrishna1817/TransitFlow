import pandas as pd
import streamlit as st
import datetime
from utils.db_utils import db
import logging

@st.cache_data(ttl=300)
def load_trains_data():
    """Fetch from trains_master table. Returns DataFrame."""
    try:
        df = db.fetch_dataframe("SELECT * FROM trains_master")
        if df is not None and not df.empty:
            # Map back to CSV compatibility names for the legacy Streamlit code
            mapping = {
                'train_id': 'Train_ID',
                'total_mileage_km': 'Current_Mileage',
                'total_running_hours': 'Running_Hours',
                'last_maintenance_date': 'Last_Maintenance_Date',
                'status': 'Status'
            }
            res = df.rename(columns=mapping)
            if 'Fitness_Valid_Until' not in res.columns:
                res['Fitness_Valid_Until'] = pd.to_datetime('today') + pd.Timedelta(days=30)
            if 'Brand_Contract' not in res.columns:
                res['Brand_Contract'] = 'Yes'
            return res
        return pd.read_csv("data/trains_master.csv")
    except Exception as e:
        logging.error(f"Fallback to CSV due to: {e}")
        return pd.read_csv("data/trains_master.csv")

@st.cache_data(ttl=300)
def load_certificates_data():
    """Fetch from fitness_certificates table."""
    try:
        df = db.fetch_dataframe("SELECT * FROM fitness_certificates")
        if df is not None and not df.empty:
            mapping = {
                'train_id': 'Train_ID',
                'certificate_type': 'Department',
                'status': 'Status',
                'issue_date': 'Valid_From',
                'expiry_date': 'Valid_Until'
            }
            return df.rename(columns=mapping)
        return pd.read_csv("data/fitness_certificates.csv")
    except Exception as e:
        logging.error(f"Fallback to CSV due to: {e}")
        return pd.read_csv("data/fitness_certificates.csv")

@st.cache_data(ttl=300)
def load_maintenance_jobs():
    """Fetch from maintenance_jobs table."""
    try:
        df = db.fetch_dataframe("SELECT * FROM maintenance_jobs")
        if df is not None and not df.empty:
            mapping = {
                'job_id': 'Job_Card_ID',
                'train_id': 'Train_ID',
                'status': 'Status',
                'priority': 'Priority',
                'estimated_hours': 'Estimated_Hours'
            }
            return df.rename(columns=mapping)
        return pd.read_csv("data/maintenance_jobs.csv")
    except Exception as e:
        logging.error(f"Fallback to CSV due to: {e}")
        return pd.read_csv("data/maintenance_jobs.csv")

@st.cache_data(ttl=300)
def load_historical_operations():
    """Fetch from historical_operations table ORDER BY date DESC."""
    try:
        df = db.fetch_dataframe("SELECT * FROM historical_operations ORDER BY operation_date DESC")
        if df is not None and not df.empty:
            mapping = {
                'operation_date': 'Date',
                'train_id': 'Train_ID',
                'kilometers_run': 'Kilometers_Run',
                'issues_reported': 'Issues_Reported'
            }
            return df.rename(columns=mapping)
        return pd.read_csv("data/historical_operations.csv")
    except Exception as e:
        logging.error(f"Fallback to CSV due to: {e}")
        return pd.read_csv("data/historical_operations.csv")

def save_daily_schedule(schedule_df, schedule_date, created_by='System'):
    """Save generated schedule to daily_schedules table"""
    try:
        if db.get_sqlalchemy_engine():
            # Delete existing for today
            db.execute_query("DELETE FROM daily_schedules WHERE schedule_date = %s", (schedule_date,), fetch=False)
            
            db_df = schedule_df.copy()
            # Safety cleanup, rename to match standard mapping
            db_df.columns = [c.lower() for c in db_df.columns]
            db_df['schedule_date'] = schedule_date
            db_df['created_at'] = datetime.datetime.now()
            db_df['created_by'] = created_by
            
            return db.insert_dataframe(db_df, 'daily_schedules')
        return False
    except Exception as e:
        logging.error(f"Failed to save schedule: {e}")
        return False

def log_alert(train_id, severity, category, description):
    """Insert into alerts_log table"""
    try:
        query = "INSERT INTO alerts_log (train_id, severity, category, description, status, created_at) VALUES (%s, %s, %s, %s, 'ACTIVE', %s)"
        return db.execute_query(query, (train_id, severity, category, description, datetime.datetime.now()), fetch=False)
    except Exception as e:
        logging.error(f"Failed to log alert: {e}")
        return False

def get_active_alerts():
    """Fetch active alerts"""
    try:
        return db.fetch_dataframe("SELECT * FROM alerts_log WHERE status = 'ACTIVE'")
    except Exception:
        return pd.DataFrame()

def acknowledge_alert(alert_id, acknowledged_by='System'):
    try:
        updates = "status = 'ACKNOWLEDGED', acknowledged_by = %s, acknowledged_at = %s"
        return db.update_record('alerts_log', updates, "id = %s", (acknowledged_by, datetime.datetime.now(), alert_id))
    except Exception:
        return False
