from backend.utils.security import sanitize_url

def test_sanitize_url_redacts_key():
    url = "https://api.groq.com/v1/chat?key=secret123&other=val"
    redacted = sanitize_url(url)
    assert "secret123" not in redacted
    assert "%5BREDACTED%5D" in redacted

def test_leaves_others_intact():
    url = "https://api.groq.com/v1/chat?key=secret123&other=val"
    redacted = sanitize_url(url)
    assert "other=val" in redacted

def test_handles_malformed_input():
    url = "not a url"
    redacted = sanitize_url(url)
    assert redacted is not None
