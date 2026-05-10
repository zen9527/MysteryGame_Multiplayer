import pytest
import json
from fastapi.testclient import TestClient
from server.main import app
from server.game_manager import GameManager
from server.websocket_hub import WebSocketHub, hub
from server.models import Role, Player
from server.di import container

client = TestClient(app)


def _get_manager():
    return container.resolve("game_manager")


def _setup_room_with_players(game_id="ws-test", creator="admin"):
    mgr = _get_manager()
    mgr.create_game(game_id, creator)
    state = mgr.get_state(game_id)
    state.script.roles = [
        Role(id="r1", name="角色A", age=30, occupation="医生", description="医生", background="背景", secret_task="秘密", alibi="不在场", motive="动机"),
        Role(id="r2", name="角色B", age=25, occupation="教师", description="教师", background="背景", secret_task="秘密", alibi="不在场", motive="动机"),
    ]
    mgr.add_player(game_id, "p1", "张三")
    mgr.add_player(game_id, "p2", "李四")
    return state


def _drain_initial_messages(ws, max_msgs=30):
    msgs = []
    for _ in range(max_msgs):
        msg = ws.receive_json()
        msgs.append(msg)
        if msg.get("type") == "system":
            break
    return msgs


def test_ws_connect_and_receive_state():
    _setup_room_with_players("ws-basic")
    with client.websocket_connect("/ws/ws-basic/p1") as ws:
        data = ws.receive_json()
        assert data["type"] == "phase_unlock"
        msgs = _drain_initial_messages(ws)
        system_msgs = [m for m in msgs if m["type"] == "system"]
        assert len(system_msgs) >= 1
        assert "加入房间" in system_msgs[0]["content"]


def test_ws_chat_message():
    _setup_room_with_players("ws-chat")
    with client.websocket_connect("/ws/ws-chat/p1") as ws:
        _drain_initial_messages(ws)
        ws.send_json({"type": "chat", "content": "大家好"})
        chat_msg = ws.receive_json()
        assert chat_msg["type"] == "chat"
        assert chat_msg["content"] == "大家好"
        assert chat_msg["from_player_id"] == "p1"


def test_ws_private_chat():
    _setup_room_with_players("ws-pchat")
    with client.websocket_connect("/ws/ws-pchat/p1") as ws1:
        _drain_initial_messages(ws1)
        with client.websocket_connect("/ws/ws-pchat/p2") as ws2:
            _drain_initial_messages(ws2)
            ws1.send_json({"type": "private_chat", "to_player_id": "p2", "content": "私信内容"})
            msg1 = ws1.receive_json()
            assert msg1["type"] == "private_chat"
            assert msg1["content"] == "私信内容"
            msg2 = ws2.receive_json()
            assert msg2["type"] == "private_chat"
            assert msg2["content"] == "私信内容"


def test_ws_accuse():
    _setup_room_with_players("ws-accuse")
    with client.websocket_connect("/ws/ws-accuse/p1") as ws:
        _drain_initial_messages(ws)
        ws.send_json({"type": "accuse", "target_role_name": "角色B", "reasoning": "他很可疑"})
        msg = ws.receive_json()
        assert msg["type"] == "accusation"
        assert msg["target"] == "角色B"
        assert msg["reasoning"] == "他很可疑"


def test_ws_vote():
    _setup_room_with_players("ws-vote")
    with client.websocket_connect("/ws/ws-vote/p1") as ws:
        _drain_initial_messages(ws)
        ws.send_json({"type": "vote", "target_role_name": "角色A", "reasoning": "投票理由"})
        msg = ws.receive_json()
        assert msg["type"] == "vote_cast"
        assert msg["target"] == "角色A"


def test_ws_disconnect_removes_connection():
    ws_hub = WebSocketHub()
    assert len(ws_hub.rooms) == 0
    ws_hub.rooms["test-room"] = {"p1": None}
    ws_hub.connections[None] = ("test-room", "p1")
    ws_hub.disconnect(None)
    assert "p1" not in ws_hub.rooms.get("test-room", {})


def test_ws_disconnect_unknown_websocket():
    ws_hub = WebSocketHub()
    ws_hub.disconnect("unknown-ws")
    assert len(ws_hub.rooms) == 0


def test_ws_private_chat_cached_for_reconnect():
    _setup_room_with_players("ws-pcache")
    mgr = _get_manager()
    with client.websocket_connect("/ws/ws-pcache/p1") as ws1:
        _drain_initial_messages(ws1)
        with client.websocket_connect("/ws/ws-pcache/p2") as ws2:
            _drain_initial_messages(ws2)
            ws1.send_json({"type": "private_chat", "to_player_id": "p2", "content": "缓存测试"})
            ws1.receive_json()
            ws2.receive_json()
    pending = mgr.get_pending_distributions("ws-pcache", "p2")
    private_msgs = [m for m in pending if m.get("type") == "private_chat"]
    assert any(m["content"] == "缓存测试" for m in private_msgs)


def test_ws_accuse_cached_for_reconnect():
    _setup_room_with_players("ws-acache")
    mgr = _get_manager()
    with client.websocket_connect("/ws/ws-acache/p1") as ws:
        _drain_initial_messages(ws)
        ws.send_json({"type": "accuse", "target_role_name": "角色B", "reasoning": "推理"})
        ws.receive_json()
    pending = mgr.get_pending_distributions("ws-acache", "p1")
    accusations = [m for m in pending if m.get("type") == "accusation"]
    assert len(accusations) >= 1
    assert accusations[0]["target"] == "角色B"


def test_ws_reconnect_resends_cached():
    _setup_room_with_players("ws-reconn")
    mgr = _get_manager()
    mgr.cache_accusation("ws-reconn", "张三", "p1", "角色B", "推理")
    with client.websocket_connect("/ws/ws-reconn/p1") as ws:
        msgs = _drain_initial_messages(ws, max_msgs=50)
        accusation_msgs = [m for m in msgs if m.get("type") == "accusation"]
        assert len(accusation_msgs) >= 1
