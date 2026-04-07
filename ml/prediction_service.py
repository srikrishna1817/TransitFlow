"""
Real-Time Prediction Service for TransitFlow HMRL.
Orchestrates feature engineering → prediction → explanation → DB logging.
"""
import logging
from datetime import datetime
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class PredictionService:
    """
    High-level service: given a train_id, return a full risk prediction dict.
    """

    def __init__(self):
        self._predictor = None
        self._explainer = None
        self._feature_engineer = None
        self._feature_cache = {}   # train_id → feature dict

    def _ensure_ready(self):
        """Lazy-load all ML components."""
        if self._predictor is None:
            from ml.advanced_predictor import AdvancedMaintenancePredictor
            self._predictor = AdvancedMaintenancePredictor()
            self._predictor._load()
            if self._predictor.clf_maintenance is None:
                logger.info("No pre-trained model found. Training now...")
                self._predictor.train()

        if self._feature_engineer is None:
            from ml.feature_engineer import FeatureEngineer
            self._feature_engineer = FeatureEngineer()

        if self._explainer is None:
            from ml.model_explainer import ModelExplainer
            self._explainer = ModelExplainer(self._predictor)

    def _get_feature_row(self, train_id):
        if train_id in self._feature_cache:
            return self._feature_cache[train_id]
        all_features = self._feature_engineer.create_all_features(train_ids=[train_id])
        if all_features.empty:
            return {}
        row = all_features.iloc[0].to_dict()
        self._feature_cache[train_id] = row
        return row

    def predict_single_train(self, train_id):
        """
        Full prediction for one train.
        Returns: enriched dict with train_id, risk, explanation.
        """
        self._ensure_ready()
        try:
            feature_row = self._get_feature_row(train_id)
            prediction = self._predictor.predict(feature_row)
            explanation = self._explainer.explain_prediction(feature_row)

            result = {
                'train_id': train_id,
                **prediction,
                'explanation': [
                    {'feature': e[0], 'value': round(float(e[1]), 2), 'impact': round(float(e[2]), 4)}
                    for e in explanation
                ],
                'predicted_at': datetime.now().isoformat(),
            }

            # Formatted recommendation
            result['recommendation'] = self._build_recommendation(result)

            # Log to DB
            self._log_prediction(result)
            return result

        except Exception as e:
            logger.error(f"predict_single_train({train_id}) failed: {e}")
            return {
                'train_id': train_id,
                'maintenance_required': False,
                'maintenance_probability': 0,
                'failure_type': 'Unknown',
                'time_to_failure_days': 90,
                'severity_score': 0,
                'estimated_cost_inr': 0,
                'risk_level': 'LOW',
                'explanation': [],
                'recommendation': 'Could not generate prediction. Check model status.',
                'predicted_at': datetime.now().isoformat(),
            }

    def predict_all_fleet(self, train_ids=None):
        """
        Predict for all 60 trains (or a given list).
        Returns: pd.DataFrame with one row per train.
        """
        self._ensure_ready()

        if train_ids is None:
            try:
                from utils.data_loader import load_trains_data
                trains = load_trains_data()
                id_col = 'train_id' if 'train_id' in trains.columns else 'Train_ID'
                train_ids = trains[id_col].tolist()
            except Exception:
                train_ids = [f"HMRL-{i+1:02d}" for i in range(60)]

        # Bulk feature engineering
        try:
            all_features = self._feature_engineer.create_all_features(train_ids=train_ids)
            self._feature_cache = {row['train_id']: row for row in all_features.to_dict('records')}
        except Exception as e:
            logger.warning(f"Bulk feature engineering failed: {e}")

        results = []
        for tid in train_ids:
            r = self.predict_single_train(tid)
            results.append({
                'train_id': r['train_id'],
                'risk_level': r['risk_level'],
                'maintenance_probability': r['maintenance_probability'],
                'maintenance_required': r['maintenance_required'],
                'failure_type': r['failure_type'],
                'time_to_failure_days': r['time_to_failure_days'],
                'severity_score': r['severity_score'],
                'estimated_cost_inr': r['estimated_cost_inr'],
                'recommendation': r.get('recommendation', ''),
            })

        return pd.DataFrame(results)

    def _build_recommendation(self, result):
        risk = result['risk_level']
        ft = result['failure_type']
        ttf = result['time_to_failure_days']
        cost = result['estimated_cost_inr']

        if risk == 'CRITICAL':
            return f"🚨 IMMEDIATE ACTION: Ground train and schedule {ft} repair within 24h. Estimated cost ₹{cost:,}."
        elif risk == 'HIGH':
            return f"⚠ HIGH PRIORITY: Schedule {ft} inspection within {ttf} days. Estimated cost ₹{cost:,}."
        elif risk == 'MEDIUM':
            return f"🟡 MONITOR: Plan {ft} maintenance in next {ttf} days during off-peak window."
        else:
            return f"✅ NOMINAL: Train in good health. Next check recommended in {ttf} days."

    def _log_prediction(self, result):
        """Write prediction to ml_predictions table."""
        try:
            from utils.db_utils import db
            db.execute("""
                INSERT INTO ml_predictions
                (train_id, prediction_date, maintenance_probability,
                 maintenance_required, failure_type, time_to_failure_days,
                 severity_score, risk_level, model_version)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                result['train_id'],
                result['predicted_at'][:10],
                result['maintenance_probability'],
                int(result['maintenance_required']),
                result['failure_type'],
                result['time_to_failure_days'],
                result['severity_score'],
                result['risk_level'],
                getattr(self._predictor, 'model_version', 'unknown'),
            ))
        except Exception as e:
            logger.debug(f"DB log skipped: {e}")
