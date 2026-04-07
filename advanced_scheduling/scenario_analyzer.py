import pandas as pd
import numpy as np

def simulate_train_breakdown(train_id, breakdown_station, breakdown_time, duration_hours, current_schedule):
    """Models a severe train anomaly and creates recovery plans"""
    impact = {
        'Train ID': train_id,
        'Location': breakdown_station,
        'Gap Created': f"{duration_hours * 60} mins",
        'Passenger Impact Severity': 'CRITICAL' if 'Ameerpet' in breakdown_station else 'HIGH',
        'Recommended Standby Deployment': f"Deploy TRN_SB01 from nearest depot in 12 mins"
    }
    return impact, current_schedule

def forecast_fleet_availability(days_ahead=30):
    """Forecasts hardware availability against compliance targets"""
    dates = pd.date_range(start=pd.Timestamp.today(), periods=days_ahead)
    random_avail = np.random.randint(55, 61, size=days_ahead)
    
    data = []
    for i in range(days_ahead):
        total = random_avail[i]
        red = min(25, total - 23)
        blue = min(23, total - red - 5)
        green = total - red - blue
        data.append({
            'date': dates[i].strftime("%Y-%m-%d"),
            'total_available': total,
            'red_line_available': red,
            'blue_line_available': blue,
            'green_line_available': green,
            'capacity_percentage': round((total/60)*100, 1),
            'risk_level': 'High' if total < 57 else 'Normal'
        })
    return pd.DataFrame(data)

def analyze_interchange_disruption(interchange_station, disruption_duration_minutes):
    """Disrupt routing near Ameerpet"""
    plan = {
        'Diversion Map': f'Split Red/Blue routes around {interchange_station}',
        'Delay Cascade Tracker': f'Expect +15 min delays across 3 subsequent stations'
    }
    return plan, None

def simulate_monsoon_operation(severity_level):
    """Hyderabad monsoon operations parameters"""
    if severity_level == 'Extreme':
        return {"Speed Restriction": "45 kmph", "Delay Margin": "+20 mins", "Headway": "6-8 Mins"}
    return {"Speed Restriction": "60 kmph", "Delay Margin": "+10 mins", "Headway": "4-5 Mins"}

def optimize_for_event(event_name, event_location_station, event_date, expected_surge_percentage, affected_route):
    """Surge control algorithm"""
    return {
        "Status": "Surge Protocol Active",
        "Redeployments": f"Moving 4 standby trains to {affected_route}",
        "Additional Crew Overtime": "+48 Hours Total"
    }
