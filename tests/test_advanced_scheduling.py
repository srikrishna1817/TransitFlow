import pytest
import sys
import pandas as pd
from datetime import datetime

sys.path.append('..')

from scheduler.route_optimizer import assign_trains_to_routes
from scheduler.crew_scheduler import assign_crew_to_trains, check_crew_availability
from scheduler.scenario_analyzer import simulate_train_breakdown, forecast_fleet_availability
from scheduler.multi_day_planner import generate_weekly_schedule, detect_schedule_conflicts

def test_route_optimizer():
    """Test route assignment logic"""
    # dummy trains
    df = pd.DataFrame({"train_id": [f"TRN_{i}" for i in range(1, 61)]})
    routes_df = assign_trains_to_routes(df, datetime.now())
    counts = routes_df['assigned_route'].value_counts()
    assert counts.get('Red Line', 0) == 25
    assert counts.get('Blue Line', 0) == 23
    assert counts.get('Green Line', 0) == 12

def test_scenario_breakdown():
    """Test breakdown scenario simulation"""
    impact, _ = simulate_train_breakdown("TRN_005", "Ameerpet", "08:15", 2, None)
    assert impact["Gap Created"] == "120 mins"

def test_conflict_detection():
    """Test schedule validation"""
    conflicts = detect_schedule_conflicts(None)
    assert len(conflicts) > 0
    assert conflicts.iloc[0]['severity'] == 'Info'

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
