import json
import logging
from typing import Generator
from datetime import datetime

from server.models import GameState
from server.game_engine.prompts import DMPrompts

log = logging.getLogger(__name__)


class GameHost:
    def __init__(self, llm_registry, game_manager, ws_hub):
        self._registry = llm_registry
        self._manager = game_manager
        self._hub = ws_hub

    @staticmethod
    def parse_event_response(raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            log.warning(f"[GameHost] JSON parse failed: {e}")
            return {"public_event": raw, "private_clues": [], "dm_instruction": ""}
        return {
            "public_event": data.get("public_event", ""),
            "private_clues": data.get("private_clues", []),
            "dm_instruction": data.get("dm_instruction", ""),
        }

    def generate_event(self, game_state: GameState) -> dict:
        messages = [{"role": "system", "content": DMPrompts.SYSTEM_EVENT}]
        for msg in game_state.host_message_history[-10:]:
            messages.append({"role": "assistant", "content": msg})
        messages.append({"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)})

        raw = self._registry.get_active().chat(messages, temperature=0.8, timeout=300)
        return self.parse_event_response(raw)

    def generate_opening(self, game_state: GameState) -> dict:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_OPENING},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        raw = self._registry.get_active().chat(messages, temperature=0.8, timeout=300)
        return self.parse_event_response(raw)

    def generate_idle_nudge(self, game_state: GameState) -> dict:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_IDLE_NUDGE},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        raw = self._registry.get_active().chat(messages, temperature=0.7, timeout=120)
        return self.parse_event_response(raw)

    def respond_to_chat(self, game_state: GameState, player_id: str, player_message: str) -> str:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_CHAT},
            {"role": "user", "content": DMPrompts.build_chat_user_prompt(game_state, player_id, player_message)},
        ]
        full_reply = ""
        for chunk in self._registry.get_active().chat_stream(messages, temperature=0.8):
            full_reply += chunk
        return full_reply

    def respond_to_chat_stream(self, game_state: GameState, player_id: str, player_message: str) -> Generator[str, None, None]:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_CHAT},
            {"role": "user", "content": DMPrompts.build_chat_user_prompt(game_state, player_id, player_message)},
        ]
        yield from self._registry.get_active().chat_stream(messages, temperature=0.8)

    def generate_reveal(self, game_state: GameState) -> str:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_REVEAL},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        return self._registry.get_active().chat(messages, temperature=0.7, timeout=300)

    def should_intervene(self, game_state: GameState) -> bool:
        if not game_state.dm_auto:
            return False
        if game_state.phase != "playing":
            return False
        if game_state.last_player_activity:
            idle_seconds = (datetime.now() - game_state.last_player_activity).total_seconds()
            return idle_seconds > 60
        return False
