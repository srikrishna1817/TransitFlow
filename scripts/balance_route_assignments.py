import sys, os, random
import pandas as pd
import numpy as np
from datetime import datetime, date

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

random.seed(42)

ROUTE_TARGETS = {
    'Red Line':   25,
    'Blue Line':  23,
    'Green Line': 12,
}

def balance_routes():
    print("Balancing route assignments across fleet...")
    trains_df = db.fetch_dataframe("SELECT train_id, health_score, status FROM trains_master ORDER BY health_score DESC")
    if trains_df is None or trains_df.empty:
        print("❌ No trains found. Run data migration first.")
        return

    service_trains = trains_df[trains_df['status'] == 'Active']['train_id'].tolist()
    standby_trains = trains_df[trains_df['status'] == 'Standby']['train_id'].tolist()
    maint_trains   = trains_df[trains_df['status'] == 'Maintenance']['train_id'].tolist()

    random.shuffle(service_trains)

    route_assignments = []
    pointer = 0
    today = date.today().isoformat()

    for route, target in ROUTE_TARGETS.items():
        batch = service_trains[pointer:pointer + target]
        pointer += target
        for train_id in batch:
            route_assignments.append({
                'train_id':   train_id,
                'schedule_date': today,
                'route':      route,
                'assignment': 'SERVICE',
                'shift':      random.choice(['Morning', 'Evening']),
            })

    for train_id in standby_trains:
        route_assignments.append({
            'train_id':      train_id,
            'schedule_date': today,
            'route':         'Depot',
            'assignment':    'STANDBY',
            'shift':         'All Day',
        })

    for train_id in maint_trains:
        route_assignments.append({
            'train_id':      train_id,
            'schedule_date': today,
            'route':         'Workshop',
            'assignment':    'MAINTENANCE',
            'shift':         'All Day',
        })

    df = pd.DataFrame(route_assignments)
    df.to_csv('data/balanced_schedule.csv', index=False)

    service_per_route = df[df['assignment'] == 'SERVICE']['route'].value_counts()
    print("Route Distribution:")
    for route, count in service_per_route.items():
        print(f"  {route}: {count} trains")
    print(f"  Standby: {len(standby_trains)} | Maintenance: {len(maint_trains)}")
    print(f"✅ Balanced schedule saved to data/balanced_schedule.csv")

if __name__ == "__main__":
    balance_routes()
