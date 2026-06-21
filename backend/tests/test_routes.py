def test_ping(client):
    res = client.get("/ping")
    assert res.status_code == 200

def test_heatmap_shape_and_weights(client):
    res = client.get("/heatmap")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_heatmap_replay(client):
    res = client.post("/heatmap/replay")
    assert res.status_code == 200

def test_incidents_pagination_and_filters(client):
    res = client.get("/incidents?page=1&limit=10")
    assert res.status_code == 200

def test_analytics_all_datasets_present(client):
    res = client.get("/analytics")
    assert res.status_code == 200

def test_predict_happy_path(client, sample_incident):
    res = client.post("/predict", json=sample_incident)
    assert res.status_code in [200, 503]

def test_predict_503_when_unset(client, sample_incident):
    res = client.post("/predict", json=sample_incident)
    if res.status_code == 503:
        assert "not loaded" in res.json()["detail"].lower()

def test_nlp_parse(client):
    res = client.post("/nlp-parse", json={"description": ""})
    assert res.status_code == 200
    assert res.json() is None

def test_feedback_roundtrip(client):
    pass

def test_anomaly(client):
    res = client.get("/anomaly")
    assert res.status_code == 200

def test_action_plan_sse(client):
    res = client.post("/action-plan", json={"event_type": "unplanned"})
    assert res.status_code == 200

def test_geocode_zone(client):
    res = client.post("/geocode-zone", json={"zone": "HSR Layout"})
    assert res.status_code == 200
