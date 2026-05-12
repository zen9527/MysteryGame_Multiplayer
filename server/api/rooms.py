from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import uuid
from server.models import Script, Role, Clue, PlotOutline, Vote, Accusation, Message
from server.constants import MAX_PUBLIC_MESSAGE_HISTORY
from server.di import container
from server.middleware import require_admin
from server.utils.display_name import resolve_display_name_for_message
from server.utils.validation import (
    CreateRoomRequest,
    JoinRoomRequest,
    AdminActionRequest,
    PlayerLeaveRequest,
    sanitize_string,
)
from server.models import WsClue, CluePhase, ClueType, ChatMessage

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_hub():
    return container.resolve("websocket_hub")


GENRES = [
    {"value": "悬疑推理", "label": "经典谋杀案，逻辑推理"},
    {"value": "古风权谋", "label": "古代宫廷/江湖，权力斗争"},
    {"value": "现代都市", "label": "当代社会背景，情感纠葛"},
    {"value": "恐怖惊悚", "label": "超自然元素，心理恐惧"},
    {"value": "欢乐搞笑", "label": "轻松幽默，反转结局"},
    {"value": "科幻未来", "label": "赛博朋克/太空，高科技犯罪"},
]

DIFFICULTIES = ["简单", "中等", "困难"]


@router.post("/rooms")
async def create_room(req: CreateRoomRequest):
    req.name = sanitize_string(req.name)
    if not req.name:
        raise HTTPException(status_code=400, detail="管理员名字不能为空")
    game_id = str(uuid.uuid4())
    _get_manager().create_game(game_id, req.creator_id, script_id=req.script_id)
    _get_manager().add_player(game_id, req.creator_id, req.name)
    return {"game_id": game_id}


@router.get("/rooms")
async def list_rooms():
    return [
        {
            "game_id": gid,
            "player_count": len(state.players),
            "phase": state.phase,
            "act": state.act,
            "script_generated": state.script_generated,
            "title": state.script.title if state.script.title != "待生成" else "",
        }
        for gid, state in _get_manager().games.items()
    ]


@router.get("/rooms/{game_id}")
async def get_room(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "game_id": state.game_id,
        "phase": state.phase,
        "act": state.act,
        "room_creator_id": state.room_creator_id,
        "script_generated": state.script_generated,
        "players": {
            pid: {
                "name": p.name,
                "role_id": p.role_id,
            }
            for pid, p in state.players.items()
        },
        "script": {
            "title": state.script.title,
            "genre": state.script.genre,
            "difficulty": state.script.difficulty,
            "estimated_time": state.script.estimated_time,
            "background_story": state.script.background_story,
            "true_killer": state.script.true_killer,
            "roles": [r.model_dump() for r in state.script.roles],
            "roles_count": len(state.script.roles),
            "plot_outline": state.script.plot_outline.model_dump(),
        } if state.script_generated else None,
        "clues": [
            WsClue.model_validate({
                "id": c.id,
                "title": c.title,
                "content": c.content,
                "unlock_phase": c.unlock_phase if hasattr(c, 'unlock_phase') else "act1",
                "clue_type": c.clue_type if hasattr(c, 'clue_type') else "public",
                "related_role_id": c.related_role_id if hasattr(c, 'related_role_id') else None,
            }).model_dump()
            for c in state.script.clues
        ],
        "votes": [v.model_dump() for v in state.votes],
        "public_messages": [
            ChatMessage.model_validate({
                "message_id": m.id,
                "content": m.content,
                "player_id": m.from_player_id,
                "role_name": state.players[m.from_player_id].role.name if m.from_player_id in state.players and state.players[m.from_player_id].role else "__dm__",
                "timestamp": str(m.timestamp),
                "from_player_name": resolve_display_name_for_message(state, m.from_player_id),
            }).model_dump()
            for m in state.public_messages[-MAX_PUBLIC_MESSAGE_HISTORY:]
        ],
    }


@router.delete("/rooms/{game_id}")
async def delete_room(game_id: str, req: AdminActionRequest):
    if game_id not in _get_manager().games:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)
    del _get_manager().games[game_id]
    return {"status": "deleted"}


@router.post("/rooms/{game_id}/players")
async def add_player(game_id: str, req: JoinRoomRequest):
    req.name = sanitize_string(req.name)
    if not req.name:
        raise HTTPException(status_code=400, detail="玩家名字不能为空")
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    player = _get_manager().add_player(game_id, req.player_id, req.name)
    if player is None:
        raise HTTPException(status_code=400, detail="房间已满或剧本未生成")
    await _get_hub().broadcast(game_id, {
        "type": "player_joined",
        "player_id": player.id,
        "player_name": player.name,
    })
    return {"player_id": player.id, "name": player.name, "role_id": player.role_id}


@router.get("/rooms/{game_id}/players")
async def list_players(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        pid: {"name": p.name, "role_id": p.role_id}
        for pid, p in state.players.items()
    }


@router.post("/rooms/{game_id}/players/{target_pid}/kick")
async def kick_player(game_id: str, target_pid: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    target_player = state.players.get(target_pid)
    _get_manager().kick_player(game_id, target_pid)

    await _get_hub().broadcast(game_id, {
        "type": "player_left",
        "player_id": target_pid,
        "player_name": target_player.name if target_player else "",
    })

    return {"status": "kicked", "target_player_id": target_pid}


@router.post("/rooms/{game_id}/leave")
async def leave_room(game_id: str, req: PlayerLeaveRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")

    if req.player_id not in state.players:
        raise HTTPException(status_code=400, detail="玩家不在房间中")

    target_player = state.players.get(req.player_id)
    _get_manager().kick_player(game_id, req.player_id)

    await _get_hub().broadcast(game_id, {
        "type": "player_left",
        "player_id": req.player_id,
        "player_name": target_player.name if target_player else "",
    })

    return {"status": "left", "player_id": req.player_id}


@router.get("/genres")
async def list_genres():
    return {"genres": GENRES, "difficulties": DIFFICULTIES}
