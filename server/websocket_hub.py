from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
from server.game_manager import manager
from server.host_dm import host as host_dm
from server.models import Message

router = APIRouter()


class WebSocketHub:
    def __init__(self):
        # room_id -> { player_id: WebSocket }
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        # websocket -> (room_id, player_id)
        self.connections: Dict[WebSocket, tuple] = {}

    async def connect(self, room_id: str, player_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][player_id] = websocket
        self.connections[websocket] = (room_id, player_id)

    def disconnect(self, websocket: WebSocket):
        if websocket not in self.connections:
            return
        room_id, player_id = self.connections.pop(websocket)
        if room_id in self.rooms and player_id in self.rooms[room_id]:
            del self.rooms[room_id][player_id]
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict):
        """广播给房间内所有玩家"""
        if room_id in self.rooms:
            disconnected = []
            for pid, ws in self.rooms[room_id].items():
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(pid)
            # Clean up disconnected players
            for pid in disconnected:
                del self.rooms[room_id][pid]

    async def send_to_player(self, room_id: str, player_id: str, message: dict):
        """发送给特定玩家"""
        if room_id in self.rooms and player_id in self.rooms[room_id]:
            try:
                await self.rooms[room_id][player_id].send_json(message)
            except Exception:
                pass

    async def send_dm_private(self, room_id: str, target_player_id: str, content: str):
        """DM 向特定玩家发送私信"""
        dm_msg = {
            "type": "dm_private",
            "from": "__dm__",
            "to": target_player_id,
            "content": content,
        }
        await self.send_to_player(room_id, target_player_id, dm_msg)

    async def handle_client_message(self, room_id: str, player_id: str, data: dict):
        """处理客户端消息，路由到对应处理器"""
        msg_type = data.get("type")

        if msg_type == "chat":
            content = data.get("content", "")
            manager.add_chat_message(room_id, player_id, content, False, None)
            # Broadcast chat to all players in room
            await self.broadcast(room_id, {
                "type": "chat",
                "from": player_id,
                "content": content,
                "timestamp": "",
            })

        elif msg_type == "private_chat":
            target = data.get("to_player_id", "")
            content = data.get("content", "")
            manager.add_chat_message(room_id, player_id, content, True, target)
            # Send to both sender and receiver only
            chat_msg = {
                "type": "private_chat",
                "from": player_id,
                "content": content,
                "timestamp": "",
            }
            await self.send_to_player(room_id, player_id, chat_msg)
            if target and target != player_id:
                await self.send_to_player(room_id, target, chat_msg)

        elif msg_type == "dm_private":
            # DM → player private message (from API, not client)
            target = data.get("to_player_id", "")
            content = data.get("content", "")
            if target:
                dm_msg = {
                    "type": "dm_private",
                    "from": "__dm__",
                    "to": target,
                    "content": content,
                }
                await self.send_to_player(room_id, target, dm_msg)

        elif msg_type == "accuse":
            # Broadcast accusation to all players
            await self.broadcast(room_id, {
                "type": "accusation",
                "from": player_id,
                "target": data.get("target_role_name", ""),
                "reasoning": data.get("reasoning", ""),
            })

        elif msg_type == "vote":
            # Record vote (handled by API endpoint too)
            pass

        elif msg_type == "request_advance":
            # Player requests DM to advance — trigger LLM event generation
            state = manager.get_state(room_id)
            if state and state.phase in ("playing",):
                try:
                    event_content = host_dm.generate_event(state)
                    manager.push_event(room_id, event_content)
                    await self.broadcast(room_id, {
                        "type": "event",
                        "content": event_content,
                    })
                except Exception as e:
                    manager.add_dm_log(room_id, f"事件生成失败: {e}")


hub = WebSocketHub()


@router.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await hub.connect(room_id, player_id, websocket)

    # Send current state to newly connected player
    state = manager.get_state(room_id)
    if state:
        await hub.send_to_player(room_id, player_id, {
            "type": "system",
            "content": f"你已加入房间，当前阶段: {state.phase}",
        })

    try:
        while True:
            data = await websocket.receive_json()
            await hub.handle_client_message(room_id, player_id, data)
    except WebSocketDisconnect:
        hub.disconnect(websocket)
