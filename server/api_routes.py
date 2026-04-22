from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.models import Script, Role, Clue, PlotOutline, Vote
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


# --- Request/Response models ---

class PlayerJoinRequest(BaseModel):
    player_id: str
    name: str


class ScriptGenerationRequest(BaseModel):
    script: Script


class VoteRequest(BaseModel):
    from_player_id: str
    target_role_name: str
    reasoning: str


class ChatMessageRequest(BaseModel):
    player_id: str
    message: str
    is_private: bool = False
    target_player_id: str | None = None


# --- Room endpoints ---

@router.post("/api/rooms")
async def create_room():
    game_id = str(uuid.uuid4())
    manager.create_game(game_id, _default_script)
    return {"game_id": game_id}


@router.get("/api/rooms")
async def list_rooms():
    return [{"game_id": gid, "player_count": len(state.players), "phase": state.phase} for gid, state in manager.games.items()]


@router.get("/api/rooms/{game_id}")
async def get_room(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {
        "game_id": state.game_id,
        "phase": state.phase,
        "players": {pid: {"name": p.name, "role_id": p.role_id} for pid, p in state.players.items()},
        "clues": [c.model_dump() for c in state.script.clues],
        "votes": [v.model_dump() for v in state.votes],
    }


@router.delete("/api/rooms/{game_id}")
async def delete_room(game_id: str):
    if game_id in manager.games:
        del manager.games[game_id]
    return {"status": "deleted"}


# --- Player endpoints ---

@router.post("/api/rooms/{game_id}/players")
async def add_player(game_id: str, req: PlayerJoinRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    player = manager.add_player(game_id, req.player_id, req.name)
    if player is None:
        raise HTTPException(status_code=400, detail="Room is full (max 6 players)")
    return {"player_id": player.id, "name": player.name, "role_id": player.role_id}


@router.get("/api/rooms/{game_id}/players")
async def list_players(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {pid: {"name": p.name, "role_id": p.role_id} for pid, p in state.players.items()}


# --- Game control endpoints ---

@router.post("/api/rooms/{game_id}/generate")
async def generate_script(game_id: str, req: ScriptGenerationRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if state.phase != "waiting":
        raise HTTPException(status_code=400, detail="Can only generate script in waiting phase")
    manager.set_script(game_id, req.script)
    return {"game_id": game_id, "phase": state.phase}


@router.post("/api/rooms/{game_id}/start")
async def start_game(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if len(state.players) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 players to start")
    manager.start_game(game_id)
    return {"game_id": game_id, "phase": state.phase}


# --- Voting endpoints ---

@router.post("/api/rooms/{game_id}/votes")
async def add_vote(game_id: str, req: VoteRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    vote = Vote(from_player_id=req.from_player_id, target_role_name=req.target_role_name, reasoning=req.reasoning)
    manager.add_vote(game_id, vote)
    return {"status": "vote recorded"}


@router.get("/api/rooms/{game_id}/consensus")
async def check_consensus(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    reached = manager.check_consensus(game_id)
    return {"consensus_reached": reached, "votes": [v.model_dump() for v in state.votes]}


# --- Chat endpoints ---

@router.post("/api/rooms/{game_id}/chat")
async def send_message(game_id: str, req: ChatMessageRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=400, detail="Player not in room")
    manager.add_chat_message(game_id, req.player_id, req.message, req.is_private, req.target_player_id)
    return {"status": "message sent"}


# --- Host DM endpoints ---

@router.post("/api/rooms/{game_id}/host-message")
async def host_message(game_id: str, req: ChatMessageRequest):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    manager.add_chat_message(game_id, "__host__", req.message, False, None)
    return {"status": "host message sent"}


# --- WebSocket endpoint ---

@router.get("/api/health")
async def health_check():
    return {"status": "ok", "games_count": len(manager.games)}
