import sys
import os
import time
import psutil
from datetime import datetime
import pandas as pd
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_utils import db
from ml.advanced_predictor import AdvancedMaintenancePredictor
from scheduler import generate_schedule
from utils.report_generator import ReportGenerator

def measure_execution(name, func, *args, **kwargs):
    start = time.time()
    try:
        func(*args, **kwargs)
        end = time.time()
        dur = end - start
        print(f"[Profiling] {name} completed in {dur:.3f} seconds.")
        return dur
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[Profiling Error] {name} failed: {e}")
        return float('inf')

def run_performance_profile():
    print("========== TRANSITFLOW PERFORMANCE PROFILER ==========\n")
    
    # 1. DB Fetch
    t1 = measure_execution("DB Query (Fetch rows)", db.fetch_dataframe, "SELECT * FROM trains_master LIMIT 500")

    # 2. ML Inference (Mocking 60 trains)
    model = AdvancedMaintenancePredictor()
    model.train() # Fast mock train
    query = "SELECT kilometers_run, days_since_last_service, current_health_score, avg_temp_c, door_cycles, brake_wear_mm FROM trains_master LIMIT 60"
    dummy_df = db.fetch_dataframe(query)
    if dummy_df is None or len(dummy_df) < 60:
        # Pad with mock data if not enough trains in DB
        import numpy as np
        needed = 60 if dummy_df is None else 60 - len(dummy_df)
        mock_df = pd.DataFrame({
            'kilometers_run': np.random.randint(50000, 150000, needed),
            'days_since_last_service': np.random.randint(10, 90, needed),
            'current_health_score': np.random.randint(60, 95, needed),
            'avg_temp_c': np.random.randint(25, 45, needed),
            'door_cycles': np.random.randint(500, 10000, needed),
            'brake_wear_mm': np.random.uniform(5.0, 15.0, needed)
        })
        if dummy_df is not None:
            dummy_df = pd.concat([dummy_df, mock_df], ignore_index=True)
        else:
            dummy_df = mock_df
            
    t2 = measure_execution("ML Prediction (60 Trains)", model.predict, dummy_df)
    
    # 3. Scheduling
    t3 = measure_execution("Generate 60 Train Schedule", generate_schedule, 60, False)
    
    # 4. Report Generation
    rg = ReportGenerator(user_id=1)
    today = datetime.now()
    t4 = measure_execution("Generate Daily Ops PDF Report", rg.generate_daily_operations_report, today)

    # 5. Memory Usage
    process = psutil.Process(os.getpid())
    mem_mb = process.memory_info().rss / (1024 * 1024)
    print(f"\n[Memory Profiling] Current memory consumption: {mem_mb:.2f} MB")

    print("\n--- Benchmark Evaluation ---")
    if t2 < 10.0:
        print("[PASS] ML Evaluation: Passed (< 10s)")
    else:
        print("[FAIL] ML Evaluation: Failed (> 10s)")
        
    if t4 < 15.0:
        print("[PASS] Report Generation: Passed (< 15s)")
    else:
        print("[FAIL] Report Generation: Failed (> 15s)")

if __name__ == "__main__":
    run_performance_profile()
