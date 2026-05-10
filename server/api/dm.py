from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
from server.di import container
from server.middleware import require_admin

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_host_dm():
    return container.resolve("host_dm")


def _get_hub():
    return container.resolve("websocket_hub")


class PushEventRequest(BaseModel):
    player_id: str


class AddClueRequest(BaseModel):
    player_id: str
    clue_title: str
    clue_content: str


class DMPrivateRequest(BaseModel):
    player_id: str  # 管理员 ID
    to_player_id: str  # 目标玩家 ID
    content: str


class ChatResponseRequest(BaseModel):
    player_id: str
    content: str = Field(min_length=1, max_length=500)


@router.post("/rooms/{game_id}/dm/add-clue")
async def add_clue(game_id: str, req: AddClueRequest):
    """追加自定义线索（仅管理员）"""
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().add_clue(game_id, req.clue_title, req.clue_content)
    _get_manager().push_event(game_id, f"🔍 新线索发现：{req.clue_title} — {req.clue_content}")
    return {"status": "clue_added"}


@router.post("/rooms/{game_id}/dm/private")
async def dm_private(game_id: str, req: DMPrivateRequest):
    """DM 向特定玩家发送私信（仅管理员）"""
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().add_chat_message(game_id, "__dm__", req.content, is_private=True, target_player_id=req.to_player_id)

    if req.to_player_id not in state.distributed_dm_private:
        state.distributed_dm_private[req.to_player_id] = []
    state.distributed_dm_private[req.to_player_id].append({
        "type": "dm_private",
        "from": "__dm__",
        "to": req.to_player_id,
        "content": req.content,
    })

    await _get_hub().send_dm_private(game_id, req.to_player_id, req.content)
    return {"status": "dm_private_sent"}


def _chat_response_generator(game_id: str, player_id: str, player_message: str, state):
    """SSE generator for DM chat response."""
    if state.phase not in ("playing", "waiting"):
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待中或游戏中与 DM 对话\"}}\n\n"
        return

    last_chat = state.dm_chat_cooldowns.get(player_id)
    if last_chat and (datetime.now() - last_chat).total_seconds() < 30:
        yield f"data: {{\"type\": \"error\", \"message\": \"请等待 30 秒后再向 DM 提问\"}}\n\n"
        return

    state.dm_chat_cooldowns[player_id] = datetime.now()

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_reply = ""
        for chunk in _get_host_dm().respond_to_chat_stream(state, player_id, player_message):
            full_reply += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        _get_manager().add_dm_chat_response(game_id, player_id, player_message, full_reply)

        done_payload = json.dumps({
            "type": "done",
            "content": full_reply,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/rooms/{game_id}/dm/chat-response")
async def chat_response(game_id: str, req: ChatResponseRequest):
    """流式 DM 私信回复（SSE），实时返回生成进度。"""
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=403, detail="Player not in room")

    _get_manager().add_chat_message(game_id, req.player_id, req.content, is_private=True, target_player_id="__dm__")

    return StreamingResponse(
        _chat_response_generator(game_id, req.player_id, req.content, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/rooms/{game_id}/dm/log")
async def get_dm_log(game_id: str):
    """获取 DM 推理日志"""
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"dm_log": state.dm_log}
