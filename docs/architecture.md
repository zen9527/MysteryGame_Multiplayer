# Architecture Overview

## Backend Architecture

The backend is a FastAPI application with a modular structure centered around a dependency injection container.

### Core Layers

```
server/
├── main.py              FastAPI app entrypoint
├── config.py            Environment configuration
├── models.py            Pydantic data models
├── middleware.py         CORS + admin auth
├── di/
│   ├── container.py     DI container (service registry + resolver)
│   └── __init__.py      Exports container, register_services
├── api/
│   ├── __init__.py      Aggregates all API routers
│   ├── rooms.py         Room CRUD + player management
│   ├── game.py          Game lifecycle (start, advance-act, end-game)
│   ├── script.py        Script generation (SSE streaming)
│   ├── dm.py            DM interactions (chat, private messages, log)
│   ├── chat.py          REST chat (supplementary to WS chat)
│   ├── voting.py        Accusations and votes
│   └── config.py        LLM config, health check, model listing
├── utils/
│   ├── display_name.py  Player name resolution (角色名(玩家名) format)
│   └── endpoint.py      LLM endpoint URL normalization
├── game_manager.py      In-memory game state management
├── websocket_hub.py     WebSocket connection hub
├── host_dm.py           LLM-powered DM host
└── llm_client.py        OpenAI-compatible API client
```

### Dependency Injection

The DI container (`server/di/container.py`) registers core services at startup:

```python
container.register("llm_client", LLMClient)
container.register("game_manager", GameManager, singleton=True)
container.register("websocket_hub", WebSocketHub, singleton=True)
container.register("host_dm", lambda: HostDM(container.resolve("llm_client")), singleton=True)
```

API modules resolve services via `container.resolve("service_name")`. This enables:
- **Testability**: Tests can override services with mocks via `container.register()`
- **Decoupling**: API modules don't import singletons directly
- **Single source of truth**: All service wiring in one place

### Request Flow

```
HTTP Request → FastAPI Router → API Module → container.resolve("game_manager") → GameManager
                                                        ↓
                                              container.resolve("host_dm") → HostDM → LLMClient
```

## Frontend Architecture

### Component Structure

```
client/src/
├── components/
│   ├── GamePage.vue           Main game page (WebSocket + storeToRefs)
│   ├── RoomList.vue           Room listing
│   ├── RoomJoin.vue           Join room form
│   ├── WaitingLobby.vue       Pre-game lobby
│   ├── AdminPanel.vue         Admin controls
│   ├── ScriptEditor.vue       Script editing
│   ├── RoleCard.vue           Role card display
│   ├── ClueCardPanel.vue      Clue panel
│   ├── PrivateChatPanel.vue   DM private chat
│   ├── GameTimer.vue          Game timer
│   ├── game/                  In-game subcomponents
│   │   ├── AccusationPanel.vue
│   │   ├── EventDisplay.vue
│   │   ├── PlayerList.vue
│   │   ├── PublicChatPanel.vue
│   │   └── VotePanel.vue
│   └── admin/                 Admin subcomponents
│       ├── AdminConsole.vue
│       ├── DmLogViewer.vue
│       └── ScriptPreview.vue
├── composables/
│   ├── useWebSocket.ts        WS connection management + auto-reconnect
│   ├── useSSE.ts              SSE streaming with loading/error state
│   └── useGameActions.ts      Game action wrappers (admin + player)
├── stores/
│   └── game.ts                Pinia store (all game state)
├── utils/
│   ├── ws.ts                  WebSocketManager class
│   └── sse.ts                 SSE stream consumer
├── types/
│   └── ws.ts                  TypeScript WS message types
└── router.ts                  Vue Router (4 routes)
```

### State Management

- **Pinia store** (`stores/game.ts`): Single source of truth for game state
- Uses `storeToRefs` for reactive destructuring in components
- Handles deduplication via `seenMessageKeys`, `seenPrivateKeys`, `clue.id` checks

### Composables

| Composable | Purpose |
|---|---|
| `useWebSocket(roomId, playerId)` | Manages WS connection with auto-reconnect, exposes `connect()`, `send()`, `disconnect()` |
| `useSSE()` | Manages SSE streaming, exposes `fetchSSE(url, options)`, tracks `isLoading`, `content`, `error` |
| `useGameActions()` | Wraps store actions for admin (startGame, advanceAct, forceTrial, endGame) and player (sendChat, submitAccusation, castVote, requestAdvance) |

## Data Flow

### WebSocket Flow

```
Client connects → /ws/{room_id}/{player_id}
                         ↓
              WebSocketHub.connect()
                         ↓
              Send cached state (phase, role cards, clues, DM private, accusations, last 50 messages)
                         ↓
              Message loop: receive JSON → handle_client_message()
                         ↓
              ┌─────────────────────────────────────┐
              │ chat        → broadcast to room      │
              │ private_chat → send to sender+target │
              │ accuse      → broadcast + cache      │
              │ vote        → broadcast              │
              │ request_advance → asyncio.to_thread( │
              │   host_dm.generate_event)            │
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
              Client useSSE().fetchSSE() consumes stream
```

## Key Design Decisions

1. **DI Container for Testability**: Services are registered in a central container rather than using module-level singletons throughout. API modules resolve dependencies through the container, allowing tests to inject mocks.

2. **Modular API Routes**: Split from a single `api_routes.py` into domain-specific modules (`rooms`, `game`, `script`, `dm`, `chat`, `voting`, `config`). Each module is self-contained with its own request models and service resolution.

3. **Shared Utilities**: Common helpers (`display_name`, `endpoint normalization`) extracted to `server/utils/` to avoid duplication between modules.

4. **Composables for Reusable Logic**: Frontend logic extracted into Vue composables (`useWebSocket`, `useSSE`, `useGameActions`) to separate concerns and enable reuse across components.

5. **Component Organization**: In-game and admin components organized into `components/game/` and `components/admin/` subdirectories for better discoverability.

6. **Sync LLM Client**: The LLM client is deliberately synchronous (using `requests`). Async compatibility is handled by wrapping calls in `asyncio.to_thread()` (for WS handlers) or relying on Starlette's automatic threadpool wrapping (for SSE generators).

7. **Distribution Cache for Reconnect Resilience**: All private data (role cards, clues, DM messages, accusations) is cached in `GameState` so it can be re-sent when a player's WebSocket reconnects.
