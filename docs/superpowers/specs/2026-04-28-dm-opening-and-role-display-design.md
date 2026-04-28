# DM Auto-Opening + Role Name Display Design

**Date:** 2026-04-28
**Status:** Approved

## Background

Two UX gaps identified during playtesting:
1. After admin clicks "开始游戏", the DM does not generate an opening narrative. Admin must manually click "推进剧情" — players see an empty event area.
2. Chat messages show only player name (e.g., "张三"), not role name + player name (e.g., "林默(张三)").

## Feature 1: DM Auto-Opening Narrative on Game Start

### Approach

Add `asyncio.create_task()` background task in `start_game` endpoint. After all distributions (role cards, clues, private events) are sent, the background task generates the DM opening via LLM and broadcasts it via WS.

### Why this approach

- `start_game` returns JSON immediately (fast UX — admin navigates to GamePage without waiting)
- DM opening arrives via WS broadcast a few seconds later (all connected players see it)
- No frontend changes needed
- No race condition on page refresh (task runs once server-side)

### Implementation

**File: `server/api_routes.py`**

Add helper function before `start_game`:

```python
async def _auto_generate_opening(game_id: str):
    """Background task: generate DM opening narrative after game starts."""
    state = manager.get_state(game_id)
    if not state or state.phase != "playing":
        return
    try:
        event = await asyncio.to_thread(host_dm.generate_event, state)
        result = manager.push_structured_event(game_id, event)
        if result:
            from server.websocket_hub import hub
            if result["public_event"]:
                await hub.broadcast(game_id, {
                    "type": "event",
                    "content": result["public_event"],
                })
            for clue in result["private_clues"]:
                await hub.send_dm_private(game_id, clue["player_id"], clue["content"])
    except Exception as e:
        manager.add_dm_log(game_id, f"开场白生成失败: {e}")
```

At the end of `start_game` endpoint (before `return`):

```python
    # Auto-generate DM opening narrative in background
    asyncio.create_task(_auto_generate_opening(game_id))
```

Add `import asyncio` to existing imports.

**Testing:** Add `asyncio` import to test. Existing `start_game` tests pass (background task doesn't affect response). No new test needed — the background task is best tested via E2E.

### Files Changed
- `server/api_routes.py` — add `_auto_generate_opening` + `asyncio.create_task` call

---

## Feature 2: Role Name + Player Name Display

### Approach

Create a shared helper `_resolve_display_name(state, player_id)` that returns `"角色名(玩家名)"` format. Apply it in all 5 places where player names are resolved for display.

### Display Format
- Player with role: `"林默(张三)"` — `role_name(player_name)`
- Player without role (waiting phase): `"张三"` — player name only
- DM: `"🎭 DM"` — unchanged

### Implementation

**File: `server/websocket_hub.py`** — Add helper function + use in 4 places:

1. `chat` handler (line ~72-85) — WS broadcast `from` field
2. `accuse` handler (line ~102-116) — WS broadcast `from` field + cache
3. `vote` handler (line ~118-130) — WS broadcast `from` field
4. WS on_connect chat history (line ~183-201) — resend messages `sender_name`

```python
def _resolve_display_name(state, player_id: str) -> str:
    """Resolve display name: '角色名(玩家名)' or '玩家名' if no role."""
    if player_id == "__dm__":
        return "🎭 DM"
    if state and player_id in state.players:
        player = state.players[player_id]
        if player.role and player.role.name:
            return f"{player.role.name}({player.name})"
        return player.name
    return player_id
```

**File: `server/api_routes.py`** — Use in 1 place:

1. `get_room` endpoint `public_messages` (line ~185-198) — `from_player_name` field

Replace the inline ternary with the same helper. Import it from websocket_hub or duplicate as a module-level function.

**Best approach:** Define the helper in `server/websocket_hub.py` and import it in `server/api_routes.py`.

### Files Changed
- `server/websocket_hub.py` — add `_resolve_display_name` helper + use in 4 places
- `server/api_routes.py` — import and use `_resolve_display_name` in `get_room`

---

## Verification

- `pytest tests/ -v` — 45 passed
- `cd client && npx vue-tsc --noEmit` — clean
- `cd client && npm test` — 2 passed
- `cd client && npm run build` — succeeds

## Scope

- Backend only (2 files). No frontend changes needed — frontend already displays `from` field directly.
- No new WS message types or API endpoints.
- No migration needed (in-memory state).
