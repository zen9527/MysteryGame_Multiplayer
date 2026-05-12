from fastapi import APIRouter, HTTPException
from server.di import container
from server.utils.validation import ChatRequest, sanitize_string
from server.models import ChatMessage, ChatPhase
from server.utils.display_name import resolve_display_name_for_message
from datetime import datetime
import logging

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


@router.get("/rooms/{game_id}/messages", response_model=list[ChatMessage])
async def get_messages(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    
    validated_messages = []
    for msg in state.public_messages:
        try:
            validated = ChatMessage.model_validate({
                "message_id": msg.id,
                "content": msg.content,
                "player_id": msg.from_player_id,
                "role_name": state.players[msg.from_player_id].role.name if msg.from_player_id in state.players else "__dm__",
                "timestamp": str(msg.timestamp),
                "from_player_name": resolve_display_name_for_message(state, msg.from_player_id),
            })
            validated_messages.append(validated)
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid message in room {game_id}: {e}")
            continue
    
    return validated_messages
