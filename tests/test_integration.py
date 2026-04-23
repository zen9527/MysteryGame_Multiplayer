import pytest
from fastapi.testclient import TestClient
from server.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_room_with_creator():
    response = client.post("/api/rooms", json={"creator_id": "admin_1"})
    assert response.status_code == 200
    data = response.json()
    assert "game_id" in data


def test_list_rooms():
    client.post("/api/rooms", json={"creator_id": "admin_1"})
    response = client.get("/api/rooms")
    assert response.status_code == 200
    assert len(response.json()) >= 1


def test_get_room_not_found():
    response = client.get("/api/rooms/nonexistent")
    assert response.status_code == 404


def test_genres_endpoint():
    response = client.get("/api/genres")
    assert response.status_code == 200
    data = response.json()
    assert len(data["genres"]) == 6
    assert "悬疑推理" in [g["value"] for g in data["genres"]]


def test_start_without_script_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    # Add a player first so we hit the script check, not the player count check
    from server.game_manager import manager
    state = manager.get_state(game_id)
    # Need at least 2 players and no script generated
    from server.models import Role
    state.script.roles = [
        Role(id="1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    manager.add_player(game_id, "p1", "张三")
    manager.add_player(game_id, "p2", "李四")

    response = client.post(f"/api/rooms/{game_id}/start")
    assert response.status_code == 400
    assert "剧本" in response.json()["detail"]


def test_admin_kick_non_admin_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    response = client.post(
        f"/api/rooms/{game_id}/players/p_fake/kick",
        json={"player_id": "not_admin"},
    )
    assert response.status_code == 403


def test_force_trial_by_admin():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    # Start first (need to set script_generated)
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "admin_1"},
    )
    assert response.status_code == 200
    assert response.json()["phase"] == "trial"


def test_force_trial_by_non_admin_fails():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "not_admin"},
    )
    assert response.status_code == 403


def test_end_game_by_admin():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/end-game",
        json={"player_id": "admin_1"},
    )
    assert response.status_code == 200
    assert response.json()["phase"] == "revealed"


def test_dm_log_endpoint():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]

    response = client.get(f"/api/rooms/{game_id}/dm/log")
    assert response.status_code == 200
    assert "dm_log" in response.json()
