from pydantic import BaseModel, Field
from typing import Optional, List


# 客户端 → 服务器
class JoinRequest(BaseModel):
    player_name: str


class ChatRequest(BaseModel):
    content: str


class PrivateChatRequest(BaseModel):
    to_player_id: str
    content: str


class AccuseRequest(BaseModel):
    target_role_name: str
    reasoning: str


class VoteRequest(BaseModel):
    target_role_name: str
    reasoning: str


class AdvanceRequest(BaseModel):
    pass


# 服务器 → 客户端
class SystemMessage(BaseModel):
    type: str = "system"
    content: str


class EventMessage(BaseModel):
    type: str = "event"
    content: str


class ClueRevealMessage(BaseModel):
    type: str = "clue_reveal"
    clue: dict
    public: bool
    to_player_id: Optional[str] = None


class ChatMessage(BaseModel):
    type: str = "chat"
    from_player: str
    content: str
    timestamp: str


class AccusationMessage(BaseModel):
    type: str = "accusation"
    from_player: str
    target: str
    reasoning: str


class VoteResultMessage(BaseModel):
    type: str = "vote_result"
    round: int
    results: dict[str, int]
    consensus: bool


class RevealMessage(BaseModel):
    type: str = "reveal"
    truth: dict
    player_evaluations: dict[str, str]


class GameOverMessage(BaseModel):
    type: str = "game_over"
    result: str  # correct/wrong/time_out


class RoleCardMessage(BaseModel):
    type: str = "role_card"
    layer: str  # "1", "2", "3"
    player_id: str
    data: dict  # 角色卡数据


class DMPrivateMessage(BaseModel):
    type: str = "dm_private"
    from_: str = Field(default="__dm__", alias="from")
    to: str
    content: str

    model_config = {"populate_by_name": True}


class ClueInfo(BaseModel):
    id: str
    title: str
    content: str
    content_hint: str
    is_red_herring: bool


class ClueUnlockMessage(BaseModel):
    type: str = "clue_unlock"
    player_id: str
    clue: ClueInfo


class PhaseUnlockMessage(BaseModel):
    type: str = "phase_unlock"
    phase: str
    act: int
