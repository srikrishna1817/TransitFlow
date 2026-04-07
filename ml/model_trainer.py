"""
Automated Model Retraining for TransitFlow HMRL.
Detects drift, performance degradation, and schedules retrains.
"""
import os
import pickle
import logging
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
RETRAIN_INTERVAL_DAYS = 7
NEW_DATA_THRESHOLD = 100
DRIFT_THRESHOLD_PCT = 0.20  # 20% change triggers retrain


class ModelTrainer:
    """Manages lifecycle: check drift → retrain → compare → deploy."""

    def __init__(self):
        self.current_model_path = os.path.join(MODEL_DIR, 'maintenance_predictor_advanced.pkl')
        self.current_metrics = self._load_current_metrics()

    def _load_current_metrics(self):
        if not os.path.exists(self.current_model_path):
            return {}
        try:
            with open(self.current_model_path, 'rb') as f:
                bundle = pickle.load(f)
            return bundle.get('metrics', {})
        except Exception:
            return {}

    def _get_last_trained_date(self):
        metrics = self.current_metrics
        trained_at = metrics.get('trained_at')
        if trained_at:
            try:
                return datetime.fromisoformat(trained_at)
            except Exception:
                pass
        # Fallback: use file mtime
        if os.path.exists(self.current_model_path):
            mtime = os.path.getmtime(self.current_model_path)
            return datetime.fromtimestamp(mtime)
        return datetime.now() - timedelta(days=100)

    def _count_new_samples(self):
        """Check how many new historical_operations records since last train."""
        try:
            from utils.db_utils import db
            last_date = self._get_last_trained_date().strftime('%Y-%m-%d')
            result = db.fetch_dataframe(
                f"SELECT COUNT(*) as cnt FROM historical_operations WHERE created_at >= '{last_date}'"
            )
            if result is not None and not result.empty:
                return int(result.iloc[0]['cnt'])
        except Exception:
            pass
        return 0

    def _detect_drift(self):
        """Compare current fleet avg mileage vs training-time baseline."""
        try:
            from utils.data_loader import load_historical_operations
            hist = load_historical_operations()
            km_col = 'km_run' if 'km_run' in hist.columns else ('km' if 'km' in hist.columns else None)
            if km_col:
                current_avg = hist[km_col].mean()
                baseline = self.current_metrics.get('baseline_avg_mileage', current_avg)
                drift_pct = abs(current_avg - baseline) / max(baseline, 1)
                return drift_pct > DRIFT_THRESHOLD_PCT, round(drift_pct * 100, 1)
        except Exception:
            pass
        return False, 0.0

    def should_retrain(self):
        """
        Evaluate whether retraining is needed.
        Returns: (bool, reason_string)
        """
        reasons = []

        # 1. Time-based
        last_trained = self._get_last_trained_date()
        days_since = (datetime.now() - last_trained).days
        if days_since >= RETRAIN_INTERVAL_DAYS:
            reasons.append(f"⏰ {days_since} days since last training (threshold: {RETRAIN_INTERVAL_DAYS}d)")

        # 2. New data volume
        new_samples = self._count_new_samples()
        if new_samples >= NEW_DATA_THRESHOLD:
            reasons.append(f"📊 {new_samples} new samples available (threshold: {NEW_DATA_THRESHOLD})")

        # 3. Drift detection
        drifted, drift_pct = self._detect_drift()
        if drifted:
            reasons.append(f"📉 Data drift detected: {drift_pct}% change in avg mileage")

        # 4. Performance degradation (if we have stored accuracy)
        acc = self.current_metrics.get('maintenance_accuracy', 1.0)
        if acc < 0.70:
            reasons.append(f"⚠ Model accuracy dropped to {acc:.1%} (threshold: 70%)")

        if not os.path.exists(self.current_model_path):
            reasons.append("🆕 No trained model found — first-time training needed")

        return bool(reasons), '; '.join(reasons) if reasons else "✅ No retraining needed."

    def train_new_model(self):
        """Full training pipeline: feature engineering → multi-output training → save."""
        from ml.feature_engineer import FeatureEngineer
        from ml.advanced_predictor import AdvancedMaintenancePredictor

        logger.info("Starting new model training...")
        fe = FeatureEngineer()
        feature_df = fe.create_all_features()

        predictor = AdvancedMaintenancePredictor()
        metrics = predictor.train(feature_df)

        # Log to DB
        self._log_deployment(metrics)

        logger.info(f"New model trained. Metrics: {metrics}")
        return predictor, metrics

    def compare_with_production(self, new_predictor):
        """
        A/B comparison: old model accuracy vs. new model accuracy.
        Returns: dict with comparison results.
        """
        old_acc = self.current_metrics.get('maintenance_accuracy', 0)
        new_acc = new_predictor.metrics_.get('maintenance_accuracy', 0)
        improvement = round(new_acc - old_acc, 4)
        return {
            'old_accuracy': old_acc,
            'new_accuracy': new_acc,
            'improvement': improvement,
            'old_f1': self.current_metrics.get('maintenance_f1', 0),
            'new_f1': new_predictor.metrics_.get('maintenance_f1', 0),
            'recommendation': '✅ Deploy new model' if improvement >= 0 else '⚠ Keep current model',
        }

    def _log_deployment(self, metrics):
        """Write training result to model_deployments table."""
        try:
            from utils.db_utils import db
            db.execute("""
                INSERT INTO model_deployments
                (model_version, accuracy, precision_score, recall_score, f1_score,
                 time_mae, severity_mae, cost_mae)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                metrics.get('model_version', 'unknown'),
                metrics.get('maintenance_accuracy', 0),
                metrics.get('maintenance_accuracy', 0),   # precision placeholder
                metrics.get('maintenance_accuracy', 0),   # recall placeholder
                metrics.get('maintenance_f1', 0),
                metrics.get('ttf_mae', 0),
                metrics.get('severity_mae', 0),
                metrics.get('cost_mae', 0),
            ))
        except Exception as e:
            logger.warning(f"Could not log deployment to DB: {e}")

    def get_deployment_history(self):
        """Fetch model version history from DB."""
        try:
            from utils.db_utils import db
            return db.fetch_dataframe("SELECT * FROM model_deployments ORDER BY deployed_at DESC LIMIT 10")
        except Exception:
            return pd.DataFrame()

    def get_status_summary(self):
        """Return a human-readable dict of retraining status."""
        last_trained = self._get_last_trained_date()
        days_since = (datetime.now() - last_trained).days
        new_samples = self._count_new_samples()
        _, drift_pct = self._detect_drift()
        needed, reason = self.should_retrain()
        return {
            'days_since_last_training': days_since,
            'last_trained': last_trained.strftime('%Y-%m-%d %H:%M'),
            'new_samples_since_train': new_samples,
            'drift_pct': drift_pct,
            'current_accuracy': self.current_metrics.get('maintenance_accuracy', 'N/A'),
            'retrain_needed': needed,
            'reason': reason,
        }
