def test_app_metadata(app):
    assert hasattr(app, "title")
    assert hasattr(app, "version")

def test_cors_middleware(app):
    assert any(m.cls.__name__ == "CORSMiddleware" for m in app.user_middleware)

def test_all_routers_mounted(app):
    pass

def test_docs_reachable(client):
    response = client.get("/docs")
    assert response.status_code == 200
