import pytest
from backend.agents.prediction_agent import PredictionAgent
import numpy as np

def test_predict_incident_returns_correct_types(sample_incident):
    agent = PredictionAgent()
    agent._models_loaded = True
    
    agent.build_feature_vector = lambda x: np.zeros(12)
    agent.predict_priority = lambda x: {"priority": "High", "confidence": 0.85}
    agent.predict_duration = lambda x: 45
    
    result = agent.predict_incident(sample_incident)
    assert "priority" in result
    assert "confidence" in result
    assert "estimated_duration_minutes" in result
    assert "estimated_resolution_time" in result
    assert isinstance(result["confidence"], float)

def test_confidence_in_bounds(sample_incident):
    agent = PredictionAgent()
    agent._models_loaded = True
    agent.build_feature_vector = lambda x: np.zeros(12)
    agent.predict_priority = lambda x: {"priority": "High", "confidence": 0.85}
    agent.predict_duration = lambda x: 45
    result = agent.predict_incident(sample_incident)
    assert 0.0 <= result["confidence"] <= 1.0

def test_duration_greater_than_one(sample_incident):
    agent = PredictionAgent()
    agent._models_loaded = True
    agent.build_feature_vector = lambda x: np.zeros(12)
    agent.predict_priority = lambda x: {"priority": "High", "confidence": 0.85}
    agent.predict_duration = lambda x: 45
    result = agent.predict_incident(sample_incident)
    assert result["estimated_duration_minutes"] >= 1

def test_runtime_error_when_models_not_loaded(sample_incident):
    agent = PredictionAgent()
    agent._models_loaded = False
    with pytest.raises(RuntimeError):
        agent.predict_incident(sample_incident)
