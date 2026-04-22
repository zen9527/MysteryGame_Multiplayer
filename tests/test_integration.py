import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_create_room():
    response = client.post("/api/rooms")
    assert response.status_code == 200
    assert "game_id" in response.json()

def test_list_rooms():
    client.post("/api/rooms")
    response = client.get("/api/rooms")
    assert response.status_code == 200
    assert len(response.json()) >= 1
