"""
Advanced Feature Engineering for TransitFlow HMRL ML System.
Expands from ~5 basic features to 25+ engineered features.
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# Try importing database utilities; fall back gracefully
try:
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.data_loader import load_trains_data, load_certificates_data, load_historical_operations, load_maintenance_jobs
    DB_AVAILABLE = True
except Exception:
    DB_AVAILABLE = False


class FeatureEngineer:
    """Creates 25+ features from raw HMRL operational data."""

    FEATURE_COLUMNS = [
        # Temporal
        'days_since_maintenance', 'season', 'day_of_week', 'is_weekend',
        # Operational
        'avg_daily_mileage_30d', 'mileage_deviation_from_avg', 'route_intensity',
        'total_km', 'total_hours',
        # Issue history
        'total_issues_30d', 'recent_issue_spike', 'high_priority_count', 'open_issues',
        # Train age & health
        'train_age_years', 'health_score', 'is_aging_fleet',
        # Certificate health
        'days_until_rolling_stock_expiry', 'days_until_signalling_expiry',
        'days_until_telecom_expiry', 'any_cert_expired', 'min_days_to_expiry',
        # Comparative / percentile
        'mileage_percentile', 'health_percentile',
        # Interactions
        'mileage_age_interaction', 'issues_per_1000km',
    ]

    def __init__(self):
        self.fleet_avg_mileage = None
        self.fleet_avg_health = None

    def _load_data(self):
        """Load raw data from DB or generate synthetic fallback."""
        if DB_AVAILABLE:
            try:
                trains = load_trains_data()
                certs = load_certificates_data()
                hist = load_historical_operations()
                maint = load_maintenance_jobs()
                return trains, certs, hist, maint
            except Exception as e:
                logger.warning(f"DB load failed: {e}. Using synthetic data.")
        return self._synthetic_data()

    def _synthetic_data(self):
        """Generate plausible synthetic data for 60 HMRL trains."""
        np.random.seed(42)
        n = 60
        train_ids = [f"HMRL-{i+1:02d}" for i in range(n)]
        today = datetime.now().date()

        trains = pd.DataFrame({
            'train_id': train_ids,
            'year_of_manufacture': np.random.randint(2010, 2022, n),
            'total_km': np.random.randint(50000, 500000, n),
            'health_score': np.random.randint(50, 100, n),
            'last_maintenance_date': [
                (today - timedelta(days=int(d))).strftime('%Y-%m-%d')
                for d in np.random.randint(0, 180, n)
            ],
        })

        cert_types = ['Rolling_Stock', 'Signalling', 'Telecom']
        cert_rows = []
        for tid in train_ids:
            for ct in cert_types:
                exp = today + timedelta(days=int(np.random.randint(-5, 365)))
                cert_rows.append({'train_id': tid, 'certificate_type': ct,
                                   'expiry_date': exp.strftime('%Y-%m-%d')})
        certs = pd.DataFrame(cert_rows)

        hist_rows = []
        for tid in train_ids:
            for _ in range(np.random.randint(5, 20)):
                hist_rows.append({
                    'train_id': tid,
                    'date': (today - timedelta(days=int(np.random.randint(0, 90)))).strftime('%Y-%m-%d'),
                    'km_run': np.random.randint(100, 600),
                    'hours_operated': np.random.uniform(2, 14),
                    'issues_reported': np.random.randint(0, 5),
                    'priority': np.random.choice(['LOW', 'MEDIUM', 'HIGH'], p=[0.6, 0.3, 0.1]),
                })
        hist = pd.DataFrame(hist_rows)

        maint_rows = []
        for tid in train_ids:
            maint_rows.append({
                'train_id': tid,
                'status': np.random.choice(['OPEN', 'CLOSED'], p=[0.3, 0.7]),
                'priority': np.random.choice(['LOW', 'MEDIUM', 'HIGH'], p=[0.5, 0.3, 0.2]),
            })
        maint = pd.DataFrame(maint_rows)

        return trains, certs, hist, maint

    def create_all_features(self, train_ids=None):
        """
        Build the full 25+ feature matrix.
        Returns: DataFrame indexed by train_id with all feature columns.
        """
        trains, certs, hist, maint = self._load_data()

        # Normalize column names
        for df in [trains, certs, hist, maint]:
            df.columns = [c.lower() for c in df.columns]

        # Resolve train_id column variants
        for df in [trains, certs, hist, maint]:
            if 'train_id' not in df.columns and 'id' in df.columns:
                df.rename(columns={'id': 'train_id'}, inplace=True)

        today = datetime.now().date()
        all_ids = trains['train_id'].unique() if train_ids is None else train_ids
        records = []

        # Fleet-level stats for percentile features
        trains['total_km'] = pd.to_numeric(trains.get('total_km', pd.Series([200000]*len(trains))), errors='coerce').fillna(200000)
        trains['health_score'] = pd.to_numeric(trains.get('health_score', pd.Series([80]*len(trains))), errors='coerce').fillna(80)
        self.fleet_avg_mileage = trains['total_km'].mean()
        self.fleet_avg_health = trains['health_score'].mean()

        for tid in all_ids:
            try:
                rec = self._build_train_features(tid, trains, certs, hist, maint, today)
                records.append(rec)
            except Exception as e:
                logger.warning(f"Feature build failed for {tid}: {e}")

        feature_df = pd.DataFrame(records)
        feature_df = feature_df.fillna(0)
        return feature_df

    def _build_train_features(self, tid, trains, certs, hist, maint, today):
        """Build feature dict for a single train."""
        t = trains[trains['train_id'] == tid]
        if t.empty:
            t_info = {'year_of_manufacture': 2015, 'total_km': 200000, 'health_score': 75}
        else:
            t_info = t.iloc[0].to_dict()

        # --- Temporal features ---
        last_maint_raw = t_info.get('last_maintenance_date', str(today - timedelta(days=30)))
        try:
            last_maint = datetime.strptime(str(last_maint_raw)[:10], '%Y-%m-%d').date()
        except Exception:
            last_maint = today - timedelta(days=30)
        days_since_maint = (today - last_maint).days
        season = (today.month % 12) // 3   # 0=Winter 1=Spring 2=Summer 3=Monsoon
        day_of_week = today.weekday()
        is_weekend = int(day_of_week >= 5)

        # --- Operational features ---
        t_hist = hist[hist['train_id'] == tid].copy() if 'train_id' in hist.columns else pd.DataFrame()
        if not t_hist.empty and 'date' in t_hist.columns:
            t_hist['date'] = pd.to_datetime(t_hist['date'], errors='coerce')
            t_hist_30d = t_hist[t_hist['date'] >= pd.Timestamp(today - timedelta(days=30))]
        else:
            t_hist_30d = pd.DataFrame()

        km_col = 'km_run' if 'km_run' in t_hist.columns else ('km' if 'km' in t_hist.columns else None)
        if km_col and not t_hist_30d.empty:
            avg_daily_km = t_hist_30d[km_col].mean()
        else:
            avg_daily_km = 300.0

        fleet_avg_daily = self.fleet_avg_mileage / 365 if self.fleet_avg_mileage else 300
        mileage_dev = avg_daily_km - fleet_avg_daily
        total_km = float(t_info.get('total_km', 200000))
        total_hours = total_km / 35  # approximate from avg commercial speed
        # Route intensity: proxy from avg daily km
        route_intensity = min(1.0, avg_daily_km / 600.0)

        # --- Issue history features ---
        issue_col = 'issues_reported' if 'issues_reported' in t_hist.columns else None
        if issue_col and not t_hist_30d.empty:
            total_issues_30d = int(t_hist_30d[issue_col].sum())
            # spike = if last 7d issues > 7d-30d issues
            t_hist_7d = t_hist[t_hist['date'] >= pd.Timestamp(today - timedelta(days=7))]
            spike = int(not t_hist_7d.empty and t_hist_7d[issue_col].sum() > (total_issues_30d / 4))
        else:
            total_issues_30d = 0
            spike = 0

        t_maint = maint[maint['train_id'] == tid] if 'train_id' in maint.columns else pd.DataFrame()
        high_pri = int((t_maint['priority'] == 'HIGH').sum()) if not t_maint.empty and 'priority' in t_maint.columns else 0
        open_issues = int((t_maint['status'] == 'OPEN').sum()) if not t_maint.empty and 'status' in t_maint.columns else 0

        # --- Train age & health ---
        mfr_year = int(t_info.get('year_of_manufacture', 2015))
        train_age = today.year - mfr_year
        health = float(t_info.get('health_score', 75))
        is_aging = int(train_age > 10)

        # --- Certificate features ---
        t_certs = certs[certs['train_id'] == tid] if 'train_id' in certs.columns else pd.DataFrame()
        def days_to_expiry(cert_type):
            if t_certs.empty or 'certificate_type' not in t_certs.columns:
                return 365
            row = t_certs[t_certs['certificate_type'].str.lower() == cert_type.lower()]
            if row.empty:
                return 365
            try:
                exp = datetime.strptime(str(row.iloc[0]['expiry_date'])[:10], '%Y-%m-%d').date()
                return (exp - today).days
            except Exception:
                return 365

        d_rolling = days_to_expiry('Rolling_Stock')
        d_signal = days_to_expiry('Signalling')
        d_telecom = days_to_expiry('Telecom')
        any_expired = int(min(d_rolling, d_signal, d_telecom) < 0)
        min_days = min(d_rolling, d_signal, d_telecom)

        # --- Comparative features ---
        km_pct = float(np.sum(trains['total_km'] <= total_km) / max(len(trains), 1) * 100)
        health_pct = float(np.sum(trains['health_score'] <= health) / max(len(trains), 1) * 100)

        # --- Interaction features ---
        mileage_age_interaction = total_km * train_age / 1e6
        issues_per_1000km = (total_issues_30d / max(total_km / 1000, 1))

        return {
            'train_id': tid,
            # Temporal
            'days_since_maintenance': days_since_maint,
            'season': season,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            # Operational
            'avg_daily_mileage_30d': round(avg_daily_km, 2),
            'mileage_deviation_from_avg': round(mileage_dev, 2),
            'route_intensity': round(route_intensity, 3),
            'total_km': total_km,
            'total_hours': round(total_hours, 1),
            # Issue history
            'total_issues_30d': total_issues_30d,
            'recent_issue_spike': spike,
            'high_priority_count': high_pri,
            'open_issues': open_issues,
            # Age & health
            'train_age_years': train_age,
            'health_score': health,
            'is_aging_fleet': is_aging,
            # Certificates
            'days_until_rolling_stock_expiry': d_rolling,
            'days_until_signalling_expiry': d_signal,
            'days_until_telecom_expiry': d_telecom,
            'any_cert_expired': any_expired,
            'min_days_to_expiry': min_days,
            # Comparative
            'mileage_percentile': round(km_pct, 1),
            'health_percentile': round(health_pct, 1),
            # Interactions
            'mileage_age_interaction': round(mileage_age_interaction, 4),
            'issues_per_1000km': round(issues_per_1000km, 4),
        }
