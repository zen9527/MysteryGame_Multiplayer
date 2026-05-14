import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "llm" in data["checks"]
    assert "game_manager" in data["checks"]
    assert "database" in data["checks"]


def test_liveness_probe():
    response = client.get("/api/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_readiness_probe():
    response = client.get("/api/health/ready")
    assert response.status_code in [200, 503]
