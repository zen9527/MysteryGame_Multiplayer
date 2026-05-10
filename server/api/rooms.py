from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import uuid
from server.models import Script, Role, Clue, PlotOutline, Vote, Accusation, Message
from server.di import container
from server.middleware import require_admin
from server.utils.display_name import resolve_display_name_for_message

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


# --- Request models ---

class PlayerJoinRequest(BaseModel):
    player_id: str
    name: str


class CreateRoomRequest(BaseModel):
    creator_id: str  # 管理员 ID
    name: str = "管理员"  # 管理员名字（也作为玩家参与游戏）


# --- Room CRUD endpoints ---

@router.post("/rooms")
async def create_room(req: CreateRoomRequest):
    game_id = str(uuid.uuid4())
    _get_manager().create_game(game_id, req.creator_id)
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
        "clues": [c.model_dump() for c in state.script.clues],
        "votes": [v.model_dump() for v in state.votes],
        "public_messages": [
            {
                "from_player_id": m.from_player_id,
                "from_player_name": resolve_display_name_for_message(state, m.from_player_id),
                "content": m.content,
                "type": m.type,
                "timestamp": str(m.timestamp),
            }
            for m in state.public_messages[-50:]
        ],
    }


@router.delete("/rooms/{game_id}")
async def delete_room(game_id: str):
    if game_id in _get_manager().games:
        del _get_manager().games[game_id]
    return {"status": "deleted"}


# --- Player management endpoints ---

@router.post("/rooms/{game_id}/players")
async def add_player(game_id: str, req: PlayerJoinRequest):
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


class AdminActionRequest(BaseModel):
    player_id: str  # 管理员 ID，用于权限校验


@router.post("/rooms/{game_id}/players/{target_pid}/kick")
async def kick_player(game_id: str, target_pid: str, req: AdminActionRequest):
    """踢出玩家（仅管理员）"""
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
async def leave_room(game_id: str, req: PlayerJoinRequest):
    """玩家离开房间"""
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
    """返回可用的剧本类型列表"""
    return {"genres": GENRES, "difficulties": DIFFICULTIES}
