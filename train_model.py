# train_model.py

import pandas as pd
import numpy as np
import pickle
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


MODEL_PATH = "models/maintenance_predictor.pkl"


def train_model():
    """
    Train Random Forest model for maintenance prediction.
    """

    # Load datasets
    trains_df = pd.read_csv("data/trains_master.csv")
    historical_df = pd.read_csv("data/historical_operations.csv")

    train_features = []

    for train_id in trains_df["Train_ID"].unique():
        train_info = trains_df[trains_df["Train_ID"] == train_id].iloc[0]
        train_history = historical_df[
            historical_df["Train_ID"] == train_id
        ]

        last_maint = pd.to_datetime(train_info["Last_Maintenance_Date"])
        days_since_maint = (datetime.now() - last_maint).days

        recent_history = train_history.head(30)
        total_issues = (
            recent_history["Issues_Reported"].sum()
            if len(recent_history) > 0
            else 0
        )

        avg_km = (
            train_history["Kilometers_Run"].mean()
            if len(train_history) > 0
            else 0
        )

        # Calculate Time-Trend Feature: Recent_Issue_Spike
        train_history_sorted = train_history.sort_values(by="Date", ascending=False)
        recent_7_days = train_history_sorted.head(7)
        previous_23_days = train_history_sorted.iloc[7:30]

        issues_last_7 = recent_7_days["Issues_Reported"].sum() if len(recent_7_days) > 0 else 0
        issues_prev_23 = previous_23_days["Issues_Reported"].sum() if len(previous_23_days) > 0 else 0
        recent_issue_spike = issues_last_7 - issues_prev_23

        # Calculate a base risk score for target generation
        base_risk = 0.0
        if train_info["Current_Mileage"] > 12000: base_risk += 0.35
        if total_issues > 3: base_risk += 0.3
        if days_since_maint > 45: base_risk += 0.25
        if recent_issue_spike > 1: base_risk += 0.2

        # Add Gaussian noise to make target less predictable
        noisy_risk = base_risk + np.random.normal(0, 0.15)
        
        needs_maintenance = (noisy_risk > 0.6)

        train_features.append(
            {
                "Mileage": train_info["Current_Mileage"],
                "Days_Since_Maintenance": days_since_maint,
                "Running_Hours": train_info["Running_Hours"],
                "Total_Issues_30d": total_issues,
                "Avg_KM_Per_Day": avg_km,
                "Recent_Issue_Spike": recent_issue_spike,
                "Needs_Maintenance": 1 if needs_maintenance else 0,
            }
        )

    feature_df = pd.DataFrame(train_features)

    X = feature_df[
        [
            "Mileage",
            "Days_Since_Maintenance",
            "Running_Hours",
            "Total_Issues_30d",
            "Avg_KM_Per_Day",
            "Recent_Issue_Spike",
        ]
    ]
    y = feature_df["Needs_Maintenance"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)

    accuracy = accuracy_score(y_test, model.predict(X_test))

    # Save model
    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    return accuracy


def load_model():
    """
    Load pre-trained model.
    """
    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    return model


if __name__ == "__main__":
    acc = train_model()
    print(f"Model trained successfully. Accuracy: {acc*100:.2f}%")