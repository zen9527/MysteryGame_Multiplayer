# API Reference

All REST endpoints are prefixed with `/api` (set via `include_router(api_router, prefix="/api")` in `main.py`). The WebSocket endpoint is at the root level.

---

## Rooms API (`server/api/rooms.py`)

### `POST /rooms`
Create a new game room. The creator becomes the admin player.

**Request:**
```json
{
  "creator_id": "string",
  "name": "string",
  "script_id": "string | null"
}
```

**Response:**
```json
{
  "game_id": "uuid-string"
}
```

---

### `GET /rooms`
List all rooms.

**Response:**
```json
[
  {
    "game_id": "string",
    "player_count": 3,
    "phase": "waiting",
    "act": 1,
    "script_generated": false,
    "title": "剧本标题"
  }
]
```

---

### `GET /rooms/{game_id}`
Get full room state including players, script, clues, votes, and recent public messages.

**Response:**
```json
{
  "game_id": "string",
  "phase": "playing",
  "act": 1,
  "room_creator_id": "string",
  "script_generated": true,
  "players": {
    "player_id": { "name": "张三", "role_id": "role_1" }
  },
  "script": {
    "title": "剧本标题",
    "genre": "悬疑推理",
    "difficulty": "中等",
    "estimated_time": 90,
    "background_story": "...",
    "true_killer": "角色名",
    "roles": [...],
    "roles_count": 4,
    "plot_outline": { "act1": "...", "act2": "...", "act3": "..." }
  },
  "clues": [...],
  "votes": [...],
  "public_messages": [
    {
      "message_id": "uuid",
      "content": "消息内容",
      "player_id": "string",
      "role_name": "角色名",
      "timestamp": "2024-01-01T00:00:00",
      "from_player_name": "角色名(玩家名)"
    }
  ]
}
```

---

### `DELETE /rooms/{game_id}`
Delete a room (admin only).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**Response:**
```json
{ "status": "deleted" }
```

---

### `POST /rooms/{game_id}/players`
Add a player to the room. Enforces MAX_PLAYERS_PER_ROOM limit.

**Request:**
```json
{
  "player_id": "string",
  "name": "string"
}
```

**Response:**
```json
{
  "player_id": "string",
  "name": "string",
  "role_id": "role_1"
}
```

Broadcasts `player_joined` via WebSocket.

---

### `GET /rooms/{game_id}/players`
List all players in a room.

**Response:**
```json
{
  "player_id": { "name": "张三", "role_id": "role_1" }
}
```

---

### `POST /rooms/{game_id}/players/{target_pid}/kick`
Kick a player (admin only).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**Response:**
```json
{ "status": "kicked", "target_player_id": "string" }
```

---

### `POST /rooms/{game_id}/leave`
Player leaves the room.

**Request:**
```json
{ "player_id": "string", "name": "string" }
```

**Response:**
```json
{ "status": "left", "player_id": "string" }
```

---

### `GET /genres`
Get available script genres and difficulties.

**Response:**
```json
{
  "genres": [
    { "value": "悬疑推理", "label": "经典谋杀案，逻辑推理" },
    { "value": "古风权谋", "label": "古代宫廷/江湖，权力斗争" },
    { "value": "现代都市", "label": "当代社会背景，情感纠葛" },
    { "value": "恐怖惊悚", "label": "超自然元素，心理恐惧" },
    { "value": "欢乐搞笑", "label": "轻松幽默，反转结局" },
    { "value": "科幻未来", "label": "赛博朋克/太空，高科技犯罪" }
  ],
  "difficulties": ["简单", "中等", "困难"]
}
```

---

## Script API (`server/api/script.py`)

### `POST /rooms/{game_id}/generate-script`
Generate a script via LLM with SSE streaming. Returns `text/event-stream`.

**Request:**
```json
{
  "genre": "悬疑推理",
  "difficulty": "中等",
  "estimated_time": 90,
  "player_count": 4
}
```

**SSE Events:**
```
data: {"type": "start"}
data: {"type": "chunk", "content": "partial json..."}
data: {"type": "chunk", "content": "more json..."}
data: {"type": "done", "title": "剧本标题", "roles_count": 4, "clues_count": 6}
data: {"type": "error", "message": "error description"}
```

---

### `POST /rooms/{game_id}/set-script`
Manually set a script (admin edited content).

**Request:**
```json
{
  "genre": "悬疑推理",
  "difficulty": "中等",
  "estimated_time": 90,
  "player_count": 4
}
```

**Response:**
```json
{ "status": "saved", "title": "剧本标题" }
```

---

## Scripts Repository API (`server/api/scripts.py`)

All scripts repository endpoints require `admin_key` query parameter (configured via `SCRIPT_ADMIN_KEY` env var).

### `GET /scripts`
List stored scripts. Optional query params: `genre`, `difficulty`, `min_players`.

**Response:**
```json
{ "scripts": [...] }
```

---

### `POST /scripts`
Upload a new script.

**Request:** `ScriptUploadRequest` (title, genre, difficulty, roles, clues, etc.)

**Response:**
```json
{ "script_id": "uuid" }
```

---

### `GET /scripts/{script_id}`
Get script detail.

---

### `DELETE /scripts/{script_id}`
Delete a script (admin key required).

---

### `GET /scripts/export`
Export all scripts (admin key required).

---

### `POST /scripts/import`
Import scripts in bulk (admin key required).

**Request:**
```json
{ "scripts": [...] }
```

**Response:**
```json
{ "imported": 3 }
```

---

## Game API (`server/api/game.py`)

### `POST /rooms/{game_id}/start`
Start the game. Requires ≥2 players and a generated script.

**Response:**
```json
{ "game_id": "string", "phase": "playing" }
```

Side effects:
- Distributes layer 1 role cards via WS (and caches in `distributed_role_cards`)
- Unlocks act 1 (layer 2 role cards, clues, private events)
- Triggers DM auto-opening background task
- Starts GameScheduler for auto-DM mode

---

### `POST /rooms/{game_id}/dm/push-event`
Admin triggers DM event generation (SSE streaming).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**SSE Events:**
```
data: {"type": "start"}
data: {"type": "done", "public_event": "...", "private_clues_count": 2}
data: {"type": "error", "message": "..."}
```

---

### `POST /rooms/{game_id}/advance-act`
Advance to next act (admin only). Max act 3.

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**Response:**
```json
{ "status": "act_advanced", "act": 2 }
```

Side effects:
- Broadcasts `phase_unlock` and `act_transition` via WS
- Distributes new role cards, clues, and private events

---

### `POST /rooms/{game_id}/force-trial`
Force trial phase (admin only).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**Response:**
```json
{ "status": "trial_started", "phase": "trial" }
```

---

### `POST /rooms/{game_id}/end-game`
End game with truth reveal (SSE streaming, admin only).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**SSE Events:**
```
data: {"type": "start"}
data: {"type": "done", "content": "真相揭晓内容..."}
data: {"type": "error", "message": "..."}
```

---

### `POST /rooms/{game_id}/dm/toggle-auto`
Toggle autonomous DM mode (admin only).

**Request:**
```json
{ "player_id": "admin_player_id" }
```

**Response:**
```json
{ "auto": true }
```

---

### `GET /rooms/{game_id}/dm/status`
Get DM status including idle time and intervention count.

**Response:**
```json
{
  "auto": true,
  "phase": "playing",
  "act": 1,
  "idle_seconds": 45,
  "interventions": 3
}
```

---

## DM API (`server/api/dm.py`)

### `POST /rooms/{game_id}/dm/add-clue`
Add a custom clue (admin only). Broadcasts event via WS.

**Request:**
```json
{
  "player_id": "admin_player_id",
  "clue_title": "线索标题",
  "clue_content": "线索内容"
}
```

**Response:**
```json
{ "status": "clue_added" }
```

---

### `POST /rooms/{game_id}/dm/private`
Send DM private message to a player (admin only).

**Request:**
```json
{
  "player_id": "admin_player_id",
  "to_player_id": "target_player_id",
  "content": "私信内容"
}
```

**Response:**
```json
{ "status": "dm_private_sent" }
```

Cached in `distributed_dm_private` for reconnect.

---

### `POST /rooms/{game_id}/dm/chat-response`
Player chats with DM (SSE streaming). 30s cooldown per player.

**Request:**
```json
{
  "player_id": "string",
  "content": "玩家消息 (1-500 chars)"
}
```

**SSE Events:**
```
data: {"type": "start"}
data: {"type": "chunk", "content": "回复片段..."}
data: {"type": "done", "content": "完整回复"}
data: {"type": "error", "message": "请等待 30 秒后再向 DM 提问"}
```

---

### `GET /rooms/{game_id}/dm/log`
Get DM reasoning log.

**Response:**
```json
{ "dm_log": ["log entry 1", "log entry 2"] }
```

---

## Chat API (`server/api/chat.py`)

### `POST /rooms/{game_id}/chat`
Send a chat message via REST (supplementary to WebSocket chat).

**Request:**
```json
{
  "player_id": "string",
  "message": "string",
  "is_private": false,
  "target_player_id": null
}
```

**Response:**
```json
{ "status": "message sent" }
```

---

### `GET /rooms/{game_id}/messages`
Get chat message history for a room.

**Query params:** `limit` (default 50)

**Response:**
```json
{
  "messages": [
    {
      "id": "uuid",
      "from_player_id": "string",
      "content": "消息内容",
      "type": "public",
      "timestamp": "2024-01-01T00:00:00",
      "from_player_name": "角色名(玩家名)"
    }
  ]
}
```

---

## Voting API (`server/api/voting.py`)

### `POST /rooms/{game_id}/accusations`
Submit an accusation. Only allowed in `playing` or `trial` phase. One accusation per player (deduplicated).

**Request:**
```json
{
  "from_player_id": "string",
  "target_role_name": "角色名",
  "reasoning": "推理理由"
}
```

**Response:**
```json
{ "status": "accusation recorded" }
```

---

### `POST /rooms/{game_id}/votes`
Cast a vote. Only allowed in `playing` or `trial` phase. Latest vote per player wins (deduplicated).

**Request:**
```json
{
  "from_player_id": "string",
  "target_role_name": "角色名",
  "reasoning": "投票理由"
}
```

**Response:**
```json
{ "status": "vote recorded" }
```

---

### `GET /rooms/{game_id}/consensus`
Check if voting consensus has been reached (≥50% on same target, excluding admin).

**Response:**
```json
{
  "consensus_reached": false,
  "votes": [
    {
      "id": "uuid",
      "from_player_id": "string",
      "target_role_name": "角色名",
      "reasoning": "理由",
      "timestamp": "2024-01-01T00:00:00"
    }
  ]
}
```

---

## LLM Provider API (`server/api/llm.py`)

### `GET /llm/providers`
List all configured LLM providers.

**Response:**
```json
{ "providers": [...] }
```

---

### `POST /llm/providers`
Add a new LLM provider.

**Request:**
```json
{
  "name": "string",
  "type": "openai|anthropic|gemini",
  "endpoint": "string",
  "model": "string",
  "api_key": "string"
}
```

---

### `DELETE /llm/providers/{name}`
Remove an LLM provider.

---

### `POST /llm/providers/active`
Set the active provider.

**Request:**
```json
{ "name": "string" }
```

---

### `POST /llm/providers/{name}/test`
Test connection to a provider.

**Response:**
```json
{
  "status": "connected",
  "response_time_ms": 1234,
  "model": "model-name",
  "sample_response": "..."
}
```

---

### `GET /llm/providers/{name}/models`
List available models from a provider.

---

### `GET /llm-config`
Get current active LLM configuration (backward-compatible).

---

### `GET /health`
Health check endpoint.

**Response:**
```json
{ "status": "ok" }
```

---

## WebSocket (`server/websocket_hub.py`)

### Endpoint: `ws://{host}:{port}/ws/{room_id}/{player_id}`

Server validates that the room exists and the player belongs to it before accepting the connection.

#### On Connect
Server sends cached state:
1. `phase_unlock` — current phase and act
2. Role card layer 1 (if not in distribution cache)
3. All pending distributions from `get_pending_distributions()`:
   - `role_card` messages
   - `clue_unlock` messages
   - `dm_private` messages
   - `private_chat` messages
   - `accusation` + `vote_cast` messages
4. Last 50 public messages (chat and event)
5. `system` welcome message

#### Client → Server Messages

| Type | Fields | Description |
|---|---|---|
| `chat` | `content` | Public chat message. Broadcast to room. Updates `last_player_activity`. |
| `private_chat` | `to_player_id`, `content` | Private message to specific player. Validates receiver exists. Sent to sender and receiver. Cached for reconnect. |
| `accuse` | `target_role_name`, `reasoning` | Submit accusation. Broadcast to room. Cached for reconnect. |
| `vote` | `target_role_name`, `reasoning` | Cast vote (only in playing/trial phase). Added to votes list. Broadcast as `vote_cast`. Cached for reconnect. |
| `request_advance` | *(none)* | Request DM to generate next event (only in playing phase). Non-blocking LLM call. Returns `event` (broadcast) + `dm_private` (per-player). Error feedback sent to requesting player. |

#### Server → Client Messages

| Type | Fields | Description |
|---|---|---|
| `phase_unlock` | `phase`, `act` | Phase/act change notification |
| `act_transition` | `act`, `plot_summary` | Act advancement with plot summary |
| `role_card` | `layer`, `player_id`, `data` (name, description) | Role card reveal (3 layers) |
| `clue_unlock` | `player_id`, `clue` (id, title, content, ...) | Clue distribution |
| `dm_private` | `from`, `to`, `content` | DM private message |
| `event` | `content` | Public event/narrative from DM |
| `chat` | `from`, `from_player_id`, `content`, `timestamp` | Public chat message |
| `private_chat` | `from`, `content`, `timestamp` | Private chat message |
| `accusation` | `from`, `from_player_id`, `target`, `reasoning` | Accusation broadcast |
| `vote_cast` | `from`, `from_player_id`, `target` | Vote broadcast |
| `player_joined` | `player_id`, `player_name` | Player joined notification |
| `player_left` | `player_id`, `player_name` | Player left notification |
| `system` | `content` | System message |
