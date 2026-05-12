"""
WebSocket message models package.

New Pydantic v2 models that mirror Zod schemas for type consistency.
Also re-exports legacy models from server.models.py for backward compatibility.
"""

# Import legacy models directly from the models.py file (not the package)
# Use importlib.util to load the file directly, bypassing the package
import importlib.util
import os

_models_py_path = os.path.join(os.path.dirname(__file__), "..", "models.py")
_legacy_spec = importlib.util.spec_from_file_location("server.models_legacy", _models_py_path)
_legacy_models = importlib.util.module_from_spec(_legacy_spec)
_legacy_spec.loader.exec_module(_legacy_models)

Role = _legacy_models.Role
Clue = _legacy_models.Clue  # Legacy Clue (keep original name for backward compat)
PrivateEvent = _legacy_models.PrivateEvent
PlotOutline = _legacy_models.PlotOutline
Script = _legacy_models.Script
ScriptMetadata = _legacy_models.ScriptMetadata
ScriptDetail = _legacy_models.ScriptDetail
Player = _legacy_models.Player  # Legacy Player (keep original name for backward compat)
Message = _legacy_models.Message
Accusation = _legacy_models.Accusation
Vote = _legacy_models.Vote
GameState = _legacy_models.GameState  # Legacy GameState (keep original name for backward compat)

# New WebSocket message models
from .ws import (
    ChatMessage,
    Clue as WsClue,
    RoleCard,
    Player as WsPlayer,
    GameState as WsGameState,
    PhaseUnlock,
    ChatPhase,
    CluePhase,
    ClueType
)

__all__ = [
    # Legacy models (original names for backward compatibility)
    "Role",
    "Clue",
    "PrivateEvent",
    "PlotOutline",
    "Script",
    "ScriptMetadata",
    "ScriptDetail",
    "Player",
    "Message",
    "Accusation",
    "Vote",
    "GameState",
    # New WebSocket models (with Ws prefix to avoid conflict)
    "ChatMessage",
    "WsClue",
    "RoleCard",
    "WsPlayer",
    "WsGameState",
    "PhaseUnlock",
    "ChatPhase",
    "CluePhase",
    "ClueType"
]
