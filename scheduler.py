# scheduler.py
import streamlit as st

import pandas as pd
import numpy as np
from datetime import datetime
from datetime import datetime


@st.cache_data(ttl=600)
def generate_schedule(required_service_trains=45, save_to_db=False):
    """
    Generate optimized train schedule.
    Returns:
        schedule_df (DataFrame)
         alerts (list of strings)
    """
    if not save_to_db:
        try:
            from utils.db_utils import db
            today = datetime.now().date()
            # Fetch pre-compiled AI schedule from DB instantly instead of running ML models repeatedly
            df = db.fetch_dataframe("SELECT * FROM daily_schedules WHERE schedule_date = %s", (today,))
            if df is not None and not df.empty:
                mapping = {
                    'train_id': 'Train_ID', 'priority_score': 'Priority_Score',
                    'ai_risk_percent': 'AI_Risk_Percent', 'days_since_maint': 'Days_Since_Maint',
                    'fitness_valid': 'Fitness_Valid', 'critical_job': 'Critical_Job',
                    'status': 'Status', 'assignment': 'Assignment', 'route': 'Route'
                }
                schedule_df = df.rename(columns=mapping)
                return schedule_df, []
        except Exception as e:
            print("DB shortcut failed, falling back to manual generation:", e)

    # Load datasets
    try:
        from utils.data_loader import load_trains_data, load_maintenance_jobs, load_certificates_data, load_historical_operations
        trains_df = load_trains_data()
        maintenance_df = load_maintenance_jobs()
        fitness_df = load_certificates_data()
        historical_df = load_historical_operations()
    except Exception:
        # Fallback
        trains_df = pd.read_csv("data/trains_master.csv")
        maintenance_df = pd.read_csv("data/maintenance_jobs.csv")
        fitness_df = pd.read_csv("data/fitness_certificates.csv")
        historical_df = pd.read_csv("data/historical_operations.csv")

    try:
        from ml.prediction_service import PredictionService
        svc = PredictionService()
        fleet_preds = svc.predict_all_fleet()
    except Exception as e:
        print(f"Warning: Advanced Predictor not loaded: {e}")
        fleet_preds = None

    alerts = []
    train_scores = []

    fleet_avg_mileage = trains_df["Current_Mileage"].mean()

    for _, train in trains_df.iterrows():

        train_id = train["Train_ID"]

        # Days since maintenance
        last_maint = pd.to_datetime(train["Last_Maintenance_Date"])
        days_since_maint = (datetime.now() - last_maint).days

        # Dynamic features from historical data
        train_history = historical_df[historical_df["Train_ID"] == train_id]
        train_history_sorted = train_history.sort_values(by="Date", ascending=False)
        
        recent_30_days = train_history_sorted.head(30)
        total_issues = recent_30_days["Issues_Reported"].sum() if len(recent_30_days) > 0 else 0
        avg_km = recent_30_days["Kilometers_Run"].mean() if len(recent_30_days) > 0 else 0
        
        recent_7_days = train_history_sorted.head(7)
        previous_23_days = train_history_sorted.iloc[7:30]
        issues_last_7 = recent_7_days["Issues_Reported"].sum() if len(recent_7_days) > 0 else 0
        issues_prev_23 = previous_23_days["Issues_Reported"].sum() if len(previous_23_days) > 0 else 0
        recent_issue_spike = issues_last_7 - issues_prev_23

        # Get advanced AI predictions
        ai_prediction = 0
        ai_probability = 15.0
        
        if fleet_preds is not None:
            pred_row = fleet_preds[fleet_preds['train_id'] == train_id]
            if not pred_row.empty:
                ai_probability = float(pred_row.iloc[0]['maintenance_probability'])
                ai_prediction = int(pred_row.iloc[0]['maintenance_required'])

        # ===== Hard Constraints =====

        train_fitness = fitness_df[
            fitness_df["Train_ID"] == train_id
        ]

        valid_fitness = all(
            (pd.to_datetime(cert["Valid_Until"]) >= datetime.now())
            and (cert["Status"] == "Valid")
            for _, cert in train_fitness.iterrows()
        )

        train_jobs = maintenance_df[
            maintenance_df["Train_ID"] == train_id
        ]

        has_critical_job = any(
            (job["Status"] == "Open")
            and (job["Priority"] == "High")
            for _, job in train_jobs.iterrows()
        )

        # ===== Scoring =====

        score = 100
        reason = "Available"

        if not valid_fitness:
            score = 0
            reason = "Invalid fitness certificate"
        elif has_critical_job:
            score = 0
            reason = "Critical maintenance pending"
        elif train["Status"] == "Maintenance":
            score = 0
            reason = "Already in maintenance"
        else:

            mileage_deviation = train["Current_Mileage"] - fleet_avg_mileage

            if ai_prediction == 1:
                score -= 40

            if mileage_deviation > 2000:
                score -= 25
            elif mileage_deviation < -2000:
                score += 15

            if train["Brand_Contract"] == "Yes":
                score += 20

            if days_since_maint < 15:
                score += 10
            elif days_since_maint > 50:
                score -= 15

        train_scores.append(
            {
                "Train_ID": train_id,
                "Priority_Score": max(0, score),
                "AI_Risk_Percent": round(ai_probability, 1),
                "Days_Since_Maint": days_since_maint,
                "Fitness_Valid": valid_fitness,
                "Critical_Job": has_critical_job,
                "Status": reason,
            }
        )

    schedule_df = pd.DataFrame(train_scores)
    schedule_df = schedule_df.sort_values(
        "Priority_Score", ascending=False
    ).reset_index(drop=True)

    # ===== Assignment =====

    schedule_df["Assignment"] = "MAINTENANCE"

    available_trains = schedule_df[
        schedule_df["Priority_Score"] > 0
    ]

    service_count = min(required_service_trains, len(available_trains))

    schedule_df.loc[
        schedule_df.index[:service_count],
        "Assignment",
    ] = "SERVICE"

    if len(available_trains) > service_count:
        standby_limit = min(
            service_count + 5, len(available_trains)
        )
        schedule_df.loc[
            schedule_df.index[service_count:standby_limit],
            "Assignment",
        ] = "STANDBY"

    # ===== Alerts =====

    # Fitness expiring soon
    for _, cert in fitness_df.iterrows():
        days_until_expiry = (
            pd.to_datetime(cert["Valid_Until"]) - datetime.now()
        ).days

        if 0 <= days_until_expiry <= 7:
            alerts.append(
                f"{cert['Train_ID']} - {cert['Department']} certificate expires in {days_until_expiry} days"
            )

    # High-risk trains in service
    high_risk_service = schedule_df[
        (schedule_df["Assignment"] == "SERVICE")
        & (schedule_df["AI_Risk_Percent"] > 50)
    ]

    for _, row in high_risk_service.iterrows():
        alerts.append(
            f"High AI maintenance risk: {row['Train_ID']} ({row['AI_Risk_Percent']}%) assigned to SERVICE"
        )

    if save_to_db:
        try:
            from utils.data_loader import save_daily_schedule
            save_daily_schedule(schedule_df, datetime.now().date())
        except Exception as e:
            print("Failed to save schedule to DB:", e)

    return schedule_df, alerts