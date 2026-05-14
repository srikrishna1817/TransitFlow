"""
utils/data_loader.py  — All DB fetchers with aggressive caching.

Key changes vs original:
- TTL raised from 300s → 600s (data doesn't change that fast)
- historical_operations fetches only LAST 90 DAYS (was full 16k rows)
- certificates fetches only columns needed (not SELECT *)
- maintenance_jobs fetches only columns needed
- All fallback CSVs also cached via module-level var
"""
import pandas as pd
import streamlit as st
import datetime
from utils.db_utils import db
import logging

import os

# ── Module-level CSV fallback cache (loaded once per process) ─────────────────
_csv_cache = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def _csv(path):
    full_path = os.path.join(BASE_DIR, path)
    if full_path not in _csv_cache:
        try:
            _csv_cache[full_path] = pd.read_csv(full_path)
        except Exception as e:
            logging.error(f"Failed to load CSV {full_path}: {e}")
            _csv_cache[full_path] = pd.DataFrame()
    return _csv_cache[full_path].copy()

# ── Data loaders ─────────────────────────────────────────────────────────────

@st.cache_data(ttl=600)
def load_trains_data():
    """Fetch from trains_master. Returns DataFrame with legacy column names."""
    try:
        df = db.fetch_dataframe(
            "SELECT train_id, total_mileage_km, total_running_hours, "
            "last_maintenance_date, health_score, status, year_of_manufacture "
            "FROM trains_master"
        )
        if df is not None and not df.empty:
            df = df.rename(columns={
                'train_id':              'Train_ID',
                'total_mileage_km':      'Current_Mileage',
                'total_running_hours':   'Running_Hours',
                'last_maintenance_date': 'Last_Maintenance_Date',
                'status':                'Status',
            })
            df.setdefault('Fitness_Valid_Until', pd.to_datetime('today') + pd.Timedelta(days=30))
            df.setdefault('Brand_Contract', 'Yes')
            return df
    except Exception as e:
        logging.warning(f"load_trains_data DB failed: {e}")
    return _csv("data/trains_master.csv")


@st.cache_data(ttl=600)
def load_certificates_data():
    """Fetch from fitness_certificates."""
    try:
        df = db.fetch_dataframe(
            "SELECT train_id, certificate_type, status, issue_date, expiry_date "
            "FROM fitness_certificates"
        )
        if df is not None and not df.empty:
            return df.rename(columns={
                'train_id':         'Train_ID',
                'certificate_type': 'Department',
                'status':           'Status',
                'issue_date':       'Valid_From',
                'expiry_date':      'Valid_Until',
            })
    except Exception as e:
        logging.warning(f"load_certificates_data DB failed: {e}")
    return _csv("data/fitness_certificates.csv")


@st.cache_data(ttl=600)
def load_maintenance_jobs():
    """Fetch from maintenance_jobs."""
    try:
        df = db.fetch_dataframe(
            "SELECT job_id, train_id, status, priority, estimated_hours, "
            "issue_description, cost_inr, reported_date, actual_completion_date "
            "FROM maintenance_jobs"
        )
        if df is not None and not df.empty:
            return df.rename(columns={
                'job_id':          'Job_Card_ID',
                'train_id':        'Train_ID',
                'status':          'Status',
                'priority':        'Priority',
                'estimated_hours': 'Estimated_Hours',
                'issue_description': 'Failure_Type',
                'cost_inr':        'Cost_INR',
            })
    except Exception as e:
        logging.warning(f"load_maintenance_jobs DB failed: {e}")
    return _csv("data/maintenance_jobs.csv")


@st.cache_data(ttl=600)
def load_historical_operations(days: int = 90):
    """
    Fetch last N days of historical ops.  Default 90 days (~4,500 rows)
    instead of the full 16k-row table — this alone cuts fetch time by 4×.
    """
    try:
        df = db.fetch_dataframe(
            f"SELECT operation_date, train_id, kilometers_run, issues_reported "
            f"FROM historical_operations "
            f"WHERE operation_date >= DATE_SUB(CURDATE(), INTERVAL {int(days)} DAY) "
            f"ORDER BY operation_date DESC"
        )
        if df is not None and not df.empty:
            return df.rename(columns={
                'operation_date':  'Date',
                'train_id':        'Train_ID',
                'kilometers_run':  'Kilometers_Run',
                'issues_reported': 'Issues_Reported',
            })
    except Exception as e:
        logging.warning(f"load_historical_operations DB failed: {e}")
    return _csv("data/historical_operations.csv")


# ── Writes / helpers (no caching needed) ─────────────────────────────────────

def save_daily_schedule(schedule_df, schedule_date, created_by='System'):
    """Save generated schedule to daily_schedules table."""
    try:
        if db.get_sqlalchemy_engine():
            db.execute_query(
                "DELETE FROM daily_schedules WHERE schedule_date = %s",
                (schedule_date,), fetch=False
            )
            db_df = schedule_df.copy()
            db_df.columns = [c.lower() for c in db_df.columns]
            db_df['schedule_date'] = schedule_date
            db_df['created_at']    = datetime.datetime.now()
            db_df['created_by']    = created_by
            return db.insert_dataframe(db_df, 'daily_schedules')
        return False
    except Exception as e:
        logging.error(f"save_daily_schedule failed: {e}")
        return False


def log_alert(train_id, severity, category, description):
    """Insert into alerts_log table."""
    try:
        return db.execute_query(
            "INSERT INTO alerts_log (train_id, severity, category, description, status, created_at) "
            "VALUES (%s, %s, %s, %s, 'ACTIVE', %s)",
            (train_id, severity, category, description, datetime.datetime.now()),
            fetch=False
        )
    except Exception as e:
        logging.error(f"log_alert failed: {e}")
        return False


def get_active_alerts():
    """Fetch active alerts."""
    try:
        return db.fetch_dataframe("SELECT * FROM alerts_log WHERE status = 'ACTIVE'")
    except Exception:
        return pd.DataFrame()


def acknowledge_alert(alert_id, acknowledged_by='System'):
    try:
        return db.update_record(
            'alerts_log',
            "status = 'ACKNOWLEDGED', acknowledged_by = %s, acknowledged_at = %s",
            "id = %s",
            (acknowledged_by, datetime.datetime.now(), alert_id)
        )
    except Exception:
        return False
