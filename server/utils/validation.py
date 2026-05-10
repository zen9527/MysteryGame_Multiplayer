import re
from pydantic import BaseModel, Field
from typing import Optional

MAX_PLAYER_NAME_LENGTH = 20
MAX_CHAT_LENGTH = 500
MAX_REASONING_LENGTH = 1000


def sanitize_string(value: str) -> str:
    value = re.sub(r'<[^>]*>', '', value)
    return value.strip()


def mask_api_key(key: str) -> str:
    if not key or len(key) < 8:
        return '***'
    return f'{key[:4]}...{key[-4:]}'


class CreateRoomRequest(BaseModel):
    creator_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(default="管理员", min_length=1, max_length=MAX_PLAYER_NAME_LENGTH)
    script_id: Optional[str] = None


class JoinRoomRequest(BaseModel):
    player_id: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=MAX_PLAYER_NAME_LENGTH)


class ChatRequest(BaseModel):
    player_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1, max_length=MAX_CHAT_LENGTH)
    is_private: bool = False
    target_player_id: Optional[str] = None


class AccusationRequest(BaseModel):
    from_player_id: str = Field(..., min_length=1)
    target_role_name: str = Field(..., min_length=1, max_length=50)
    reasoning: str = Field(..., min_length=1, max_length=MAX_REASONING_LENGTH)


class VoteRequest(BaseModel):
    from_player_id: str = Field(..., min_length=1)
    target_role_name: str = Field(..., min_length=1, max_length=50)
    reasoning: str = Field(..., min_length=1, max_length=MAX_REASONING_LENGTH)


class AdminActionRequest(BaseModel):
    player_id: str = Field(..., min_length=1, max_length=50)


class PlayerLeaveRequest(BaseModel):
    player_id: str = Field(..., min_length=1, max_length=50)
