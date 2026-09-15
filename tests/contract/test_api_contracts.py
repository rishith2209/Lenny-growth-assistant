import pytest
from fastapi.testclient import TestClient
from apps.api.src.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Lenny Growth Assistant API"
    assert "X-Request-ID" in response.headers


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "providers" in data
    assert data["cost_profile"] == "100% Free / ₹0 spend"


def test_provider_health_endpoint():
    response = client.get("/health/providers")
    assert response.status_code == 200
    data = response.json()
    assert "providers" in data
    assert "ollama" in data["providers"]
    assert "anthropic" in data["providers"]


def test_knowledge_search_validation():
    # Empty query should fail validation (422)
    response = client.post("/api/v1/knowledge/search", json={"query": "a"})  # min_length is 2
    assert response.status_code == 422

    # Top_k out of bounds should fail validation
    response = client.post("/api/v1/knowledge/search", json={"query": "retention", "top_k": 50})  # le is 20
    assert response.status_code == 422


def test_request_id_header_propagation():
    custom_id = "req_custom_test_123"
    response = client.get("/", headers={"X-Request-ID": custom_id})
    assert response.headers["X-Request-ID"] == custom_id
