from backend.agents.feature_engineering import build_feature_vector
import pandas as pd
import numpy as np

class MockLE:
    classes_ = ["HSR Layout", "unknown"]
    def transform(self, x):
        return [0]

def test_build_feature_vector_12_column_order(sample_incident):
    encoders = {"zone": MockLE(), "event_cause": MockLE(), "veh_type": MockLE()}
    junction_lookup = {"Silk Board": 5}
    df = build_feature_vector(sample_incident, encoders, junction_lookup)
    
    expected_cols = [
        "event_type", "latitude", "longitude", "requires_road_closure", 
        "priority", "status", "corridor", "zone", "junction", "resolution_minutes", 
        "planned_duration_minutes", "hour_of_day", "day_of_week", "is_peak_hour", 
        "is_weekend", "corridor_rank", "junction_recurrence", 
        "event_cause_enc", "veh_type_enc", "zone_enc"
    ]
    assert list(df.columns) == expected_cols

def test_peak_hour_window_correctness(sample_incident):
    sample_incident["start_datetime"] = "2025-06-15T08:30:00" # Peak hour
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["is_peak_hour"] == 1
    
    sample_incident["start_datetime"] = "2025-06-15T12:30:00" # Non-peak
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["is_peak_hour"] == 0

def test_weekend_logic(sample_incident):
    sample_incident["start_datetime"] = "2025-06-14T08:30:00"
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["is_weekend"] == 1
    
    sample_incident["start_datetime"] = "2025-06-16T08:30:00"
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["is_weekend"] == 0

def test_planned_duration_null_for_unplanned(sample_incident):
    sample_incident["event_type"] = "unplanned"
    sample_incident["end_datetime"] = "2025-06-15T10:30:00"
    df = build_feature_vector(sample_incident, {}, {})
    assert np.isnan(df.iloc[0]["planned_duration_minutes"])

def test_unseen_label_to_minus_one(sample_incident):
    sample_incident["zone"] = "Unknown Zone"
    encoders = {"zone": MockLE()}
    df = build_feature_vector(sample_incident, encoders, {})
    assert df.iloc[0]["zone_enc"] == -1

def test_junction_recurrence_default_1(sample_incident):
    sample_incident["junction"] = "New Junction"
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["junction_recurrence"] == 1

def test_corridor_rank_mapping(sample_incident):
    sample_incident["corridor_rank"] = 2
    df = build_feature_vector(sample_incident, {}, {})
    assert df.iloc[0]["corridor_rank"] == 2
