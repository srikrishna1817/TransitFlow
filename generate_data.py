import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

np.random.seed(42)
random.seed(42)

print("=" * 52)
print("  TRANSITFLOW — REALISTIC DATA GENERATOR v2.0")
print("=" * 52)

train_ids = [f"HMRL-{str(i).zfill(2)}" for i in range(1, 61)]

# ── 1. Fleet Status Distribution ──────────────────────────────────────
service_count   = random.randint(45, 48)
standby_count   = random.randint(6, 8)
maintenance_count = 60 - service_count - standby_count

statuses = ['Active'] * service_count + ['Standby'] * standby_count + ['Maintenance'] * maintenance_count
random.shuffle(statuses)

# ── 2. Manufacture years (spread 2015-2023) ─────────────────────────
years_manufactured = np.random.choice(range(2015, 2024), 60,
    p=[0.05, 0.08, 0.10, 0.12, 0.15, 0.15, 0.15, 0.12, 0.08])

# ── 3. Mileage correlated to age ─────────────────────────────────────
mileages = []
for yr in years_manufactured:
    age = 2025 - yr
    base = age * 35000
    mileages.append(int(base + random.randint(-10000, 10000)))

# ── 4. Health scores — normal distribution, clipped ───────────────────
health_scores = np.clip(np.random.normal(70, 15, 60), 30, 100).round(1)

# ── 5. Last maintenance — spread 5 to 60 days ago ─────────────────────
last_maint_days = []
for _ in range(60):
    roll = random.random()
    if roll < 0.30:           # recent
        days = random.randint(5, 15)
    elif roll < 0.75:         # normal
        days = random.randint(16, 44)
    else:                     # overdue
        days = random.randint(45, 90)
    last_maint_days.append(days)

last_maint_dates = [(datetime.now() - timedelta(days=d)).strftime('%Y-%m-%d')
                    for d in last_maint_days]

trains_data = {
    'Train_ID':              train_ids,
    'Current_Mileage':       mileages,
    'Running_Hours':         [int(m / 55) for m in mileages],
    'Last_Maintenance_Date': last_maint_dates,
    'Fitness_Valid_Until':   [(datetime.now() + timedelta(days=random.randint(-7, 270))).strftime('%Y-%m-%d')
                               for _ in range(60)],
    'Brand_Contract':        np.random.choice(['Yes', 'No'], 60, p=[0.4, 0.6]),
    'Status':                statuses,
    'health_score':          health_scores,
    'year_of_manufacture':   years_manufactured,
}

trains_df = pd.DataFrame(trains_data)
trains_df.to_csv('data/trains_master.csv', index=False)
print(f"\n✓ trains_master.csv   — Active:{statuses.count('Active')} "
      f"| Standby:{statuses.count('Standby')} | Maint:{statuses.count('Maintenance')}")

# ── 6. Maintenance Jobs ────────────────────────────────────────────────
FAILURE_TYPES = ['Brake System', 'Electrical/Power', 'Door Mechanism',
                 'HVAC/Climate', 'Signaling', 'Structural', 'Routine']
COST_RANGES = {
    'Brake System':      (80_000,  1_80_000),
    'Electrical/Power':  (1_20_000,4_50_000),
    'Door Mechanism':    (50_000,  1_20_000),
    'HVAC/Climate':      (90_000,  2_00_000),
    'Signaling':         (1_50_000,5_00_000),
    'Structural':        (2_00_000,8_00_000),
    'Routine':           (20_000,   60_000),
}
PRIORITY_MULTIPLIER = {'High': 1.5, 'Medium': 1.0, 'Low': 0.7}

job_cards = []
for i, train_id in enumerate(train_ids):
    n_jobs = random.randint(1, 3) if statuses[i] == 'Maintenance' else \
             (random.randint(0, 2) if random.random() < 0.45 else 0)
    for _ in range(n_jobs):
        priority = random.choices(['High', 'Medium', 'Low'], weights=[15, 45, 40])[0]
        failure  = random.choice(FAILURE_TYPES)
        lo, hi   = COST_RANGES[failure]
        cost     = int(random.randint(lo, hi) * PRIORITY_MULTIPLIER[priority])
        reported = datetime.now() - timedelta(days=random.randint(1, 30))
        status   = random.choices(['Open', 'Closed', 'In Progress'],
                                  weights=[40, 40, 20])[0]
        completion = reported + timedelta(days=random.randint(1, 10)) \
                     if status == 'Closed' else None

        job_cards.append({
            'Train_ID':                train_id,
            'Job_Card_ID':             f"JC-{random.randint(1000, 9999)}",
            'Status':                  status,
            'Priority':                priority,
            'Failure_Type':            failure,
            'Estimated_Hours':         random.randint(2, 24),
            'Cost_INR':                cost,
            'reported_date':           reported.strftime('%Y-%m-%d'),
            'actual_completion_date':  completion.strftime('%Y-%m-%d') if completion else None,
        })

maintenance_df = pd.DataFrame(job_cards)
maintenance_df.to_csv('data/maintenance_jobs.csv', index=False)
print(f"✓ maintenance_jobs.csv — {len(job_cards)} jobs generated")

# ── 7. Historical Operations (365 days, seasonal) ─────────────────────
SEASON_WEIGHTS = {
    12: 0.8, 1: 0.8, 2: 0.85,   # Winter
    3: 1.3, 4: 1.4, 5: 1.45,    # Summer
    6: 1.2, 7: 1.3, 8: 1.25, 9: 1.1,   # Monsoon
    10: 1.0, 11: 0.95            # Post-monsoon
}

historical_data = []
for day in range(365):
    date_obj = datetime.now() - timedelta(days=day)
    date_str = date_obj.strftime('%Y-%m-%d')
    month    = date_obj.month
    is_weekend = date_obj.weekday() >= 5
    season_w = SEASON_WEIGHTS.get(month, 1.0)
    sample_size = random.randint(42, 50)

    for train_id in random.sample(train_ids, sample_size):
        km = random.randint(300, 500) if is_weekend else random.randint(500, 700)
        base_issues = random.random()
        issue_prob  = min(0.6, 0.08 * season_w)
        issues = random.choices([0, 1, 2, 3], weights=[0.7, 0.18, 0.08, 0.04])[0] \
                 if base_issues < issue_prob else 0
        historical_data.append({
            'Date':            date_str,
            'Train_ID':        train_id,
            'Kilometers_Run':  km,
            'Issues_Reported': issues,
        })

historical_df = pd.DataFrame(historical_data)
historical_df.to_csv('data/historical_operations.csv', index=False)
print(f"✓ historical_operations.csv — {len(historical_data):,} records (365 days, seasonal)")

# ── 8. Fitness Certificates (realistic expiry distribution) ────────────
CERT_TYPES = ['Rolling_Stock', 'Signalling', 'Telecom']
fitness_data = []
for train_id in train_ids:
    for cert in CERT_TYPES:
        roll = random.random()
        if roll < 0.10:          # 10% expired
            days_ahead = random.randint(-60, -1)
            sts = 'Expired'
        elif roll < 0.25:        # 15% expiring within 7 days
            days_ahead = random.randint(0, 7)
            sts = 'Valid'
        elif roll < 0.45:        # 20% expiring 8-30 days
            days_ahead = random.randint(8, 30)
            sts = 'Valid'
        elif roll < 0.75:        # 30% expiring 31-90 days
            days_ahead = random.randint(31, 90)
            sts = 'Valid'
        else:                    # 25% healthy 90+ days
            days_ahead = random.randint(91, 365)
            sts = 'Valid'

        issue  = datetime.now() - timedelta(days=365 - days_ahead)
        expiry = datetime.now() + timedelta(days=days_ahead)
        fitness_data.append({
            'Train_ID':    train_id,
            'Department':  cert,
            'Valid_From':  issue.strftime('%Y-%m-%d'),
            'Valid_Until': expiry.strftime('%Y-%m-%d'),
            'Status':      sts,
        })

fitness_df = pd.DataFrame(fitness_data)
fitness_df.to_csv('data/fitness_certificates.csv', index=False)
expired_count = sum(1 for r in fitness_data if r['Status'] == 'Expired')
print(f"✓ fitness_certificates.csv — {len(fitness_data)} certs | {expired_count} expired")

print("\n🎉 All realistic datasets generated in data/ — run migration next!")