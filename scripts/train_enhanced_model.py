"""
Train the enhanced multi-output ML model.
Run from project root: python scripts/train_enhanced_model.py
"""
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s  %(levelname)s  %(message)s')

from ml.feature_engineer import FeatureEngineer
from ml.advanced_predictor import AdvancedMaintenancePredictor

def main():
    print("=" * 60)
    print("  TransitFlow HMRL -- Enhanced ML Model Training")
    print("=" * 60)

    print("\n[1/3] Engineering features for all 60 trains...")
    fe = FeatureEngineer()
    feature_df = fe.create_all_features()
    print(f"  Features created: {feature_df.shape[1]-1} features x {len(feature_df)} trains")

    print("\n[2/3] Training multi-output model (3000-sample augmented dataset)...")
    predictor = AdvancedMaintenancePredictor()
    metrics = predictor.train(feature_df)

    print("\n[3/3] Results:")
    for k, v in metrics.items():
        print(f"  {k}: {v}")

    print(f"\n[OK] Model saved -> models/maintenance_predictor_{metrics['model_version']}.pkl")
    print("[OK] Latest copy -> models/maintenance_predictor_advanced.pkl")

if __name__ == "__main__":
    main()
