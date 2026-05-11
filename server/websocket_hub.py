from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import asyncio
import json
from server.game_manager import manager
from server.host_dm import host as host_dm
from server.models import Message
from server.utils.validation import sanitize_string, MAX_CHAT_LENGTH

router = APIRouter()


def _resolve_display_name(state, player_id: str) -> str:
    if player_id == "__dm__":
        return "🎭 DM"
    if state and player_id in state.players:
        player = state.players[player_id]
        if player.role and player.role.name:
            return f"{player.role.name}({player.name})"
        return player.name
    return player_id


class WebSocketHub:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
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
        if room_id in self.rooms:
            disconnected = []
            for pid, ws in self.rooms[room_id].items():
                try:
                    await ws.send_json(message)
                except Exception:
                    disconnected.append(pid)
            for pid in disconnected:
                del self.rooms[room_id][pid]

    async def send_to_player(self, room_id: str, player_id: str, message: dict):
        if room_id in self.rooms and player_id in self.rooms[room_id]:
            try:
                await self.rooms[room_id][player_id].send_json(message)
            except Exception:
                pass

    async def send_dm_private(self, room_id: str, target_player_id: str, content: str):
        dm_msg = {
            "type": "dm_private",
            "from": "__dm__",
            "to": target_player_id,
            "content": content,
        }
        await self.send_to_player(room_id, target_player_id, dm_msg)

    async def handle_client_message(self, room_id: str, player_id: str, data: dict):
        msg_type = data.get("type")

        if msg_type == "chat":
            content = sanitize_string(data.get("content", ""))
            if not content:
                return
            if len(content) > MAX_CHAT_LENGTH:
                content = content[:MAX_CHAT_LENGTH]
            state = manager.get_state(room_id)
            display_name = _resolve_display_name(state, player_id)
            manager.add_chat_message(room_id, player_id, content, False, None)
            await self.broadcast(room_id, {
                "type": "chat",
                "from": display_name,
                "from_player_id": player_id,
                "content": content,
                "timestamp": "",
            })

        elif msg_type == "private_chat":
            target = data.get("to_player_id", "")
            content = sanitize_string(data.get("content", ""))
            if not content or not target:
                return
            if len(content) > MAX_CHAT_LENGTH:
                content = content[:MAX_CHAT_LENGTH]
            manager.add_chat_message(room_id, player_id, content, True, target)
            manager.cache_private_chat(room_id, player_id, target, content)
            chat_msg = {
                "type": "private_chat",
                "from": player_id,
                "content": content,
                "timestamp": "",
            }
            await self.send_to_player(room_id, player_id, chat_msg)
            if target and target != player_id:
                await self.send_to_player(room_id, target, chat_msg)

        elif msg_type == "accuse":
            target = sanitize_string(data.get("target_role_name", ""))
            reasoning = sanitize_string(data.get("reasoning", ""))
            if not target or not reasoning:
                return
            if len(reasoning) > 1000:
                reasoning = reasoning[:1000]
            state = manager.get_state(room_id)
            display_name = _resolve_display_name(state, player_id)
            manager.cache_accusation(room_id, display_name, player_id, target, reasoning)
            await self.broadcast(room_id, {
                "type": "accusation",
                "from": display_name,
                "from_player_id": player_id,
                "target": target,
                "reasoning": reasoning,
            })

        elif msg_type == "vote":
            target = sanitize_string(data.get("target_role_name", ""))
            if not target:
                return
            reasoning = sanitize_string(data.get("reasoning", ""))
            state = manager.get_state(room_id)
            display_name = _resolve_display_name(state, player_id)
            await self.broadcast(room_id, {
                "type": "vote_cast",
                "from": display_name,
                "from_player_id": player_id,
                "target": target,
            })

        elif msg_type == "request_advance":
            state = manager.get_state(room_id)
            if state and state.phase in ("playing",):
                try:
                    state.current_round += 1
                    event = await asyncio.to_thread(host_dm.generate_event, state)
                    result = manager.push_structured_event(room_id, event)
                    if result:
                        if result["public_event"]:
                            await self.broadcast(room_id, {
                                "type": "event",
                                "content": result["public_event"],
                            })
                        for clue in result["private_clues"]:
                            await self.send_dm_private(
                                room_id,
                                clue["player_id"],
                                clue["content"],
                            )
                except Exception as e:
                    manager.add_dm_log(room_id, f"事件生成失败: {e}")


hub = WebSocketHub()


@router.websocket("/ws/{room_id}/{player_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str, player_id: str):
    await hub.connect(room_id, player_id, websocket)

    state = manager.get_state(room_id)
    if state:
        await hub.send_to_player(room_id, player_id, {
            "type": "phase_unlock",
            "phase": state.phase,
            "act": state.act,
        })

        if player_id in state.players:
            player = state.players[player_id]
            cached = state.distributed_role_cards.get(player_id, [])
            if player.role and not any(m.get("layer") == "1" for m in cached):
                await hub.send_to_player(room_id, player_id, {
                    "type": "role_card",
                    "layer": "1",
                    "player_id": player_id,
                    "data": {
                        "name": player.role.name,
                        "description": player.role.description,
                    },
                })

        pending = manager.get_pending_distributions(room_id, player_id)
        for msg in pending:
            await hub.send_to_player(room_id, player_id, msg)

        for msg in state.public_messages[-50:]:
            sender_name = _resolve_display_name(state, msg.from_player_id)

            if msg.type == "event":
                await hub.send_to_player(room_id, player_id, {
                    "type": "event",
                    "content": msg.content,
                })
            else:
                await hub.send_to_player(room_id, player_id, {
                    "type": "chat",
                    "from": sender_name,
                    "from_player_id": msg.from_player_id,
                    "content": msg.content,
                    "timestamp": "",
                })

        await hub.send_to_player(room_id, player_id, {
            "type": "system",
            "content": f"你已加入房间，当前阶段: {state.phase}",
        })

    try:
        while True:
            data = await websocket.receive_json()
            await hub.handle_client_message(room_id, player_id, data)
    except WebSocketDisconnect:
        if state and player_id in state.players:
            player_name = state.players[player_id].name
            hub.disconnect(websocket)
            await hub.broadcast(room_id, {
                "type": "player_left",
                "player_id": player_id,
                "player_name": player_name,
            })
        else:
            hub.disconnect(websocket)
