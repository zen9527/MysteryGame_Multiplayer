import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.di import container

client = TestClient(app)


def test_health_check():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert "status" in data
    assert "checks" in data
    assert data["status"] in ["healthy", "unhealthy"]
    assert "llm" in data["checks"]
    assert "game_manager" in data["checks"]
    assert "database" in data["checks"]


def test_get_llm_config():
    resp = client.get("/api/llm-config")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "type" in data
    assert "model" in data


def test_list_providers():
    resp = client.get("/api/llm/providers")
    assert resp.status_code == 200
    data = resp.json()
    assert "providers" in data
    assert len(data["providers"]) >= 1
    # Default provider should be active
    default = next((p for p in data["providers"] if p["name"] == "default"), None)
    assert default is not None
    assert default["is_active"] is True


def test_add_provider():
    resp = client.post("/api/llm/providers", json={
        "name": "test-provider",
        "type": "openai",
        "endpoint": "http://localhost:12340",
        "model": "gpt-4",
        "api_key": "sk-test-key",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "added"
    assert data["name"] == "test-provider"

    # Verify it appears in list
    resp = client.get("/api/llm/providers")
    providers = resp.json()["providers"]
    assert any(p["name"] == "test-provider" for p in providers)


def test_set_active_provider():
    resp = client.post("/api/llm/providers/active", json={"name": "default"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "active"


def test_remove_provider():
    # First add a provider to remove
    client.post("/api/llm/providers", json={
        "name": "to-remove",
        "type": "openai",
        "endpoint": "http://localhost:12340",
        "model": "gpt-4",
        "api_key": "sk-test",
    })
    resp = client.delete("/api/llm/providers/to-remove")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "removed"

    # Verify removed
    resp = client.get("/api/llm/providers")
    providers = resp.json()["providers"]
    assert not any(p["name"] == "to-remove" for p in providers)


def test_remove_nonexistent():
    resp = client.delete("/api/llm/providers/nonexistent")
    assert resp.status_code == 404


def test_set_active_nonexistent():
    resp = client.post("/api/llm/providers/active", json={"name": "nonexistent"})
    assert resp.status_code == 404


def test_health_reflects_games_count():
    resp = client.post("/api/rooms", json={"creator_id": "health_test_admin"})
    assert resp.status_code == 200
    resp = client.get("/api/health")
    data = resp.json()
    assert "checks" in data
    assert "game_manager" in data["checks"]
    assert data["checks"]["game_manager"]["active_games"] >= 1
