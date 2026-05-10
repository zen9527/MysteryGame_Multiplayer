import pytest
from fastapi.testclient import TestClient
from server.main import app
from server.game_manager import GameManager
from server.models import Role, Script, PlotOutline, Clue, PrivateEvent
from server.di import container

client = TestClient(app)


def _get_manager():
    return container.resolve("game_manager")


def _setup_playable_game(creator="admin_1", player_count=2):
    resp = client.post("/api/rooms", json={"creator_id": creator})
    game_id = resp.json()["game_id"]
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    roles = [
        Role(id=f"r{i}", name=f"角色{i}", age=25 + i, occupation=f"职业{i}",
             description=f"描述{i}", background=f"背景{i}", secret_task=f"秘密{i}",
             alibi=f"不在场{i}", motive=f"动机{i}")
        for i in range(1, player_count + 1)
    ]
    state.script.roles = roles
    state.script.clues = [
        Clue(id="c1", title="线索1", content="内容1", target_role=None, is_red_herring=False, content_hint="提示1", unlock_phase="act1"),
        Clue(id="c2", title="线索2", content="内容2", target_role=None, is_red_herring=False, content_hint="提示2", unlock_phase="act2"),
    ]
    state.script.plot_outline = PlotOutline(act1="第一幕概述", act2="第二幕概述", act3="第三幕概述")
    for i in range(1, player_count + 1):
        mgr.add_player(game_id, f"p{i}", f"玩家{i}")
    state.script_generated = True
    return game_id


def test_start_game_success():
    game_id = _setup_playable_game()
    resp = client.post(f"/api/rooms/{game_id}/start")
    assert resp.status_code == 200
    data = resp.json()
    assert data["phase"] == "playing"
    state = _get_manager().get_state(game_id)
    assert state.phase == "playing"
    assert state.act == 1


def test_start_game_not_found():
    resp = client.post("/api/rooms/nonexistent/start")
    assert resp.status_code == 404


def test_start_game_too_few_players():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
    ]
    mgr.add_player(game_id, "p1", "张三")
    state.script_generated = True
    resp = client.post(f"/api/rooms/{game_id}/start")
    assert resp.status_code == 400
    assert "2 名玩家" in resp.json()["detail"]


def test_start_game_no_script():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    mgr = _get_manager()
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="r2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    mgr.add_player(game_id, "p1", "张三")
    mgr.add_player(game_id, "p2", "李四")
    resp = client.post(f"/api/rooms/{game_id}/start")
    assert resp.status_code == 400
    assert "剧本" in resp.json()["detail"]


def test_advance_act_admin(monkeypatch):
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/advance-act",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["act"] == 2
    state = mgr.get_state(game_id)
    assert state.act == 2


def test_advance_act_non_admin():
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/advance-act",
        json={"player_id": "p1"},
    )
    assert resp.status_code == 403


def test_advance_act_not_playing():
    game_id = _setup_playable_game()
    resp = client.post(
        f"/api/rooms/{game_id}/advance-act",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 400


def test_advance_act_beyond_max():
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    mgr.get_state(game_id).act = 3
    resp = client.post(
        f"/api/rooms/{game_id}/advance-act",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 400
    assert "最后一幕" in resp.json()["detail"]


def test_force_trial_admin():
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 200
    assert resp.json()["phase"] == "trial"


def test_force_trial_non_admin():
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/force-trial",
        json={"player_id": "p1"},
    )
    assert resp.status_code == 403


def test_force_trial_not_found():
    resp = client.post(
        "/api/rooms/nonexistent/force-trial",
        json={"player_id": "admin"},
    )
    assert resp.status_code == 404


def test_end_game_admin(monkeypatch):
    monkeypatch.setattr(
        "server.host_dm.host.generate_event",
        lambda state: {"public_event": "真相揭晓", "private_clues": [], "dm_instruction": ""},
    )
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/end-game",
        json={"player_id": "admin_1"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")


def test_end_game_non_admin():
    game_id = _setup_playable_game()
    mgr = _get_manager()
    mgr.start_game(game_id)
    resp = client.post(
        f"/api/rooms/{game_id}/end-game",
        json={"player_id": "p1"},
    )
    assert resp.status_code == 403


def test_advance_act_not_found():
    resp = client.post(
        "/api/rooms/nonexistent/advance-act",
        json={"player_id": "admin"},
    )
    assert resp.status_code == 404


def test_end_game_not_found():
    resp = client.post(
        "/api/rooms/nonexistent/end-game",
        json={"player_id": "admin"},
    )
    assert resp.status_code == 404
