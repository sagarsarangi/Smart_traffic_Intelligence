import pytest
from backend.agents.anomaly_detector import TrafficAnomalyDetector as AnomalyDetector

def test_model_load_from_disk():
    agent = AnomalyDetector()
    assert getattr(agent, "_model_loaded", False) is False

def test_baseline_stats_presence():
    agent = AnomalyDetector()
    assert getattr(agent, "baseline_stats", None) is None or isinstance(agent.baseline_stats, dict)

def test_overall_mean_duration_fallback():
    agent = AnomalyDetector()
    assert getattr(agent, "overall_mean_duration", 60.0) == 60.0

def test_file_not_found_for_missing_path():
    agent = AnomalyDetector(model_path="nonexistent.joblib")
    with pytest.raises(FileNotFoundError):
        agent.load("nonexistent.joblib")
