from backend.agents.action_planner import ActionPlannerAgent as ActionPlanner

def test_prompt_builders_planned_vs_unplanned():
    planner = ActionPlanner()
    prompt = planner._build_user_prompt({"event_type": "planned", "event_cause": "construction"})
    assert "planned" in prompt.lower() or "pre-emptive" in prompt.lower()

async def test_no_key_path_yields_warning_sse():
    planner = ActionPlanner()
    planner.groq_key = None
    gen = planner.stream_plan({"event_type": "unplanned"})
    first = await gen.__anext__()
    assert "data:" in first

async def test_mocked_groq_stream_parses_delta_content_tokens(monkeypatch):
    planner = ActionPlanner()
    planner.groq_key = "dummy"
    def mock_post(*args, **kwargs):
        class MockResponse:
            def iter_lines(self):
                yield b'data: {"choices": [{"delta": {"content": "Deploy"}}]}'
                yield b'data: [DONE]'
            def raise_for_status(self): pass
            def __enter__(self): return self
            def __exit__(self, *args): pass
        return MockResponse()
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    gen = planner.stream_plan({"event_type": "unplanned"})
    lines = [line async for line in gen]
    assert any("Deploy" in line for line in lines)

async def test_mocked_failure_yields_warning_event(monkeypatch):
    planner = ActionPlanner()
    planner.groq_key = "dummy"
    def mock_post(*args, **kwargs):
        raise Exception("Stream error")
    import requests
    monkeypatch.setattr(requests, "post", mock_post)
    gen = planner.stream_plan({"event_type": "unplanned"})
    lines = [line async for line in gen]
    assert len(lines) > 0

def test_confidence_formatting():
    planner = ActionPlanner()
    prompt = planner._build_user_prompt({"confidence": 0.85})
    assert "85%" in prompt or "0.85" in prompt
