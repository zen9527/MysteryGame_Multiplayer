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
client/src/      Vue 3 frontend (App.vue, router.ts, stores/game.ts, types/ws.ts, utils/ws.ts, 8 components)
shared/          ws_types.py — Pydantic schemas for WebSocket messages; schemas.ts — Zod schemas for frontend validation
tests/           pytest suite (test_game_manager.py, test_integration.py, conftest.py)
```

## Key Architecture

- **GameManager** (server/game_manager.py): Singleton `manager` holds all game states in memory. Handles room lifecycle, player management, voting/consensus, phase transitions.
- **WebSocketHub** (server/websocket_hub.py): Singleton `hub` manages WebSocket connections per room. Routes client messages (chat, private_chat, accuse, request_advance) to GameManager.
- **HostDM** (server/host_dm.py): Singleton `host` wraps LLMClient with a DM system prompt. Calls LLM to generate events based on game state context.
- **LLMClient** (server/llm_client.py): OpenAI-compatible chat API client. Reads config from `.env` but supports runtime overrides via `set_runtime_config()`.
- **API Routes** (server/api_routes.py): REST endpoints for room CRUD, script generation (admin-only), game control, voting, chat, LLM config. Admin actions guarded by `require_admin()`.
- **Frontend Router**: `/` → RoomList, `/join/:gameId` → RoomJoin, `/lobby/:gameId` → WaitingLobby, `/game/:gameId` → GamePage.
- **Frontend State**: Pinia store `useGameStore` manages phase, messages, players, currentEvent. WebSocketManager (`utils/ws.ts`) is unused — `GamePage.vue` uses direct WebSocket connections.

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
3. Admin triggers LLM script generation → full script with roles, clues, plot outline
4. Admin starts game → `playing` phase, act=1
5. Players chat, request advance → LLM generates events/clues
6. Accusations & votes → consensus (>=50% on same target) triggers reveal
7. Admin can force-trial, end-game, kick players at any time

## Important Notes

- All game state is in-memory (no database). Restarting server clears all games.
- `server/game_manager.py` and `server/websocket_hub.py` use module-level singletons (`manager`, `hub`).
- Frontend `game.ts` store is minimal — many WS message types have empty handlers (e.g., `chat`, `role_assigned`).
- WebSocket endpoint path: `/ws/{room_id}/{player_id}`
- LLM calls use OpenAI `/v1/chat/completions` format with configurable endpoint/model/key.
- `.env` file at project root is used.
