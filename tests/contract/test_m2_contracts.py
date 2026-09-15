import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_artifact_crud_and_validation_contract():
    # 1. Create Session
    sess_res = client.post("/api/v1/sessions", json={"title": "Contract Test Session", "model": "llama3.1:8b"})
    assert sess_res.status_code == 201
    session_id = sess_res.json()["id"]

    # 2. Create Artifact
    art_payload = {
        "session_id": session_id,
        "title": "Testing Growth Loops",
        "content": "# Testing Growth Loops\n\n## The Core Idea\nLoops compound.\n\n## Pillar 1\nExecution [00:10:00].",
        "artifact_type": "essay",
        "metadata": {"guest": "Elena Verna"},
    }
    art_res = client.post("/api/v1/artifacts", json=art_payload)
    assert art_res.status_code == 201
    art_data = art_res.json()
    assert art_data["id"].startswith("art_")
    assert art_data["title"] == "Testing Growth Loops"
    assert art_data["word_count"] > 0
    assert "validation" in art_data["metadata"]

    artifact_id = art_data["id"]

    # 3. Retrieve Artifact by ID
    get_res = client.get(f"/api/v1/artifacts/{artifact_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == artifact_id

    # 4. Retrieve Raw HTML with Security Headers (CSP, isolation)
    raw_res = client.get(f"/api/v1/artifacts/{artifact_id}/raw")
    assert raw_res.status_code == 200
    assert "text/html" in raw_res.headers["content-type"]
    assert "Content-Security-Policy" in raw_res.headers
    assert "default-src 'none'" in raw_res.headers["Content-Security-Policy"]
    assert "X-Content-Type-Options" in raw_res.headers

    # 5. List Session Artifacts
    list_res = client.get(f"/api/v1/artifacts/session/{session_id}")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1


def test_chat_stream_out_of_domain_guardrail_contract():
    # Test that out-of-domain queries stream with guardrail response and completed event
    payload = {
        "message": "How do I bake sourdough bread?",
        "model": "llama3.1:8b",
        "provider": "ollama",
    }
    res = client.post("/api/v1/chat/stream", json=payload)
    assert res.status_code == 200
    assert "text/event-stream" in res.headers["content-type"]
    assert "X-Session-ID" in res.headers
    assert "X-Model" in res.headers

    # Read SSE events from body
    content = res.text
    assert "agent_started" in content
    assert "text_delta" in content
    assert "agent_completed" in content
    assert "Lenny's Podcast" in content
