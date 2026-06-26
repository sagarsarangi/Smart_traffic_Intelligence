import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from backend.agents.anomaly_detector import TrafficAnomalyDetector as AnomalyDetector

@pytest.fixture(scope="module")
def loaded_detector():
    model_path = Path(__file__).parent.parent / "models" / "anomaly_detector.joblib"
    agent = AnomalyDetector(model_path=str(model_path))
    if model_path.exists():
        agent.load(str(model_path))
    return agent

def test_model_load_from_disk(loaded_detector):
    assert loaded_detector.model is not None

def test_baseline_stats_presence(loaded_detector):
    assert loaded_detector.baseline_stats is not None
    assert isinstance(loaded_detector.baseline_stats, pd.DataFrame)
    assert "zone_or_station" in loaded_detector.baseline_stats.columns

def test_overall_mean_duration_fallback(loaded_detector):
    assert isinstance(loaded_detector.overall_mean_duration, float)
    assert loaded_detector.overall_mean_duration > 0

def test_anomaly_scoring_decision_function(loaded_detector):
    X_live = np.array([[5.0, 0.8, 120.0]])
    scores = loaded_detector.model.decision_function(X_live)
    assert len(scores) == 1
    assert isinstance(float(scores[0]), float)

def test_file_not_found_for_missing_path():
    agent = AnomalyDetector(model_path="nonexistent.joblib")
    with pytest.raises(FileNotFoundError):
        agent.load("nonexistent.joblib")
