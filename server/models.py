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
    target_player_ids: List[str] = Field(default_factory=list)
    unlock_phase: str = "act2"
    trigger_condition: Optional[str] = None


class PrivateEvent(BaseModel):
    """DM 私信触发点 — LLM 生成剧本时规划"""
    phase: str  # act1, act2, act3, trial
    target_role_name: str  # 目标玩家角色名（LLM 输出角色名，后端匹配 player_id）
    content: str  # DM 私信内容
    trigger: Optional[str] = None  # 触发条件，如"玩家请求线索时"


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
    private_events: List[PrivateEvent] = Field(default_factory=list)


class Player(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    role_id: str
    role: Optional[Role] = None
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
    act: int = 1  # 1=背景介绍, 2=自由调查, 3=审判揭晓
    room_creator_id: str = ""  # 管理员ID（房间创建者）
    players: dict[str, Player]
    script: Script
    public_messages: List[Message] = Field(default_factory=list)
    private_messages: List[Message] = Field(default_factory=list)
    accusations: List[Accusation] = Field(default_factory=list)
    votes: List[Vote] = Field(default_factory=list)
    timer_start: datetime = Field(default_factory=datetime.now)
    max_duration_minutes: int = 60
    current_round: int = 0
    host_message_history: List[str] = Field(default_factory=list)
    dm_log: List[str] = Field(default_factory=list)  # LLM推理日志
    script_generated: bool = False  # 是否已生成剧本

    # Distribution cache: stores WS messages to resend on player (re)connect
    distributed_role_cards: dict[str, List[dict]] = Field(default_factory=dict)  # pid -> [{type, layer, data}, ...]
    distributed_clues: dict[str, List[dict]] = Field(default_factory=dict)  # pid -> [{type, clue}, ...]
    distributed_dm_private: dict[str, List[dict]] = Field(default_factory=dict)  # pid -> [{type, from, to, content}, ...]
