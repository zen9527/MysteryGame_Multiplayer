# Architecture Overview

## Backend Architecture

The backend is a FastAPI application with a modular structure centered around a dependency injection container.

### Core Layers

```
server/
├── main.py              FastAPI app entrypoint
├── config.py            Environment configuration (LLM, server, SCRIPT_ADMIN_KEY)
├── models.py            Pydantic data models (Script, Role, Clue, GameState, etc.)
├── constants.py         Shared constants (MAX_PLAYERS, CONSENSUS_THRESHOLD, etc.)
├── middleware.py         CORS + admin auth (require_admin)
├── di/
│   ├── container.py     DI container (service registry + resolver)
│   └── __init__.py      Exports container, register_services
├── api/
│   ├── __init__.py      Aggregates all API routers
│   ├── rooms.py         Room CRUD + player management
│   ├── game.py          Game lifecycle (start, advance-act, end-game)
│   ├── script.py        Script generation (SSE streaming)
│   ├── scripts.py       Script repository CRUD (admin key protected)
│   ├── dm.py            DM interactions (chat, private messages, log, add-clue)
│   ├── chat.py          REST chat + message history
│   ├── voting.py        Accusations and votes (with phase guard + dedup)
│   └── llm.py           Multi-provider LLM config, health check
├── llm/
│   ├── base.py          LLMProvider ABC
│   ├── openai_provider.py   OpenAI-compatible provider
│   ├── anthropic_provider.py Anthropic provider
│   ├── gemini_provider.py   Gemini provider
│   └── registry.py      LLMRegistry (multi-provider management)
├── script_engine/
│   ├── models.py        ScriptV2 model (extends Script with NPCs, timeline, etc.)
│   ├── templates.py     6 genre templates
│   └── generator.py     ScriptGenerator (LLM prompt → ScriptV2)
├── game_engine/
│   ├── prompts.py       DMPrompts (5 system prompts)
│   ├── host.py          GameHost (event/chat/reveal/opening generation)
│   └── scheduler.py     GameScheduler (auto-DM idle monitoring)
├── utils/
│   ├── display_name.py  Player name resolution (角色名(玩家名) format)
│   ├── endpoint.py      LLM endpoint URL normalization
│   └── validation.py    Request validation + sanitization
├── game_manager.py      GameManager — in-memory game state (thread-safe)
└── websocket_hub.py     WebSocketHub — WS connection routing + broadcast
```

### Dependency Injection

The DI container (`server/di/container.py`) registers core services at startup:

```python
container.register("llm_registry", lambda: LLMRegistry(...), singleton=True)
container.register("game_manager", lambda: GameManager(), singleton=True)
container.register("websocket_hub", lambda: WebSocketHub(), singleton=True)
container.register("script_generator", lambda: ScriptGenerator(...), singleton=True)
container.register("game_host", lambda: GameHost(...), singleton=True)
container.register("game_scheduler", lambda: GameScheduler(...), singleton=True)
```

API modules resolve services via `container.resolve("service_name")`. This enables:
- **Testability**: Tests can override services with mocks via `container.register()`
- **Decoupling**: API modules don't import singletons directly
- **Single source of truth**: All service wiring in one place

### Request Flow

```
HTTP Request → FastAPI Router → API Module → container.resolve("game_manager") → GameManager
                                                       ↓
                                             container.resolve("game_host") → GameHost → LLMRegistry → Provider
```

## Frontend Architecture

### Component Structure

```
client/src/
├── components/
│   ├── GamePage.vue           Main game page (WebSocket + storeToRefs)
│   ├── RoomList.vue           Room listing + create
│   ├── RoomCreate.vue         Room creation with script selection
│   ├── RoomJoin.vue           Join room form
│   ├── WaitingLobby.vue       Pre-game lobby (LLM config, script gen, player list)
│   ├── AdminPanel.vue         Admin controls (push event, advance act, etc.)
│   ├── ScriptEditor.vue       Script editing/preview
│   ├── RoleCard.vue           Role card display (3 layers)
│   ├── ClueCardPanel.vue      Clue panel
│   ├── PrivateChatPanel.vue   DM private chat (SSE streaming)
│   ├── GameTimer.vue          Game timer countdown
│   ├── game/                  (Unused scaffold components)
│   └── admin/                 (Unused scaffold components)
├── pages/
│   └── RoomCreate.vue         Room creation page
├── composables/
│   └── useSSE.ts              SSE streaming with loading/error state
├── stores/
│   └── game.ts                Pinia store (all game state + WS message handler)
├── utils/
│   ├── ws.ts                  WebSocketManager (unused — GamePage uses native WS)
│   ├── sse.ts                 SSE stream consumer utility
│   └── schema-validation.ts   Zod validation (unused)
├── types/
│   ├── ws.ts                  TypeScript WS message types
│   └── script.ts              Script metadata types
├── constants.ts               Frontend constants (timeouts, intervals)
└── router.ts                  Vue Router (4 routes)
```

### State Management

- **Pinia store** (`stores/game.ts`): Single source of truth for game state
- Uses `storeToRefs` for reactive destructuring in components
- Handles deduplication via `seenMessageKeys` (public messages), `seenPrivateKeys` (DM private), `clue.id` checks (clues)
- `handleWSMessage()` routes all WS message types to correct state updates

### Composables

| Composable | Purpose |
|---|---|
| `useSSE()` | Manages SSE streaming, exposes `fetchSSE(url, options)`, tracks `isLoading`, `content`, `error` |

Note: `useWebSocket` and `useGameActions` were removed during cleanup. GamePage.vue manages WebSocket connections directly using native `WebSocket` API. Admin/player actions are handled inline in components.

## Data Flow

### WebSocket Flow

```
Client connects → /ws/{room_id}/{player_id}
                         ↓
              Server validates player exists in room
                         ↓
              WebSocketHub.connect()
                         ↓
              Send cached state (phase, role cards, clues, DM private, accusations, votes, last 50 messages)
                         ↓
              Message loop: receive JSON → handle_client_message()
                         ↓
              ┌─────────────────────────────────────┐
              │ chat        → broadcast to room      │
              │ private_chat → send to sender+target │
              │               (validates receiver)   │
              │ accuse      → broadcast + cache      │
              │ vote        → add_vote + cache +     │
              │               broadcast vote_cast    │
              │ request_advance → asyncio.to_thread( │
              │   game_host.generate_event)          │
              │   → broadcast public event           │
              │   → send_dm_private per clue         │
              └─────────────────────────────────────┘
```

### SSE Flow

```
Client POST → API endpoint (e.g., /generate-script)
                         ↓
              StreamingResponse(sync_generator)
                         ↓
              Starlette auto-wraps in threadpool
                         ↓
              Generator yields: data: {"type": "start"}
                                data: {"type": "chunk", "content": "..."}
                                data: {"type": "done", ...}
                         ↓
              Client reads response.body stream (getReader)
```

## Key Design Decisions

1. **DI Container for Testability**: Services are registered in a central container rather than using module-level singletons throughout. API modules resolve dependencies through the container, allowing tests to inject mocks.

2. **Modular API Routes**: Split from a single `api_routes.py` into domain-specific modules (`rooms`, `game`, `script`, `scripts`, `dm`, `chat`, `voting`, `llm`). Each module is self-contained with its own request models and service resolution.

3. **Shared Utilities**: Common helpers (`display_name`, `endpoint normalization`, `validation/sanitization`) extracted to `server/utils/` to avoid duplication between modules.

4. **Multi-Provider LLM**: LLM providers abstracted behind `LLMProvider` ABC with `LLMRegistry` managing runtime provider switching without server restart.

5. **Component Organization**: GamePage.vue implements all game functionality inline (chat, accusations, votes, admin controls). The `game/` and `admin/` component directories are unused scaffolds.

6. **Sync LLM Client**: LLM providers are deliberately synchronous. Async compatibility is handled by wrapping calls in `asyncio.to_thread()` (for WS handlers) or relying on Starlette's automatic threadpool wrapping (for SSE generators).

7. **Distribution Cache for Reconnect Resilience**: All private data (role cards, clues, DM messages, accusations, votes, private chats) is cached in `GameState` so it can be re-sent when a player's WebSocket reconnects.

8. **Thread-Safe State Management**: GameManager uses `threading.RLock` per game for all state mutations. Public methods like `update_activity()` and `increment_round()` ensure atomic state changes.
