from backend.agents.nlp_parser import NLPIncidentParser as NLPParser

def test_heuristic_fallback_keyword_maps():
    parser = NLPParser()
    res = parser.parse_with_heuristics("accident on the road")
    assert res["root_cause"] == "accident"

def test_empty_description_returns_none():
    parser = NLPParser()
    assert parser.parse_description("") is None

def test_no_api_key_returns_none(fake_groq_key):
    parser = NLPParser()
    parser.groq_key = None
    res = parser.parse_description("test")
    assert res is None

def test_unknown_model_fallback():
    parser = NLPParser()
    res = parser.parse_description("test", model_name="unknown-model")
    assert res is None

def test_mocked_groq_happy_path_returns_parsed_json(monkeypatch):
    parser = NLPParser()
    parser.groq_key = "dummy"
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
            def json(self):
                return {"choices": [{"message": {"content": '{"root_cause":"accident"}'}}]}
        return MockResponse()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    res = parser.parse_description("accident")
    assert res["root_cause"] == "accident"

def test_mocked_http_error_returns_none(monkeypatch):
    parser = NLPParser()
    parser.groq_key = "dummy"
    def mock_post(*args, **kwargs):
        import requests
        class MockResponse:
            status_code = 500
            reason = "Server Error"
            def raise_for_status(self):
                raise requests.exceptions.HTTPError("HTTP Error", response=self, request=requests.Request('POST', 'http://url'))
        return MockResponse()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    res = parser.parse_description("test")
    assert res is None

def test_mocked_null_literal_response_returns_none(monkeypatch):
    parser = NLPParser()
    parser.groq_key = "dummy"
    def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def raise_for_status(self): pass
            def json(self):
                return {"choices": [{"message": {"content": 'null'}}]}
        return MockResponse()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    res = parser.parse_description("test")
    assert res is None
