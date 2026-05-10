from fastapi import APIRouter, HTTPException
from server.di import container
from server.utils.validation import ChatRequest, sanitize_string

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


@router.post("/rooms/{game_id}/chat")
async def send_message(game_id: str, req: ChatRequest):
    req.message = sanitize_string(req.message)
    if not req.message:
        raise HTTPException(status_code=400, detail="消息内容不能为空")
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=400, detail="Player not in room")
    _get_manager().add_chat_message(
        game_id, req.player_id, req.message, req.is_private, req.target_player_id
    )
    return {"status": "message sent"}
