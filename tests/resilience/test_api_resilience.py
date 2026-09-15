import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_invalid_session_id_404():
    """Verify requesting a non-existent session returns structured 404."""
    res = client.get("/api/v1/sessions/non_existent_session_999999")
    assert res.status_code == 404
    data = res.json()
    assert "detail" in data or "message" in data


def test_invalid_artifact_id_404():
    """Verify requesting a non-existent artifact returns structured 404."""
    res = client.get("/api/v1/artifacts/art_nonexistent_12345")
    assert res.status_code == 404


def test_malformed_search_payload_validation():
    """Verify malformed search queries return 422 with structured validation errors."""
    # Missing query field
    res = client.post("/api/v1/knowledge/search", json={})
    assert res.status_code == 422
    assert "detail" in res.json()

    # Query too short (< 2 chars)
    res = client.post("/api/v1/knowledge/search", json={"query": "x"})
    assert res.status_code == 422


def test_malformed_chat_payload_validation():
    """Verify malformed chat requests return 422."""
    res = client.post("/api/v1/chat/stream", json={"session_id": "test"})
    assert res.status_code == 422


def test_health_providers_always_structured():
    """Verify health endpoint always returns structured provider availability matrix."""
    res = client.get("/health/providers")
    assert res.status_code == 200
    data = res.json()
    assert "primary_provider" in data
    assert "providers" in data
    assert "ollama" in data["providers"]
    assert "anthropic" in data["providers"]
    assert isinstance(data["providers"]["ollama"]["models_available"], list)
