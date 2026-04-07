import sys, os, random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

random.seed(42)
np.random.seed(42)

ROUTES = {
    'Red Line':   'Miyapur',
    'Blue Line':  'Uppal',
    'Green Line': 'JBS',
}
DESIGNATIONS = ['Driver', 'Co-Driver', 'Guard', 'Technician']

def generate_crew():
    print("Generating realistic crew roster...")
    crew = []
    for i in range(1, 121):  # 120 crew members
        roll = random.random()
        if roll < 0.30:      # New (1-3 yrs)
            exp_years = random.randint(1, 3)
            routes_cert = 1
        elif roll < 0.80:    # Mid (4-8 yrs)
            exp_years = random.randint(4, 8)
            routes_cert = random.randint(1, 2)
        else:                # Senior (9+ yrs)
            exp_years = random.randint(9, 20)
            routes_cert = 3

        home_route = random.choice(list(ROUTES.keys()))
        home_depot = ROUTES[home_route]
        on_leave   = random.random() < 0.12  # 12% on leave
        weekly_hrs = random.randint(40, 48)  if not on_leave else 0

        all_routes = list(ROUTES.keys())
        certified  = random.sample(all_routes, min(routes_cert, len(all_routes)))

        crew.append({
            'crew_id':              f"CR-{str(i).zfill(3)}",
            'name':                 f"Crew Member {i}",
            'designation':          random.choice(DESIGNATIONS),
            'experience_years':     exp_years,
            'home_depot':           home_depot,
            'certified_routes':     ','.join(certified),
            'on_leave':             on_leave,
            'weekly_hours':         weekly_hrs,
            'max_hours_per_shift':  8,
            'shift_type':           random.choice(['Day', 'Evening', 'Night']),
        })

    df = pd.DataFrame(crew)
    try:
        db.execute_query("DELETE FROM crew_master")
        db.insert_dataframe(df, 'crew_master', if_exists='append')
        print(f"✅ Inserted {len(df)} realistic crew records into DB.")
    except Exception as e:
        print(f"DB insert failed: {e}. Saving to CSV instead.")
        df.to_csv('data/crew_master_realistic.csv', index=False)

if __name__ == "__main__":
    generate_crew()
