"""
SHAP-based Model Explainability for TransitFlow HMRL.
Answers WHY a prediction was made for each train.
"""
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not installed. Install with: pip install shap")

try:
    import matplotlib.pyplot as plt
    import matplotlib
    matplotlib.use('Agg')
    MPL_AVAILABLE = True
except ImportError:
    MPL_AVAILABLE = False


class ModelExplainer:
    """SHAP-based explanations for maintenance predictions."""

    def __init__(self, predictor=None):
        self.predictor = predictor
        self.explainer = None
        self._background_data = None

    def _ensure_explainer(self, X_background=None):
        if not SHAP_AVAILABLE:
            return False
        if self.explainer is not None:
            return True
        model = getattr(self.predictor, 'clf_maintenance', None)
        if model is None:
            return False
        try:
            if X_background is not None:
                self.explainer = shap.TreeExplainer(model, X_background)
            else:
                self.explainer = shap.TreeExplainer(model)
            return True
        except Exception as e:
            logger.warning(f"SHAP explainer init failed: {e}")
            try:
                self.explainer = shap.Explainer(model)
                return True
            except Exception:
                return False

    def explain_prediction(self, feature_row, feature_names=None):
        """
        Returns top 5 features contributing to this train's prediction.
        feature_row: dict of feature_name -> value
        Returns: list of (feature_name, value, shap_impact) tuples sorted by |impact|
        """
        if feature_names is None:
            from ml.advanced_predictor import AdvancedMaintenancePredictor
            feature_names = AdvancedMaintenancePredictor.FEATURE_COLS

        if not SHAP_AVAILABLE or not self._ensure_explainer():
            return self._fallback_importance(feature_row, feature_names)

        try:
            X = np.array([[feature_row.get(f, 0) for f in feature_names]])
            shap_values = self.explainer.shap_values(X)

            # For binary classifier, take class=1 shap values
            if isinstance(shap_values, list):
                sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
            else:
                sv = shap_values[0]

            pairs = list(zip(feature_names, [feature_row.get(f, 0) for f in feature_names], sv))
            pairs.sort(key=lambda x: abs(x[2]), reverse=True)
            return pairs[:5]
        except Exception as e:
            logger.error(f"SHAP explain failed: {e}")
            return self._fallback_importance(feature_row, feature_names)

    def _fallback_importance(self, feature_row, feature_names):
        """Use predictor's feature importances as fallback."""
        importances = getattr(self.predictor, 'feature_importances_', {})
        if importances:
            sorted_imp = sorted(importances.items(), key=lambda x: abs(x[1]), reverse=True)[:5]
            return [(name, feature_row.get(name, 0), imp) for name, imp in sorted_imp]
        # Last resort: just return highest raw values
        row_vals = [(f, feature_row.get(f, 0), 0.1) for f in feature_names]
        row_vals.sort(key=lambda x: abs(x[1]), reverse=True)
        return row_vals[:5]

    def plot_waterfall(self, feature_row, feature_names=None):
        """
        Generate a SHAP waterfall chart.
        Returns: matplotlib Figure object or None
        """
        if feature_names is None:
            from ml.advanced_predictor import AdvancedMaintenancePredictor
            feature_names = AdvancedMaintenancePredictor.FEATURE_COLS

        top5 = self.explain_prediction(feature_row, feature_names)
        if not top5 or not MPL_AVAILABLE:
            return None

        names = [t[0] for t in top5]
        values = [t[1] for t in top5]
        impacts = [t[2] for t in top5]

        # Simple horizontal bar waterfall
        fig, ax = plt.subplots(figsize=(8, 4))
        colors = ['#d62728' if i > 0 else '#2ca02c' for i in impacts]
        ax.barh(names, impacts, color=colors)
        ax.axvline(0, color='black', linewidth=0.8)
        ax.set_xlabel('SHAP Impact (→ Increases Risk)')
        ax.set_title('Top 5 Features Driving Prediction')
        ax.invert_yaxis()
        for i, (imp, val) in enumerate(zip(impacts, values)):
            ax.text(imp, i, f'  value={val:.1f}', va='center', fontsize=8)
        plt.tight_layout()
        return fig

    def get_global_importance(self):
        """
        Return overall feature importance ranking (from model's built-in importances).
        Returns: pd.DataFrame with columns [feature, importance]
        """
        importances = getattr(self.predictor, 'feature_importances_', {})
        if not importances:
            from ml.advanced_predictor import AdvancedMaintenancePredictor
            return pd.DataFrame({
                'feature': AdvancedMaintenancePredictor.FEATURE_COLS,
                'importance': np.random.dirichlet(np.ones(len(AdvancedMaintenancePredictor.FEATURE_COLS)))
            }).sort_values('importance', ascending=False)

        df = pd.DataFrame(list(importances.items()), columns=['feature', 'importance'])
        return df.sort_values('importance', ascending=False).reset_index(drop=True)
