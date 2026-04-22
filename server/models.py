from pydantic import BaseModel, Field
from typing import Optional, List
import uuid
from datetime import datetime


class Role(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int
    occupation: str
    description: str
    background: str
    secret_task: str
    alibi: str
    motive: str
    relationships: List[dict[str, str]] = Field(default_factory=list)


class Clue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    target_role: Optional[str] = None
    is_red_herring: bool = False
    content_hint: str


class PlotOutline(BaseModel):
    act1: str
    act2: str
    act3: str


class Script(BaseModel):
    title: str
    genre: str  # 悬疑推理/古风权谋/现代都市/恐怖惊悚/欢乐搞笑/科幻未来
    difficulty: str  # 简单/中等/困难
    estimated_time: int
    background_story: str
    true_killer: str
    murder_method: str
    cover_up: str
    roles: List[Role]
    clues: List[Clue]
    plot_outline: PlotOutline


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role_id: str
    status: str = "connected"  # connected/playing/left
    has_read_role: bool = False


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_player_id: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    type: str  # public/private/system/event
    to_player_id: Optional[str] = None


class Accusation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_player_id: str
    target_role_name: str
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)


class Vote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_player_id: str
    target_role_name: str
    reasoning: str
    timestamp: datetime = Field(default_factory=datetime.now)


class GameState(BaseModel):
    game_id: str
    phase: str  # waiting/playing/trial/revealed/finished
    players: dict[str, Player]
    script: Script
    public_messages: List[Message] = Field(default_factory=list)
    private_messages: List[Message] = Field(default_factory=list)
    accusations: List[Accusation] = Field(default_factory=list)
    votes: List[Vote] = Field(default_factory=list)
    timer_start: datetime = Field(default_factory=datetime.now)
    max_duration_minutes: int = 60
    current_round: int = 0
    host_message_history: List[Message] = Field(default_factory=list)
