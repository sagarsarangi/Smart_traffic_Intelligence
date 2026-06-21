"""
Shared pytest fixtures and configuration for the backend test suite.

Design notes
------------
- The FastAPI app (``backend.main:app``) is imported ONCE at collection time.
  Importing it triggers the ``@app.on_event("startup")`` machinery only when a
  live ASGI client is used; the underlying dataset + committed ``.joblib``
  models are real artifacts already present in the repo, so no training is
  required for tests.
- Every external network call (Groq API,  LocationIQ) is blocked
  at the ``requests`` layer by the ``block_network`` autouse fixture. Route
  tests that exercise the LLM/geocoding paths monkeypatch the specific call
  sites, so a real key or network connection is never needed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# ---------------------------------------------------------------------------
# Ensure the project root (parent of backend/) is on sys.path so that the
# `backend.*` import style used throughout the codebase resolves under pytest.
# ---------------------------------------------------------------------------
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# Tests must never hit a real external API. Strip any locally-configured key
# BEFORE the app is imported so agents initialise in their "no key" state,
# then individual tests can opt back in via monkeypatch where needed.
os.environ["GROQ_API_KEY"] = "dummy-groq-key-for-tests"
os.environ["LOCATIONIQ_API_KEY"] = "dummy-locationiq-key-for-tests"

import requests  # noqa: E402  (after sys.path manipulation)


# ---------------------------------------------------------------------------
# Autouse: hard-block all outbound HTTP at the requests layer.
# A test that legitimately needs a fake response monkeypatches the call site
# itself, so this is purely a safety net against accidental live calls.
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Session-scoped: load the dataset + caches ONCE before any test runs.
# The data loader is module-level global state that the FastAPI startup event
# normally populates. Tests that touch loader caches directly need it primed,
# and the route tests import the same module — so we prime it up front for the
# whole session (idempotent inside load_dataset()).
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def _prime_dataset():
    from backend.data.loader import load_dataset
    load_dataset()
    yield


@pytest.fixture(autouse=True)
def block_network(monkeypatch):
    def _blocked(*args, **kwargs):
        raise RuntimeError(
            "Network call blocked in tests. Monkeypatch the specific "
            "requests.post / requests.get call site instead."
        )
    monkeypatch.setattr(requests, "post", _blocked)
    monkeypatch.setattr(requests, "get", _blocked)
    yield


# ---------------------------------------------------------------------------
# FastAPI app + async HTTP client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """Import the real FastAPI application once per session."""
    from backend.main import app as fastapi_app
    return fastapi_app


@pytest.fixture()
def client(app):
    """
    A synchronous Starlette ``TestClient``. Preferred for route tests because
    it transparently runs startup/shutdown events (loading the dataset,
    starting background replay loops) and supports SSE streaming reads.
    """
    from starlette.testclient import TestClient
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# Data factories
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_incident() -> Dict[str, Any]:
    """
    A realistic incident dict matching PredictRequest fields — safe defaults
    for every optional field so PredictionAgent has a complete feature vector.
    """
    return {
        "event_type": "unplanned",
        "event_cause": "vehicle_breakdown",
        "veh_type": "bmtc_bus",
        "requires_road_closure": False,
        "start_datetime": "2025-06-15T08:30:00",
        "zone": "HSR Layout",
        "junction": "Silk Board",
        "corridor": "ORR East 1",
        "planned_duration_minutes": None,
        "lat": 12.9352,
        "lng": 77.6245,
        "address": "Silk Board Junction, Bengaluru",
        "police_station": "HSR Layout PS",
    }


@pytest.fixture()
def planned_incident() -> Dict[str, Any]:
    """A planned-event variant for testing the event_type binary feature."""
    return {
        "event_type": "planned",
        "event_cause": "public_event",
        "veh_type": None,
        "requires_road_closure": True,
        "start_datetime": "2025-06-15T18:00:00",
        "end_datetime": "2025-06-15T23:00:00",
        "zone": "MG Road",
        "junction": "Trinity Circle",
        "corridor": "MG Road",
        "planned_duration_minutes": 300.0,
        "lat": 12.9756,
        "lng": 77.6066,
        "address": "MG Road, Bengaluru",
        "police_station": "Ashok Nagar PS",
    }


# ---------------------------------------------------------------------------
# Convenience: explicitly re-grant a fake Groq key for tests that exercise the
# "key present but API call mocked" code path.
# ---------------------------------------------------------------------------

@pytest.fixture()
def fake_groq_key(monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-key-not-real")
    yield
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
