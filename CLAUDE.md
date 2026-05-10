# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

剧本杀 (Script Murder) — an LLM-driven multiplayer online murder mystery game. FastAPI backend + Vue 3 frontend, with WebSocket real-time communication. A local LLM acts as the DM (Dungeon Master) host, auto-generating scripts, roles, clues, and guiding the game flow.

## Tech Stack

- **Backend**: FastAPI, Pydantic v2, uvicorn, python-dotenv, requests (OpenAI-compatible LLM API)
- **Frontend**: Vue 3 + TypeScript, Vite (port 3000), Pinia, Vue Router, Vitest
- **Shared**: Pydantic models (`server/models.py`) and `shared/ws_types.py` define the contract; frontend has matching Zod schemas in `shared/schemas.ts`

## Directory Structure

```
server/
  main.py           FastAPI app entrypoint, registers DI and middleware
  config.py         Environment config (LLM_ENDPOINT, LLM_MODEL, etc.)
  models.py         Pydantic models (Script, Role, Clue, GameState, etc.)
  game_manager.py   GameManager — in-memory game state management
  websocket_hub.py  WebSocketHub — WS connection routing and broadcast
  host_dm.py        HostDM — LLM-powered DM host
  llm_client.py     LLMClient — sync OpenAI-compatible chat API client
  middleware.py     CORS middleware and require_admin guard
  api/              Modular API routes (rooms, game, script, dm, chat, voting, config)
  di/               Dependency injection container
  utils/            Shared utilities (display_name, endpoint normalization)
client/src/
  App.vue, router.ts, main.ts
  stores/game.ts    Pinia store for all game state
  types/ws.ts       TypeScript WebSocket message types
  utils/ws.ts       WebSocketManager (used by useWebSocket composable)
  utils/sse.ts      SSE stream consumer
  composables/      useWebSocket, useSSE, useGameActions
  components/       Top-level page components (GamePage, RoomList, RoomJoin, WaitingLobby, etc.)
  components/game/  In-game components (AccusationPanel, EventDisplay, PlayerList, PublicChatPanel, VotePanel)
  components/admin/ Admin components (AdminConsole, DmLogViewer, ScriptPreview)
shared/
  ws_types.py       Pydantic schemas for WebSocket messages
  schemas.ts        Zod schemas for frontend validation
tests/
  conftest.py, test_game_manager.py, test_dm_chat_response.py, test_integration.py
  test_api_rooms.py, test_api_game.py, test_api_dm.py, test_api_config.py
  test_websocket_hub.py
docs/
  superpowers/      Design specs and implementation plans
  architecture.md   Architecture overview
  api-reference.md  API endpoint reference
```

## Key Architecture

- **DI Container** (`server/di/container.py`): Registers all core services (LLMClient, GameManager, WebSocketHub, HostDM) as singletons. API modules resolve dependencies via `container.resolve("service_name")`. Enables testability by allowing service overrides.
- **GameManager** (`server/game_manager.py`): Holds all game states in memory. Handles room lifecycle, player management, voting/consensus, phase transitions, distribution caching for WS reconnect.
- **WebSocketHub** (`server/websocket_hub.py`): Manages WebSocket connections per room. Routes client messages (chat, private_chat, accuse, request_advance) to GameManager. `request_advance` uses `asyncio.to_thread()` for non-blocking LLM calls.
- **HostDM** (`server/host_dm.py`): Wraps LLMClient with a DM system prompt. Provides `generate_event()`, `respond_to_chat_stream()`, `respond_to_chat()` (blocking), and streaming script generation.
- **LLMClient** (`server/llm_client.py`): Synchronous OpenAI-compatible chat API client using `requests`. All methods are sync — must be wrapped in `asyncio.to_thread()` when called from async handlers (SSE generators are auto-wrapped by Starlette's threadpool).
- **API Routes** (`server/api/`): Modular REST endpoints split into domain routers (rooms, game, script, dm, chat, voting, config). All included via `server/api/__init__.py`. Admin actions guarded by `require_admin()`. Uses `run_in_threadpool` for sync LLM calls in async handlers.
- **Shared Utilities** (`server/utils/`): `display_name.py` provides `resolve_display_name()` and `resolve_display_name_for_message()` for consistent player name resolution. `endpoint.py` provides `normalize_endpoint()` for LLM URL normalization.
- **Frontend Router**: `/` → RoomList, `/join/:gameId` → RoomJoin, `/lobby/:gameId` → WaitingLobby, `/game/:gameId` → GamePage.
- **Frontend State**: Pinia store `useGameStore` manages phase, act, messages, players, currentEvent, roleCard (3 layers), privateMessages, clues (Array), publicMessages (deduplicated via seenMessageKeys), activeTab, actBanner (auto-dismiss).
- **Frontend Composables**: `useWebSocket` manages WS connection via WebSocketManager, `useSSE` manages SSE streaming with loading/error state, `useGameActions` wraps store actions for admin and player operations with storeToRefs.

## Development Commands

```bash
# Backend
pip install -r requirements.txt
uvicorn server.main:app --host 0.0.0.0 --port 8000

# Frontend
cd client && npm install
npm run dev        # Vite dev server (port 3000)
npm run build      # vue-tsc + vite build
npm test           # vitest run

# Tests
pytest tests/ -v   # Backend tests (project root is in sys.path via conftest.py)

# Quick Start
.\start.ps1   # Start both servers
.\stop.ps1    # Stop both servers
```

## Configuration

- `.env` at project root: `LLM_ENDPOINT`, `LLM_MODEL`, `LLM_API_KEY`, `SERVER_HOST`, `SERVER_PORT`
- Runtime LLM config can be changed via `/api/llm-config` POST without restarting

## Game Flow

1. Admin creates room → `waiting` phase, placeholder script (no roles yet)
2. Players join → roles assigned after script generation (players can join before script is generated)
3. Admin triggers LLM script generation (SSE streaming) → full script with roles, clues, plot outline
4. Admin starts game → `playing` phase, act=1; unlocks act1 clues (default `unlock_phase` for new clues) + layer 2 role cards + private events; DM auto-generates opening narrative via background task
5. Admin advances to act 2 → unlocks act2 clues + layer 3 role cards + act2 private events; broadcasts `act_transition` with plot outline
6. Players chat, request advance → LLM generates events/clues (WS `request_advance` uses `asyncio.to_thread`)
7. Players DM chat with DM → SSE streaming response, 30s rate limit per player
8. Accusations & votes → broadcast via WS (`accusation`, `vote_cast`); cached for reconnect; consensus (>=50% on same target) triggers reveal
9. Admin can advance-act, force-trial, end-game (SSE streaming), kick players at any time; all admin actions have loading states and error feedback

## Important Notes

- All game state is in-memory (no database). Restarting server clears all games.
- **DI Container**: Services registered in `server/di/container.py` via `register_services()`. API modules use `container.resolve()` to get service instances. Singletons are cached for the process lifetime.
- `server/websocket_hub.py` still uses module-level `hub` singleton directly (legacy). API modules use DI container.
- **Distribution Cache**: GameState stores `distributed_role_cards`, `distributed_clues`, `distributed_dm_private`, `distributed_accusations`, `distributed_private_chat` — used to resend on WS (re)connect via `get_pending_distributions()`. ALL WS messages containing private data MUST be cached here.
- **push_structured_event**: Private clues are cached in `distributed_dm_private` for WS reconnect resilience.
- **/dm/private endpoint**: Admin DM messages are stored in `private_messages` AND cached in `distributed_dm_private` for reconnect.
- **unlock_phase**: Uses `act_key = f"act{new_act}"` to look up layer_map. Layer map: act1→layer2, act2→layer3. Phase stays "playing" — acts 1/2 are within playing phase.
- **Clue defaults**: `_normalize_script_json` (in `server/api/script.py`) defaults `unlock_phase` to `"act1"` (not `"act2"`). Script generation prompt instructs LLM to spread clues across act1 (2-3) and act2 (3-5).
- **WS on_connect**: Resends phase_unlock, all cached distributions (role cards, clues, dm_private, accusations — deduplicated to avoid double-send), and last 50 public messages with resolved player names.
- **Chat display**: Chat messages show `角色名(玩家名)` format (e.g., "林默(张三)"). DM messages show "🎭 DM". Resolved by `resolve_display_name()` in `server/utils/display_name.py` and `_resolve_display_name()` in `server/websocket_hub.py`.
- **Chat**: `sendPublicChat` uses WS only — server handles persistence via `manager.add_chat_message`. WS broadcast includes `from_player_id` for deduplication.
- **Private chat**: `private_chat` WS messages are cached in `distributed_private_chat` for WS reconnect resilience. Both sender and receiver get cached copy via `manager.cache_private_chat()`.
- **DM auto-opening**: `start_game` triggers `asyncio.create_task(_auto_generate_opening)` background task (in `server/api/game.py`). DM opening narrative arrives via WS broadcast after LLM generation (10-30s). No frontend changes needed.
- **DM Chat**: `POST /api/rooms/{gameId}/dm/chat-response` SSE streaming. Player's own message is immediately pushed to `store.privateMessages`. DM reply streamed via SSE, cached via `manager.add_dm_chat_response()`.
- **request_advance**: WS message, non-blocking via `asyncio.to_thread()`. Frontend shows `requestingClue` loading state, cleared when `event` WS message arrives or 15s timeout.
- **advance-act**: `POST /api/rooms/{gameId}/advance-act` admin endpoint. Calls `unlock_phase` with act+1, broadcasts `phase_unlock` and distributes new role cards, clues, and private events via WS.
- **get_room API**: `public_messages` includes `from_player_name` (resolved from player name or "__dm__" → "🎭 DM").
- **Deduplication**: Frontend store uses `seenMessageKeys` Set for public messages, `seenPrivateKeys` Set for DM private messages, and `clue.id` check for clue deduplication.
- Frontend `game.ts` store is comprehensive — handles role_card, dm_private, clue_unlock, phase_unlock, chat deduplication, and publicMessages loading from API.
- WebSocket endpoint path: `/ws/{room_id}/{player_id}`
- LLM calls use OpenAI `/v1/chat/completions` format with configurable endpoint/model/key.
- **SSE generators**: `_push_event_generator`, `_chat_response_generator`, `_generate_script_generator`, `_end_game_generator` are sync generators — Starlette auto-wraps them in a threadpool via `iterate_in_threadpool()`. They do NOT need explicit `asyncio.to_thread()`.
- **Async handlers**: Direct async endpoint functions (not SSE) that call sync LLM methods MUST use `run_in_threadpool()` (from starlette.concurrency) to avoid blocking the event loop. Compatible with FastAPI's TestClient.
- `.env` file at project root is used.

## Known Technical Debt

- `server/websocket_hub.py` still imports `manager` and `host` as module-level singletons instead of using DI container.
- `server/middleware.py` still imports `manager` directly for `require_admin()` instead of using DI container.
- **Unused game/ and admin/ components**: `client/src/components/game/` (AccusationPanel, EventDisplay, PlayerList, PublicChatPanel, VotePanel) and `client/src/components/admin/` (AdminConsole, DmLogViewer, ScriptPreview) are scaffold components that are NOT used by GamePage.vue. GamePage.vue implements all functionality inline. These components call `useGameActions()` which delegates to store stub actions (console.log only). Do NOT rely on these components for production behavior.
- **Store actions are stubs**: `game.ts` store methods `startGame`, `advanceAct`, `forceTrial`, `endGame`, `sendPublicChat`, `submitAccusation`, `castVote`, `requestAdvance` only log to console. GamePage.vue handles all actions directly via fetch/WebSocket. The `useGameActions` composable wraps these stubs.
- **ScriptPreview.vue** is completely unimplemented (`<p>剧本功能待实现...</p>`).
- **shared/ws_types.py** is declarative only — Pydantic schemas are defined but not used for WS message validation. The actual WS message format is defined by the server-side code in `websocket_hub.py`.
- **shared/schemas.ts** duplicates types from `client/src/types/ws.ts` with inconsistencies (missing `player_id` fields). Frontend uses `client/src/types/ws.ts`, not `shared/schemas.ts`.
- **Consensus threshold**: `check_consensus()` uses `>=` with threshold 0.5, meaning in a 2-player game, 1 vote (50%) triggers consensus. Consider whether strict majority (>50%) is intended.
- **ChatPanel.vue** exists but is unused (replaced by `PublicChatPanel.vue`).
