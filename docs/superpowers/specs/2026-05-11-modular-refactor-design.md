# Modular Refactor Design: LLM Provider, Script Engine, Game Engine

Date: 2026-05-11

## Goal

Refactor the monolithic LLM/DM layer into three independent modules:
1. **LLM Provider** — multi-format API adapter (OpenAI, Claude, Gemini)
2. **Script Engine** — enhanced script generation with richer output structures
3. **Game Engine** — autonomous DM that monitors and drives game progress

## 1. LLM Provider Layer (`server/llm/`)

### 1.1 Abstract Interface

```python
# server/llm/base.py
class LLMProvider(ABC):
    name: str  # unique identifier

    @abstractmethod
    def chat(self, messages: list[dict], temperature: float = 0.7, timeout: int = 120) -> str

    @abstractmethod
    def chat_stream(self, messages: list[dict], temperature: float = 0.7) -> Generator[str, None, None]

    @abstractmethod
    def list_models(self) -> list[str]

    @abstractmethod
    def test_connection(self) -> str

    def get_config(self) -> dict:
        """Return provider config summary (masked secrets)."""
        ...
```

### 1.2 Providers

| File | API Format | Base URL Pattern |
|------|-----------|-----------------|
| `openai_provider.py` | `/v1/chat/completions` | OpenAI, z.ai, local-ai, ollama, any compatible |
| `anthropic_provider.py` | `/v1/messages` | Anthropic Claude |
| `gemini_provider.py` | `/v1beta/models/{model}:generateContent` | Google Gemini |

Each provider:
- Handles auth headers per its API spec
- Implements streaming with provider-specific SSE parsing
- Has retry logic (inherited from current LLMClient)
- Connection timeout 10s, stream total timeout 300s

### 1.3 Registry

```python
# server/llm/registry.py
class LLMRegistry:
    providers: dict[str, LLMProvider]
    active_name: str

    def register(self, name: str, provider: LLMProvider) -> None
    def remove(self, name: str) -> None
    def set_active(self, name: str) -> None
    def get_active(self) -> LLMProvider
    def list_providers() -> list[dict]  # [{name, type, model, endpoint_masked, is_active}]
```

Active provider is used by all LLM consumers (script gen, game host, DM chat).
On startup, loads default from `.env` as the initial provider.

### 1.4 Admin API

Replace existing `/api/llm-config` with:

```
GET    /api/llm/providers              → list all providers + status
POST   /api/llm/providers              → add provider {name, type, endpoint, api_key?, model}
DELETE /api/llm/providers/{name}       → remove provider
POST   /api/llm/providers/active       → switch active {name}
POST   /api/llm/providers/{name}/test  → test connection
GET    /api/llm/providers/{name}/models → list available models
```

### 1.5 Migration from LLMClient

- `server/llm_client.py` → deleted
- All callers use `registry.get_active().chat()` or `registry.get_active().chat_stream()`
- `HostDM.llm` becomes `HostDM.llm_registry`
- DI container registers `LLMRegistry` instead of `LLMClient`
- `.env` LLM_ENDPOINT/LLM_MODEL/LLM_API_KEY create the default "local" provider at startup

## 2. Script Engine (`server/script_engine/`)

### 2.1 Enhanced Script Model

```python
# server/script_engine/models.py
class NPC(BaseModel):
    name: str
    age: int
    occupation: str
    description: str
    relationship_to_victim: str
    knows: list[str]

class TimelineEntry(BaseModel):
    time: str          # "21:30" or "案发前2小时"
    event: str
    witnesses: list[str]

class Relationship(BaseModel):
    from_role: str
    to_role: str
    relation: str
    tension: int = 0   # 0-10

class ScriptV2(Script):
    """Extended script model - backward compatible with original Script."""
    npcs: list[NPC] = []
    timeline: list[TimelineEntry] = []
    relationships: list[Relationship] = []
    atmosphere: str = ""
    key_questions: list[str] = []
```

`ScriptV2` extends `Script` (Pydantic inheritance) so existing code that reads `script.roles`, `script.clues` etc. continues to work unchanged.

### 2.2 Generator

```python
# server/script_engine/generator.py
class ScriptGenerator:
    def __init__(self, llm_registry: LLMRegistry)

    def generate(self, genre, difficulty, player_count, ...) -> ScriptV2
    def generate_stream(self, ...) -> Generator[str]
```

- Prompts moved out of `api/script.py` into `generator.py`
- Prompt includes instructions for new fields (NPCs, timeline, relationships)
- `_normalize_script_json()` moved here from `api/script.py`
- LLM prompt explicitly requests all new fields

### 2.3 Templates

```python
# server/script_engine/templates.py
GENRE_TEMPLATES = {
    "悬疑推理": { "atmosphere_hint": "封闭空间，暴风雪山庄模式...", ... },
    "古风权谋": { ... },
    ...
}
```

Templates provide genre-specific guidance to the LLM prompt for better output quality.

## 3. Game Engine (`server/game_engine/`)

### 3.1 Autonomous Game Host

```python
# server/game_engine/host.py
class GameHost:
    def __init__(self, llm_registry, game_manager, ws_hub)
```

Methods:
- `on_game_start(game_id)` — auto opening narrative + act 1 guidance
- `on_act_transition(game_id, act)` — inter-act narrative + distribute new content
- `on_player_idle(game_id)` — DM nudges when players are silent too long
- `on_accusation(game_id, ...)` — handle accusations, guide trial
- `on_end_game(game_id)` — truth reveal
- `_generate_event(game_id) -> dict` — core LLM event generation
- `_should_intervene(game_id) -> bool` — heuristic: check last activity time, current phase

Replaces `server/host_dm.py` entirely.

### 3.2 Scheduler

```python
# server/game_engine/scheduler.py
class GameScheduler:
    """Periodic monitor that triggers autonomous DM behavior."""
    _tasks: dict[str, asyncio.Task]  # game_id → monitor task

    def start(self, game_id)
    def stop(self, game_id)
    def _monitor_loop(self, game_id):
        # Every 30s:
        #   1. Check last player activity timestamp
        #   2. If idle > 60s in playing phase → host.on_player_idle()
        #   3. Check if phase progression is due
        #   4. Check if clue drops are needed
```

Started when game enters "playing" phase, stopped on "revealed"/"finished".

### 3.3 Prompt Management

```python
# server/game_engine/prompts.py
class DMPrompts:
    SYSTEM_EVENT: str      # Event generation system prompt
    SYSTEM_CHAT: str       # DM chat system prompt
    SYSTEM_REVEAL: str     # Truth reveal system prompt
    SYSTEM_OPENING: str    # Opening narrative system prompt

    @staticmethod
    def build_event_prompt(game_state) -> str
    @staticmethod
    def build_chat_prompt(game_state, player_id, message) -> str
```

All DM prompts extracted from `host_dm.py` into this single file.

### 3.4 Admin API Additions

```
POST /api/rooms/{id}/dm/toggle-auto   → {auto: bool} enable/disable autonomous mode
GET  /api/rooms/{id}/dm/status        → {auto, last_intervention, idle_seconds, ...}
```

When `auto=false`, DM reverts to manual-only (current behavior). Default is `auto=true`.

### 3.5 GameState Extension

Add to `GameState`:
```python
dm_auto: bool = True                          # autonomous mode toggle
last_player_activity: datetime                 # for idle detection
dm_intervention_history: list[dict] = []       # track DM interventions
```

## 4. Migration Plan

### Phase 1: LLM Provider Layer
1. Create `server/llm/` package with base, providers, registry
2. Update DI container to register `LLMRegistry`
3. Update `server/api/config.py` for new provider management API
4. Update `host_dm.py` and `api/script.py` to use registry
5. Delete `server/llm_client.py`
6. Tests for each provider + registry

### Phase 2: Script Engine
1. Create `server/script_engine/` with enhanced models and generator
2. Move prompt logic from `api/script.py` to `generator.py`
3. Update `api/script.py` to use `ScriptGenerator`
4. Update `GameManager.set_script()` to handle `ScriptV2`
5. Tests for generator + model validation

### Phase 3: Game Engine
1. Create `server/game_engine/` with host, scheduler, prompts
2. Replace `host_dm.py` with `GameHost`
3. Add `GameScheduler` integration in game start/stop flow
4. Add admin toggle API
5. Update WebSocket handlers to notify `GameHost` of player activity
6. Tests for host decisions + scheduler timing

### Phase 4: Cleanup
1. Delete `server/host_dm.py`
2. Delete `server/llm_client.py`
3. Update DI container registrations
4. Update CLAUDE.md documentation
5. Full integration test suite

## 5. File Map After Refactor

```
server/
  llm/
    __init__.py
    base.py                 # LLMProvider ABC
    openai_provider.py      # OpenAI-compatible provider
    anthropic_provider.py   # Claude provider
    gemini_provider.py      # Gemini provider
    registry.py             # Multi-provider management
  script_engine/
    __init__.py
    models.py               # ScriptV2, NPC, Timeline, Relationship
    generator.py            # Script generation logic + prompts
    templates.py            # Genre/difficulty templates
  game_engine/
    __init__.py
    host.py                 # GameHost — autonomous DM
    scheduler.py            # GameScheduler — periodic monitoring
    prompts.py              # DM prompt templates
  game_manager.py           # State layer (unchanged)
  websocket_hub.py          # Transport layer (minor updates)
  models.py                 # Core models (unchanged)
  config.py                 # Config (unchanged)
  constants.py              # Constants (unchanged)
  middleware.py             # Middleware (unchanged)
  di/
    container.py            # Updated registrations
  api/
    __init__.py
    rooms.py                # Room lifecycle (unchanged)
    game.py                 # Updated to use GameHost
    script.py               # Updated to use ScriptGenerator
    dm.py                   # Updated to use GameHost
    config.py               → llm.py (renamed, provider management)
    voting.py, chat.py, scripts.py  # Unchanged
  main.py                   # Updated lifespan
```

## 6. Risk Mitigation

- **Backward compatibility**: `ScriptV2` extends `Script` so all existing code works
- **Incremental rollout**: Each phase is independently testable and deployable
- **Fallback**: Admin can toggle `auto=false` to revert to manual DM at any time
- **Default provider**: `.env` config auto-creates default provider on startup
