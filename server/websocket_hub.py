from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict
import json
from server.models import GameState, Player

router = APIRouter()

class WebSocketHub:
    def __init__(self):
        self.rooms: Dict[str, Dict[str, WebSocket]] = {}
        self.game_states: Dict[str, GameState] = {}

    async def connect(self, room_id: str, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][websocket.client.root_path.split("/")[-1]] = websocket

    def disconnect(self, room_id: str, websocket: WebSocket):
        player_id = websocket.client.root_path.split("/")[-1]
        if room_id in self.rooms and player_id in self.rooms[room_id]:
            del self.rooms[room_id][player_id]
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast(self, room_id: str, message: dict):
        if room_id in self.rooms:
            for player_ws in self.rooms[room_id].values():
                await player_ws.send_json(message)

    async def send_to_player(self, room_id: str, player_id: str, message: dict):
        if room_id in self.rooms and player_id in self.rooms[room_id]:
            await self.rooms[room_id][player_id].send_json(message)

hub = WebSocketHub()

@router.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await hub.connect(room_id, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            # 消息路由由 GameManager 处理
            message_type = data.get("type")
            if message_type:
                # 这里后续由 GameManager 处理
                pass
    except WebSocketDisconnect:
        hub.disconnect(room_id, websocket)
