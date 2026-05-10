from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from server.models import Vote, Accusation
from server.di import container

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


class AccusationRequest(BaseModel):
    from_player_id: str
    target_role_name: str
    reasoning: str


class VoteRequest(BaseModel):
    from_player_id: str
    target_role_name: str
    reasoning: str


@router.post("/api/rooms/{game_id}/accusations")
async def add_accusation(game_id: str, req: AccusationRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    accusation = Accusation(
        from_player_id=req.from_player_id,
        target_role_name=req.target_role_name,
        reasoning=req.reasoning,
    )
    _get_manager().add_accusation(game_id, accusation)
    return {"status": "accusation recorded"}


@router.post("/api/rooms/{game_id}/votes")
async def add_vote(game_id: str, req: VoteRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    vote = Vote(
        from_player_id=req.from_player_id,
        target_role_name=req.target_role_name,
        reasoning=req.reasoning,
    )
    _get_manager().add_vote(game_id, vote)
    return {"status": "vote recorded"}


@router.get("/api/rooms/{game_id}/consensus")
async def check_consensus(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    reached = _get_manager().check_consensus(game_id)
    return {
        "consensus_reached": reached,
        "votes": [v.model_dump() for v in state.votes],
    }
