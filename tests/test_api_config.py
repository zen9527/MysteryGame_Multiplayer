import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.di import container

client = TestClient(app)


def _get_host_dm():
    return container.resolve("host_dm")


def _get_manager():
    return container.resolve("game_manager")


def test_health_check():
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "games_count" in data


def test_get_llm_config():
    resp = client.get("/llm-config")
    assert resp.status_code == 200
    data = resp.json()
    assert "endpoint" in data
    assert "model" in data
    assert "api_key_set" in data


def test_update_llm_config():
    resp = client.post("/llm-config", json={
        "endpoint": "http://localhost:11434/v1",
        "model": "test-model",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "updated"
    assert data["model"] == "test-model"


def test_update_llm_config_partial():
    host = _get_host_dm()
    original_endpoint = host.llm.endpoint
    resp = client.post("/llm-config", json={"model": "partial-model"})
    assert resp.status_code == 200
    assert resp.json()["model"] == "partial-model"
    assert resp.json()["endpoint"] == original_endpoint


def test_update_llm_config_api_key_masked():
    resp = client.post("/llm-config", json={"api_key": "secret-key-12345678"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("api_key_set") is True
    assert "api_key_masked" in data
    assert "..." in data["api_key_masked"]
    assert "secret-key-12345678" not in data.get("api_key_masked", "")


def test_llm_models_endpoint():
    resp = client.get("/llm-models")
    assert resp.status_code == 200
    data = resp.json()
    assert "models" in data


def test_health_reflects_games_count():
    resp = client.post("/rooms", json={"creator_id": "health_test_admin"})
    assert resp.status_code == 200
    resp = client.get("/health")
    data = resp.json()
    assert data["games_count"] >= 1
