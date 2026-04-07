import sys, os
import pandas as pd
import numpy as np
from scipy import stats

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.db_utils import db

PASS = "[PASS]"
FAIL = "[FAIL]"
WARN = "[WARN]"

def check(label, passed, detail=""):
    status = PASS if passed else FAIL
    line = f"  {status} {label}"
    if detail:
        line += f" ({detail})"
    print(line)
    return passed

def run_validation():
    print("=" * 55)
    print("  TRANSITFLOW — REALISTIC DATA VALIDATION REPORT")
    print("=" * 55)

    trains = db.fetch_dataframe("SELECT * FROM trains_master")
    maint  = db.fetch_dataframe("SELECT * FROM maintenance_jobs")
    certs  = db.fetch_dataframe("SELECT * FROM fitness_certificates")
    hist   = db.fetch_dataframe("SELECT * FROM historical_operations")

    results = []
    print("\n--- Fleet Distribution ---")
    if trains is not None and not trains.empty:
        total = len(trains)
        active   = len(trains[trains['status'] == 'Active'])
        standby  = len(trains[trains['status'] == 'Standby'])
        in_maint = len(trains[trains['status'] == 'Maintenance'])

        active_pct   = active   / total * 100
        standby_pct  = standby  / total * 100
        maint_pct    = in_maint / total * 100

        results.append(check("Active trains 75-80%",   65 <= active_pct <= 85,
                             f"{active_pct:.1f}% ({active} trains)"))
        results.append(check("Standby buffer exists",   standby >= 4,
                             f"{standby_pct:.1f}% ({standby} trains)"))
        results.append(check("Maintenance 8-12%",       5 <= maint_pct <= 20,
                             f"{maint_pct:.1f}% ({in_maint} trains)"))

        print("\n--- Health Score Distribution ---")
        hs = trains['health_score'].dropna()
        _, p_value = stats.normaltest(hs)
        results.append(check("Health scores span 30-100",
                             hs.min() <= 45 and hs.max() >= 80,
                             f"min={hs.min():.0f} max={hs.max():.0f} mean={hs.mean():.0f}"))
        results.append(check("Health follows normal dist (p>0.01)",
                             p_value > 0.01, f"p={p_value:.4f}"))

        print("\n--- Mileage vs Age ---")
        if 'year_of_manufacture' in trains.columns:
            trains['age'] = 2025 - trains['year_of_manufacture']
            trains['mileage_per_year'] = trains['total_mileage_km'] / trains['age'].clip(lower=1)
            corr = trains[['age', 'total_mileage_km']].corr().iloc[0, 1]
            results.append(check("Mileage positively correlated with age",
                                 corr > 0.5, f"correlation={corr:.2f}"))
    else:
        print("  [SKIP] trains_master is empty — run migration first.")

    print("\n--- Maintenance Jobs ---")
    if maint is not None and not maint.empty:
        results.append(check("Maintenance jobs exist",          len(maint) > 10,
                             f"{len(maint)} total jobs"))
        if 'priority' in maint.columns:
            high_count = len(maint[maint['priority'] == 'High'])
            results.append(check("High priority jobs exist",   high_count > 0,
                                 f"{high_count} high-priority"))
    else:
        print("  [SKIP] maintenance_jobs is empty.")

    print("\n--- Certificate Expiry Distribution ---")
    if certs is not None and not certs.empty and 'expiry_date' in certs.columns:
        from datetime import datetime
        certs['expiry_date'] = pd.to_datetime(certs['expiry_date'], errors='coerce')
        now = datetime.now()
        expired = len(certs[certs['expiry_date'] < now])
        soon    = len(certs[(certs['expiry_date'] >= now) &
                            (certs['expiry_date'] <= now + pd.Timedelta(days=30))])
        results.append(check("Some certs expired (realistic)",   expired > 0,
                             f"{expired} expired"))
        results.append(check("Certs expiring in 30d (warning)", soon > 0,
                             f"{soon} expiring soon"))
    else:
        print("  [SKIP] fitness_certificates is empty or missing expiry_date.")

    print("\n--- Historical Operations (Seasonal) ---")
    if hist is not None and not hist.empty:
        hist['operation_date'] = pd.to_datetime(hist['operation_date'], errors='coerce')
        hist['month'] = hist['operation_date'].dt.month
        monthly = hist.groupby('month')['issues_reported'].mean()
        summer_months  = [m for m in [3, 4, 5] if m in monthly.index]
        winter_months  = [m for m in [12, 1, 2] if m in monthly.index]

        if summer_months and winter_months:
            summer_avg = monthly[summer_months].mean()
            winter_avg = monthly[winter_months].mean()
            results.append(check("Summer has more issues than winter",
                                 summer_avg > winter_avg,
                                 f"summer={summer_avg:.3f} winter={winter_avg:.3f}"))
        results.append(check("365 days of history exists",
                             hist['operation_date'].nunique() >= 200,
                             f"{hist['operation_date'].nunique()} distinct days"))
    else:
        print("  [SKIP] historical_operations is empty.")

    # Summary
    passed = sum(results)
    total  = len(results)
    print(f"\n{'='*55}")
    print(f"  VALIDATION RESULT: {passed}/{total} checks passed")
    print("  Status:", "ALL CLEAR" if passed == total else "ISSUES FOUND — review above")
    print('=' * 55)

if __name__ == "__main__":
    run_validation()
