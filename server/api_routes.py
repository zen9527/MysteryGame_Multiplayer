from fastapi import APIRouter, HTTPException
from server.models import Script, Role, Clue, PlotOutline
from server.game_manager import manager
import uuid

router = APIRouter()


_default_script = Script(
    title="默认剧本",
    genre="悬疑推理",
    difficulty="简单",
    estimated_time=60,
    background_story="默认剧本背景",
    true_killer="未知",
    murder_method="默认",
    cover_up="默认",
    roles=[Role(name="玩家1", age=20, occupation="学生", description="描述", background="背景", secret_task="任务", alibi="不在场证明", motive="动机")],
    clues=[Clue(title="线索1", content="内容", content_hint="提示")],
    plot_outline=PlotOutline(act1="第一幕", act2="第二幕", act3="第三幕"),
)


@router.post("/api/rooms")
async def create_room():
    game_id = str(uuid.uuid4())
    manager.create_game(game_id, _default_script)
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
