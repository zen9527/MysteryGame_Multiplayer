"""
WebSocket message models - Pydantic v2

These models mirror the Zod schemas in shared/schemas/ws.ts
Keep field names and types consistent between both files.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ChatPhase(str, Enum):
    WAITING = "waiting"
    PLAYING = "playing"
    ENDED = "ended"


class CluePhase(str, Enum):
    ACT1 = "act1"
    ACT2 = "act2"


class ClueType(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class ChatMessage(BaseModel):
    """Chat message model - mirrors Zod chatMessageSchema"""
    message_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    player_id: str
    role_name: str
    timestamp: str  # ISO 8601 format
    from_player_name: str


class Clue(BaseModel):
    """Clue model - mirrors Zod clueSchema"""
    id: str
    title: str
    content: str
    unlock_phase: CluePhase
    clue_type: ClueType
    related_role_id: Optional[str] = None


class RoleCard(BaseModel):
    """Role card model - mirrors Zod roleCardSchema"""
    role_id: str
    role_name: str
    player_id: str
    layer: int = Field(..., ge=1, le=3)
    content: str
    secrets: Optional[List[str]] = None


class Player(BaseModel):
    """Player model - mirrors Zod playerSchema"""
    player_id: str
    role_id: str
    role_name: str
    is_admin: bool


class GameState(BaseModel):
    """Game state model - mirrors Zod gameStateSchema"""
    room_id: str
    phase: ChatPhase
    act: int = Field(..., ge=1)
    players: List[Player]
    current_event: Optional[dict] = None
    clues_unlocked: List[str] = []


class PhaseUnlock(BaseModel):
    """Phase unlock response - mirrors Zod phaseUnlockSchema"""
    new_act: int = Field(..., ge=1)
    distributed_role_cards: Optional[List[RoleCard]] = None
    distributed_clues: Optional[List[Clue]] = None


__all__ = [
    "ChatMessage",
    "Clue",
    "RoleCard",
    "Player",
    "GameState",
    "PhaseUnlock",
    "ChatPhase",
    "CluePhase",
    "ClueType"
]
