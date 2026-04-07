import sys
import os
import subprocess

def run_regression_tests():
    print("========== TRANSITFLOW REGRESSION TEST SUITE ==========\n")
    print("Executing standard automation suite 1A to ensure 1B fixes caused no regressions...")
    scripts = [
        "tests/comprehensive_test_suite.py",
        "tests/data_quality_report.py",
        "tests/performance_profiler.py"
    ]
    all_passed = True
    
    # Configure path explicitly to root folder
    env = os.environ.copy()
    env["PYTHONPATH"] = "."
    env["PYTHONIOENCODING"] = "utf-8"
    
    for s in scripts:
        print(f"\n--- Initializing {s} ---")
        try:
            res = subprocess.run([sys.executable, s], env=env, capture_output=True, text=True, encoding="utf-8")
            
            # Explicit failure detection (looking at exit codes and print signatures)
            if res.returncode != 0 or "Status: FAIL" in res.stdout or "[CRITICAL]" in res.stdout:
                print(res.stdout)
                print(f"❌ Regression failure detected inside {s}")
                if res.stderr:
                   print("STDER OUTPUT:", res.stderr)
                all_passed = False
            else:
                print(f"✅ Executed {s} successfully without regressions.")
        except Exception as e:
            print(f"Failed to execute test binary {s}: {e}")
            all_passed = False
            
    if all_passed:
        print("\n✅ REGRESSION SUITE: ALL TESTS PASSED. CODEBASE IS STABLE.")
    else:
        print("\n❌ REGRESSION SUITE: FAILURE. RECENT FIXES MAY HAVE INTRODUCED A REGRESSION.")

if __name__ == "__main__":
    run_regression_tests()
