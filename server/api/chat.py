from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.di import container

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


class ChatMessageRequest(BaseModel):
    player_id: str
    message: str
    is_private: bool = False
    target_player_id: str | None = None


@router.post("/api/rooms/{game_id}/chat")
async def send_message(game_id: str, req: ChatMessageRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=400, detail="Player not in room")
    _get_manager().add_chat_message(
        game_id, req.player_id, req.message, req.is_private, req.target_player_id
    )
    return {"status": "message sent"}
