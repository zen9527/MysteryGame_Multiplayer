import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.game_manager import GameManager
from server.models import Role, Script, PlotOutline
from server.di import container

client = TestClient(app)


def _get_manager():
    return container.resolve("game_manager")


def _setup_room(creator="admin_1"):
    resp = client.post("/rooms", json={"creator_id": creator})
    game_id = resp.json()["game_id"]
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="医生", background="背景", secret_task="秘密", alibi="不在场", motive="动机"),
        Role(id="r2", name="角色B", age=25, occupation="教师", description="教师", background="背景", secret_task="秘密", alibi="不在场", motive="动机"),
    ]
    mgr.add_player(game_id, "p1", "张三")
    mgr.add_player(game_id, "p2", "李四")
    return game_id


def _setup_playing_room(creator="admin_1"):
    game_id = _setup_room(creator)
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script_generated = True
    mgr.start_game(game_id)
    return game_id


def test_add_clue_admin():
    game_id = _setup_room()
    initial_count = len(_get_manager().get_state(game_id).script.clues)
    resp = client.post(
        f"/rooms/{game_id}/dm/add-clue",
        json={"player_id": "admin_1", "clue_title": "新线索", "clue_content": "血迹在地板上"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "clue_added"
    state = _get_manager().get_state(game_id)
    assert len(state.script.clues) == initial_count + 1


def test_add_clue_non_admin():
    game_id = _setup_room()
    resp = client.post(
        f"/rooms/{game_id}/dm/add-clue",
        json={"player_id": "p1", "clue_title": "新线索", "clue_content": "内容"},
    )
    assert resp.status_code == 403


def test_add_clue_not_found():
    resp = client.post(
        "/rooms/nonexistent/dm/add-clue",
        json={"player_id": "admin", "clue_title": "线索", "clue_content": "内容"},
    )
    assert resp.status_code == 404


def test_dm_private_admin():
    game_id = _setup_room()
    resp = client.post(
        f"/rooms/{game_id}/dm/private",
        json={"player_id": "admin_1", "to_player_id": "p1", "content": "DM私信内容"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "dm_private_sent"
    state = _get_manager().get_state(game_id)
    dm_privates = [m for m in state.private_messages if m.from_player_id == "__dm__" and m.to_player_id == "p1"]
    assert len(dm_privates) >= 1


def test_dm_private_cached_for_reconnect():
    game_id = _setup_room()
    client.post(
        f"/rooms/{game_id}/dm/private",
        json={"player_id": "admin_1", "to_player_id": "p1", "content": "缓存私信"},
    )
    mgr = _get_manager()
    pending = mgr.get_pending_distributions(game_id, "p1")
    dm_msgs = [m for m in pending if m.get("type") == "dm_private" and m.get("content") == "缓存私信"]
    assert len(dm_msgs) >= 1


def test_dm_private_non_admin():
    game_id = _setup_room()
    resp = client.post(
        f"/rooms/{game_id}/dm/private",
        json={"player_id": "p1", "to_player_id": "p2", "content": "假冒DM"},
    )
    assert resp.status_code == 403


def test_dm_private_not_found():
    resp = client.post(
        "/rooms/nonexistent/dm/private",
        json={"player_id": "admin", "to_player_id": "p1", "content": "内容"},
    )
    assert resp.status_code == 404


def test_dm_log():
    game_id = _setup_room()
    _get_manager().add_dm_log(game_id, "测试日志条目")
    resp = client.get(f"/rooms/{game_id}/dm/log")
    assert resp.status_code == 200
    data = resp.json()
    assert "dm_log" in data
    assert len(data["dm_log"]) >= 1
    assert "测试日志条目" in data["dm_log"]


def test_dm_log_not_found():
    resp = client.get("/rooms/nonexistent/dm/log")
    assert resp.status_code == 404


def test_dm_chat_response_not_found():
    resp = client.post(
        "/rooms/nonexistent/dm/chat-response",
        json={"player_id": "p1", "content": "你好"},
    )
    assert resp.status_code == 404


def test_dm_chat_response_player_not_in_room():
    game_id = _setup_room()
    resp = client.post(
        f"/rooms/{game_id}/dm/chat-response",
        json={"player_id": "nonexistent_player", "content": "你好"},
    )
    assert resp.status_code == 403
