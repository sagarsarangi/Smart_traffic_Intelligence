import pytest
from pathlib import Path
from backend.agents.prediction_agent import PredictionAgent

@pytest.fixture(scope="module")
def loaded_agent():
    base_dir = Path(__file__).parent.parent
    agent = PredictionAgent(
        classifier_path=str(base_dir / "models/priority_model.joblib"),
        regressor_path=str(base_dir / "models/duration_model.joblib"),
        junction_lookup_path=str(base_dir / "models/junction_lookup.joblib"),
        zone_encoder_path=str(base_dir / "models/encoders.joblib"),
    )
    agent.load_models()
    return agent

def test_predict_incident_returns_correct_types(loaded_agent, sample_incident):
    result = loaded_agent.predict_incident(sample_incident)
    assert "priority" in result
    assert "confidence" in result
    assert "estimated_duration_minutes" in result
    assert "estimated_resolution_time" in result
    assert result["priority"] in ["High", "Low"]
    assert isinstance(result["confidence"], float)

def test_confidence_in_bounds(loaded_agent, sample_incident):
    result = loaded_agent.predict_incident(sample_incident)
    assert 0.0 <= result["confidence"] <= 1.0

def test_duration_greater_than_one(loaded_agent, sample_incident):
    result = loaded_agent.predict_incident(sample_incident)
    assert result["estimated_duration_minutes"] >= 1

def test_runtime_error_when_models_not_loaded(sample_incident):
    agent = PredictionAgent()
    agent._models_loaded = False
    with pytest.raises(RuntimeError):
        agent.predict_incident(sample_incident)
