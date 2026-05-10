import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.game_manager import GameManager
from server.models import Role, Script, PlotOutline, Clue
from server.di import container

client = TestClient(app)


def _get_manager():
    return container.resolve("game_manager")


def _create_room(creator="admin_1"):
    resp = client.post("/rooms", json={"creator_id": creator})
    assert resp.status_code == 200
    return resp.json()["game_id"]


def _setup_room_with_script_and_players(player_count=2, creator="admin_1"):
    game_id = _create_room(creator)
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    roles = [
        Role(id=f"r{i}", name=f"角色{i}", age=25 + i, occupation=f"职业{i}",
             description=f"描述{i}", background=f"背景{i}", secret_task=f"秘密{i}",
             alibi=f"不在场{i}", motive=f"动机{i}")
        for i in range(1, player_count + 1)
    ]
    state.script.roles = roles
    for i in range(1, player_count + 1):
        mgr.add_player(game_id, f"p{i}", f"玩家{i}")
    return game_id


def test_create_room():
    game_id = _create_room()
    assert game_id is not None
    state = _get_manager().get_state(game_id)
    assert state is not None
    assert state.phase == "waiting"
    assert state.room_creator_id == "admin_1"


def test_list_rooms():
    _create_room()
    resp = client.get("/rooms")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_get_room_detail():
    game_id = _create_room()
    resp = client.get(f"/rooms/{game_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["game_id"] == game_id
    assert data["phase"] == "waiting"
    assert data["room_creator_id"] == "admin_1"
    assert "players" in data


def test_get_room_not_found():
    resp = client.get("/rooms/nonexistent-room-id")
    assert resp.status_code == 404


def test_delete_room():
    game_id = _create_room()
    resp = client.delete(f"/rooms/{game_id}")
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert _get_manager().get_state(game_id) is None


def test_delete_nonexistent_room():
    resp = client.delete("/rooms/nonexistent")
    assert resp.status_code == 200


def test_add_player_to_room():
    game_id = _create_room()
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="r2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    resp = client.post(f"/rooms/{game_id}/players", json={"player_id": "p1", "name": "张三"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "张三"


def test_add_player_to_nonexistent_room():
    resp = client.post("/rooms/nonexistent/players", json={"player_id": "p1", "name": "张三"})
    assert resp.status_code == 404


def test_add_player_room_full():
    game_id = _setup_room_with_script_and_players(2)
    resp = client.post(f"/rooms/{game_id}/players", json={"player_id": "p3", "name": "王五"})
    assert resp.status_code == 400


def test_list_players():
    game_id = _create_room()
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="r2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    client.post(f"/rooms/{game_id}/players", json={"player_id": "p1", "name": "张三"})
    resp = client.get(f"/rooms/{game_id}/players")
    assert resp.status_code == 200
    data = resp.json()
    assert "p1" in data
    assert data["p1"]["name"] == "张三"


def test_list_players_not_found():
    resp = client.get("/rooms/nonexistent/players")
    assert resp.status_code == 404


def test_kick_player_admin():
    game_id = _setup_room_with_script_and_players(2)
    resp = client.post(
        f"/rooms/{game_id}/players/p1/kick",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "kicked"


def test_kick_player_non_admin():
    game_id = _setup_room_with_script_and_players(2)
    resp = client.post(
        f"/rooms/{game_id}/players/p2/kick",
        json={"player_id": "p1"},
    )
    assert resp.status_code == 403


def test_leave_room():
    game_id = _setup_room_with_script_and_players(2)
    resp = client.post(
        f"/rooms/{game_id}/leave",
        json={"player_id": "p1", "name": "玩家1"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "left"


def test_leave_room_not_in_room():
    game_id = _create_room()
    resp = client.post(
        f"/rooms/{game_id}/leave",
        json={"player_id": "nonexistent", "name": "无名"},
    )
    assert resp.status_code == 400


def test_genres_endpoint():
    resp = client.get("/genres")
    assert resp.status_code == 200
    data = resp.json()
    assert "genres" in data
    assert "difficulties" in data
    assert len(data["genres"]) == 6


def test_get_room_public_messages():
    game_id = _create_room()
    mgr = _get_manager()
    mgr.push_event(game_id, "测试事件消息")
    resp = client.get(f"/rooms/{game_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["public_messages"]) >= 1
    assert any(m["content"] == "测试事件消息" for m in data["public_messages"])
