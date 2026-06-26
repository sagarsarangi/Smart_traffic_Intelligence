def test_app_metadata(app):
    assert hasattr(app, "title")
    assert hasattr(app, "version")

def test_cors_middleware(app):
    assert any(m.cls.__name__ == "CORSMiddleware" for m in app.user_middleware)

def test_all_routers_mounted(client):
    """Verify critical API routes are mounted by checking they don't return 404.

    Inspecting ``app.routes`` directly is unreliable in CI: pytest-cov's import
    hook (activated by ``--cov=backend``) can interfere with namespace-package
    resolution and cause router objects to appear empty before
    ``app.include_router(...)`` runs. Using the TestClient is the only approach
    that is stable across all import environments.

    A 404 means the route is not registered; 200 / 422 / 503 all confirm it
    exists (even if the request body is incomplete or an agent is not ready).
    """
    # GET routes
    for path in ["/heatmap", "/anomaly"]:
        resp = client.get(path)
        assert resp.status_code != 404, (
            f"Route GET {path} is not mounted (got 404). "
            "Check that the router is included in main.py."
        )

    # POST routes — empty body is intentional; we only care the route exists
    for path in ["/predict", "/action-plan", "/feedback"]:
        resp = client.post(path, json={})
        assert resp.status_code != 404, (
            f"Route POST {path} is not mounted (got 404). "
            "Check that the router is included in main.py."
        )

def test_docs_reachable(client):
    response = client.get("/docs")
    assert response.status_code == 200
