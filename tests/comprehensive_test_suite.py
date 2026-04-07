import sys
import os
import datetime
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.db_utils import db
from auth.authenticator import hash_password, check_password
from ml.advanced_predictor import AdvancedMaintenancePredictor
from scheduler import generate_schedule
from utils.report_generator import ReportGenerator

class TestRunner:
    def __init__(self):
        self.failures = 0
        self.passed = 0

    def assert_test(self, name, condition, error_msg=""):
        if condition:
            print(f"  [PASS] {name}")
            self.passed += 1
        else:
            print(f"  [FAIL] {name} - {error_msg}")
            self.failures += 1

    def run_tests(self):
        print(f"========== TRANSITFLOW AUTOMATED TEST SUITE ==========\n")
        self.test_database()
        self.test_authentication()
        self.test_ml_model()
        self.test_scheduling()
        self.test_reports()
        
        print("\n================== TEST SUMMARY ==================")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failures}")
        print("Status: " + ("PASS" if self.failures == 0 else "FAIL"))
        sys.exit(0 if self.failures == 0 else 1)

    def test_database(self):
        print("\n--- Testing Database Connectivity ---")
        tables = [
            "users", "user_activity_log", "trains_master", "historical_operations",
            "maintenance_jobs", "ml_predictions", "schedule_master", "maintenance_schedule",
            "alerts", "crew_master", "crew_assignments", "report_history", "scheduled_reports"
        ]
        for tbl in tables:
            try:
                db.execute_query(f"SELECT 1 FROM {tbl} LIMIT 1")
                self.assert_test(f"Table Access: {tbl}", True)
            except Exception as e:
                self.assert_test(f"Table Access: {tbl}", False, str(e))

    def test_authentication(self):
        print("\n--- Testing Authentication System ---")
        try:
            pw = "securepass123"
            h = hash_password(pw)
            self.assert_test("Password Hashing", check_password(pw, h))
            self.assert_test("Invalid Password Rejection", not check_password("wrong", h))
        except Exception as e:
            self.assert_test("Auth Mechanics", False, str(e))

    def test_ml_model(self):
        print("\n--- Testing ML Predictive Model ---")
        try:
            model = AdvancedMaintenancePredictor()
            metrics = model.train()
            self.assert_test("ML Model Training Cycle", metrics is not None)
            
            # Prediction on synthetic dict row
            test_row = {
                'kilometers_run': 120000,
                'days_since_last_service': 45,
                'current_health_score': 65,
                'avg_temp_c': 35,
                'door_cycles': 8000,
                'brake_wear_mm': 12.0
            }
            preds = model.predict(test_row)
            self.assert_test("ML Probability Output Valid", 'maintenance_probability' in preds)
            self.assert_test("ML Failure Type Predicted", 'failure_type' in preds)
        except Exception as e:
            self.assert_test("ML Model Execution", False, str(e))

    def test_scheduling(self):
        print("\n--- Testing Scheduling Engine ---")
        try:
            sch, alerts = generate_schedule(required_service_trains=60, save_to_db=False)
            
            self.assert_test("Scheduler Generates Output", not sch.empty)
            self.assert_test("Service Assignments Processed", "SERVICE" in sch['Assignment'].values)
            self.assert_test("Standby Optimization Engine", "STANDBY" in sch['Assignment'].values or "MAINTENANCE" in sch['Assignment'].values)
        except Exception as e:
            self.assert_test("Scheduling Execution", False, str(e))

    def test_reports(self):
        print("\n--- Testing Automated Reporting Engine ---")
        try:
            rg = ReportGenerator(user_id=1)
            today = datetime.date.today()
            f1 = rg.generate_daily_operations_report(today)
            f2 = rg.generate_fleet_health_report(today - datetime.timedelta(days=30), today)
            
            self.assert_test("Daily Operations Report Generated", os.path.exists(f1))
            self.assert_test("Fleet Health Report Generated", os.path.exists(f2))
        except Exception as e:
            self.assert_test("Report Generation", False, str(e))

if __name__ == "__main__":
    runner = TestRunner()
    runner.run_tests()
