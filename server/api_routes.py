from fastapi import APIRouter, HTTPException
from server.models import Script
from server.game_manager import manager
import uuid

router = APIRouter()


@router.post("/api/rooms")
async def create_room():
    game_id = str(uuid.uuid4())
    return {"game_id": game_id}


@router.get("/api/rooms")
async def list_rooms():
    return [{"game_id": gid, "player_count": len(state.players)} for gid, state in manager.games.items()]


@router.get("/api/rooms/{game_id}")
async def get_room(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "game_id": state.game_id,
        "phase": state.phase,
        "players": {pid: {"name": p.name, "role_id": p.role_id} for pid, p in state.players.items()},
    }


@router.delete("/api/rooms/{game_id}")
async def delete_room(game_id: str):
    if game_id in manager.games:
        del manager.games[game_id]
    return {"status": "deleted"}


@router.get("/api/health")
async def health_check():
    return {"status": "ok", "games_count": len(manager.games)}
