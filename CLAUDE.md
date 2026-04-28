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
server/          FastAPI backend (main.py, config, models, game_manager, websocket_hub, api_routes, host_dm, llm_client, middleware)
client/src/      Vue 3 frontend (App.vue, router.ts, stores/game.ts, types/ws.ts, utils/ws.ts [deprecated], 12 components)
shared/          ws_types.py — Pydantic schemas for WebSocket messages; schemas.ts — Zod schemas for frontend validation
tests/           pytest suite (test_game_manager.py, test_dm_chat_response.py, test_integration.py, conftest.py)
docs/            Design specs and implementation plans (docs/superpowers/)
```

## Key Architecture

- **GameManager** (server/game_manager.py): Singleton `manager` holds all game states in memory. Handles room lifecycle, player management, voting/consensus, phase transitions, distribution caching for WS reconnect.
- **WebSocketHub** (server/websocket_hub.py): Singleton `hub` manages WebSocket connections per room. Routes client messages (chat, private_chat, accuse, request_advance) to GameManager. `request_advance` uses `asyncio.to_thread()` for non-blocking LLM calls.
- **HostDM** (server/host_dm.py): Singleton `host` wraps LLMClient with a DM system prompt. Provides `generate_event()`, `respond_to_chat_stream()`, `respond_to_chat()` (blocking), and streaming script generation.
- **LLMClient** (server/llm_client.py): Synchronous OpenAI-compatible chat API client using `requests`. All methods are sync — must be wrapped in `asyncio.to_thread()` when called from async handlers (SSE generators are auto-wrapped by Starlette's threadpool).
- **API Routes** (server/api_routes.py): REST endpoints for room CRUD, script generation (admin-only, SSE streaming), game control, DM chat (SSE streaming), voting, chat, LLM config. Admin actions guarded by `require_admin()`.
- **Frontend Router**: `/` → RoomList, `/join/:gameId` → RoomJoin, `/lobby/:gameId` → WaitingLobby, `/game/:gameId` → GamePage.
- **Frontend State**: Pinia store `useGameStore` manages phase, act, messages, players, currentEvent, roleCard (3 layers), privateMessages, clues (Array), publicMessages (deduplicated via seenMessageKeys), activeTab. WebSocketManager (`utils/ws.ts`) is deprecated — `GamePage.vue` uses direct WebSocket connections with storeToRefs bidirectional sync.

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
```

## Configuration

- `.env` at project root: `LLM_ENDPOINT`, `LLM_MODEL`, `LLM_API_KEY`, `SERVER_HOST`, `SERVER_PORT`
- Runtime LLM config can be changed via `/api/llm-config` POST without restarting

## Game Flow

1. Admin creates room → `waiting` phase, placeholder script (no roles yet)
2. Players join → roles assigned after script generation (players can join before script is generated)
3. Admin triggers LLM script generation (SSE streaming) → full script with roles, clues, plot outline
4. Admin starts game → `playing` phase, act=1; unlocks act1 clues (default `unlock_phase` for new clues) + layer 2 role cards + private events
5. Admin advances to act 2 → unlocks act2 clues + layer 3 role cards + act2 private events
6. Players chat, request advance → LLM generates events/clues (WS `request_advance` uses `asyncio.to_thread`)
7. Players DM chat with DM → SSE streaming response, 30s rate limit per player
8. Accusations & votes → consensus (>=50% on same target) triggers reveal
9. Admin can advance-act, force-trial, end-game, kick players at any time

## Important Notes

- All game state is in-memory (no database). Restarting server clears all games.
- `server/game_manager.py` and `server/websocket_hub.py` use module-level singletons (`manager`, `hub`).
- **Distribution Cache**: GameState stores `distributed_role_cards`, `distributed_clues`, `distributed_dm_private` — used to resend on WS (re)connect via `get_pending_distributions()`. ALL WS messages containing private data MUST be cached here.
- **push_structured_event**: Private clues are cached in `distributed_dm_private` for WS reconnect resilience.
- **/dm/private endpoint**: Admin DM messages are stored in `private_messages` AND cached in `distributed_dm_private` for reconnect.
- **unlock_phase**: Uses `act_key = f"act{new_act}"` to look up layer_map. Layer map: act1→layer2, act2→layer3. Phase stays "playing" — acts 1/2 are within playing phase.
- **Clue defaults**: `_normalize_script_json` defaults `unlock_phase` to `"act1"` (not `"act2"`). Script generation prompt instructs LLM to spread clues across act1 (2-3) and act2 (3-5).
- **WS on_connect**: Resends phase_unlock, all cached distributions (role cards, clues, dm_private — deduplicated to avoid double-send), and last 50 public messages with resolved player names.
- **Chat**: `sendPublicChat` uses WS only — server handles persistence via `manager.add_chat_message`. WS broadcast includes `from_player_id` for deduplication.
- **DM Chat**: `POST /api/rooms/{gameId}/dm/chat-response` SSE streaming. Player's own message is immediately pushed to `store.privateMessages`. DM reply streamed via SSE, cached via `manager.add_dm_chat_response()`.
- **request_advance**: WS message, non-blocking via `asyncio.to_thread()`. Frontend shows `requestingClue` loading state, cleared when `event` WS message arrives or 15s timeout.
- **advance-act**: `POST /api/rooms/{gameId}/advance-act` admin endpoint. Calls `unlock_phase` with act+1, broadcasts `phase_unlock` and distributes new role cards, clues, and private events via WS.
- **get_room API**: `public_messages` includes `from_player_name` (resolved from player name or "__dm__" → "🎭 DM").
- **Deduplication**: Frontend store uses `seenMessageKeys` Set for public messages, `seenPrivateKeys` Set for DM private messages, and `clue.id` check for clue deduplication.
- Frontend `game.ts` store is comprehensive — handles role_card, dm_private, clue_unlock, phase_unlock, chat deduplication, and publicMessages loading from API.
- WebSocket endpoint path: `/ws/{room_id}/{player_id}`
- LLM calls use OpenAI `/v1/chat/completions` format with configurable endpoint/model/key.
- **SSE generators**: `_push_event_generator`, `_chat_response_generator`, `_generate_script_generator` are sync generators — Starlette auto-wraps them in a threadpool via `iterate_in_threadpool()`. They do NOT need explicit `asyncio.to_thread()`.
- **Async handlers**: Direct async endpoint functions (not SSE) that call sync LLM methods MUST use `asyncio.to_thread()` to avoid blocking the event loop. Currently `end_game` uses sync with `try/except` — should be migrated to SSE streaming.
- `.env` file at project root is used.

## Known Technical Debt

- **Blocking async calls**: `end_game`, `test_llm`, `list_llm_models` endpoints call sync LLM methods directly in async handlers. These should be migrated to SSE streaming or wrapped in `asyncio.to_thread()`. Blocked by `TestClient` incompatibility with `asyncio.to_thread`.
- **Missing UI feedback**: Many admin actions (handleForceTrial, handleEndGame, handleAddClue, submitAccusation, submitVote) lack loading states and error handling. See audit report for full list.
- **private_chat WS messages**: Not cached for reconnect. If a player disconnects, their private chat history is lost.
- **accusation WS messages**: Not cached or replayed on reconnect. Frontend store handler is a no-op.
