"""Server utility modules for shared functionality."""

from server.utils.endpoint import normalize_endpoint
from server.utils.display_name import resolve_display_name, resolve_display_name_for_message
from server.utils.validation import (
    sanitize_string,
    mask_api_key,
    MAX_PLAYER_NAME_LENGTH,
    MAX_CHAT_LENGTH,
    CreateRoomRequest,
    JoinRoomRequest,
    ChatRequest,
    AccusationRequest,
    VoteRequest,
    AdminActionRequest,
    PlayerLeaveRequest,
)

__all__ = [
    "normalize_endpoint",
    "resolve_display_name",
    "resolve_display_name_for_message",
    "sanitize_string",
    "mask_api_key",
    "MAX_PLAYER_NAME_LENGTH",
    "MAX_CHAT_LENGTH",
    "CreateRoomRequest",
    "JoinRoomRequest",
    "ChatRequest",
    "AccusationRequest",
    "VoteRequest",
    "AdminActionRequest",
    "PlayerLeaveRequest",
]
