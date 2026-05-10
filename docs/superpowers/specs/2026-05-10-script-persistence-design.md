# Script Persistence Design

**Date:** 2026-05-10  
**Status:** Approved  
**Author:** OpenCode

## Overview

Add long-term storage for generated scripts in the Script Murder game. Players can select from a library of pre-generated scripts to start games, instead of always generating new ones via LLM.

## Goals

- Persist scripts to SQLite database
- Allow players to browse, filter, and preview scripts
- Enable admin to upload/delete/export/import scripts via JSON
- Support selecting existing scripts when creating rooms
- Maintain backward compatibility with existing game flow

## Non-Goals

- Game history tracking (deferred)
- Player ratings/comments (deferred)
- Full game state persistence (out of scope)

## Architecture

### Layer Structure

```
Frontend (Vue 3)
    ↓ HTTP/WebSocket
ScriptService (Business Logic)
    ↓
ScriptRepository (Data Access)
    ↓
SQLite Database
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| `ScriptRepository` | SQLite CRUD, JSON import/export, soft delete |
| `ScriptService` | Script generation, storage orchestration, detail masking |
| `RoomManager` | Create games with selected script ID (modified) |
| `Script API Routes` | REST endpoints for script management |

## Database Schema

### scripts Table

```sql
CREATE TABLE scripts (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    genre TEXT,              -- 悬疑/古风/都市/恐怖/欢乐/科幻
    difficulty TEXT,         -- 简单/中等/困难
    player_count INTEGER,    -- 支持人数
    estimated_time INTEGER,  -- 预计时长（分钟）
    background_story TEXT,
    full_content JSON,       -- 完整 Script 模型（JSON 序列化）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

CREATE INDEX idx_scripts_genre ON scripts(genre);
CREATE INDEX idx_scripts_difficulty ON scripts(difficulty);
CREATE INDEX idx_scripts_player_count ON scripts(player_count);
```

### Data Storage Strategy

- **`full_content`**: Store entire `Script` Pydantic model as JSON
- Enables easy JSON export/import without schema mapping
- Contains roles, clues, plot_outline, private_events, true_killer, etc.
- Frontend masks sensitive fields (true_killer, clues) in preview

## API Endpoints

### Public Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/scripts` | List scripts with filters (`?genre=x&difficulty=y&min_players=z`) | None |
| GET | `/api/scripts/{id}` | Get script detail (masked: hide true_killer, clues) | None |

### Admin Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/scripts` | Upload new script (JSON body) | Admin |
| DELETE | `/api/scripts/{id}` | Soft delete script | Admin |
| GET | `/api/scripts/export` | Export all scripts as JSON array | Admin |
| POST | `/api/scripts/import` | Import scripts from JSON file | Admin |

### Request/Response Examples

**List Scripts:**
```json
GET /api/scripts?genre=悬疑&difficulty=中等
Response: {
  "scripts": [
    {
      "id": "abc123",
      "title": "午夜凶铃",
      "genre": "悬疑",
      "difficulty": "中等",
      "player_count": 6,
      "estimated_time": 120,
      "background_story": "...",
      "created_at": "2026-05-10T10:00:00Z"
    }
  ]
}
```

**Get Detail (Masked):**
```json
GET /api/scripts/abc123
Response: {
  "id": "abc123",
  "title": "午夜凶铃",
  "genre": "悬疑",
  "difficulty": "中等",
  "player_count": 6,
  "estimated_time": 120,
  "background_story": "...",
  "roles": [...],           // Include role names/descriptions only
  "plot_outline": {...},    // Include act outlines
  // true_killer: HIDDEN
  // clues: HIDDEN
  // private_events: HIDDEN
}
```

**Upload Script:**
```json
POST /api/scripts
Headers: Authorization: Bearer <admin_token>
Body: {
  "title": "午夜凶铃",
  "genre": "悬疑",
  "difficulty": "中等",
  "player_count": 6,
  "estimated_time": 120,
  "background_story": "...",
  "true_killer": "角色 A",
  "murder_method": "...",
  "cover_up": "...",
  "roles": [...],
  "clues": [...],
  "plot_outline": {...},
  "private_events": [...]
}
```

## File Structure

### Backend (New Files)

```
server/
  script_repository.py    # SQLite CRUD + JSON import/export
  script_service.py       # Business logic layer
  api/
    scripts.py            # Script management routes
```

### Backend (Modified Files)

```
server/
  game_manager.py         # Add script_id parameter to create_game()
  di/container.py         # Register ScriptService singleton
  main.py                 # Include /api/scripts router
```

### Frontend (New Files)

```
client/src/
  components/
    ScriptList.vue        # Script list with filters
    ScriptDetail.vue      # Script preview (masked)
  pages/
    RoomCreate.vue        # Create room + select script
  types/
    script.ts             # TypeScript Script type
```

## Implementation Steps

### Phase 1: Database & Repository

1. Create `script_repository.py` with:
   - SQLite initialization
   - CRUD operations (create, read, list, delete)
   - JSON import/export functions
   - Index creation

2. Test repository with pytest:
   - Test script creation/retrieval
   - Test soft delete
   - Test JSON round-trip

### Phase 2: Service Layer

1. Create `script_service.py` with:
   - `list_scripts(filters)` → filtered list (masked metadata)
   - `get_script_detail(id)` → full detail (masked sensitive fields)
   - `upload_script(script_data)` → validate + store
   - `delete_script(id)` → soft delete
   - `export_scripts()` → JSON array
   - `import_scripts(json_data)` → bulk insert

2. Register in DI container as singleton

### Phase 3: API Routes

1. Create `api/scripts.py` with all endpoints
2. Add admin guard for write operations
3. Test with pytest + httpx client

### Phase 4: Game Manager Integration

1. Modify `create_game()` to accept optional `script_id`:
   - If `script_id` provided → load from repository
   - If not → use placeholder (LLM generation flow)

2. Update WebSocket state broadcast to include script metadata

### Phase 5: Frontend Components

1. Create `ScriptList.vue`:
   - Grid/list view toggle
   - Filter dropdowns (genre, difficulty, player count)
   - Search by title
   - Click to view detail

2. Create `ScriptDetail.vue`:
   - Display metadata + background story
   - Show role names/descriptions (no secrets)
   - Show plot outline
   - "Start Game" button → navigate to RoomCreate

3. Create `RoomCreate.vue`:
   - Script selection dropdown/search
   - Player count configuration
   - "Create Room" button

### Phase 6: Testing & Integration

1. End-to-end test flow:
   - Admin uploads script via API
   - Player browses scripts
   - Player selects script + creates room
   - Game starts with loaded script

2. Verify backward compatibility:
   - Existing LLM generation flow still works
   - No breaking changes to existing APIs

## Security Considerations

1. **Admin Authentication**: All write endpoints require admin token
2. **Input Validation**: Validate script JSON against Pydantic `Script` model
3. **SQL Injection**: Use parameterized queries (sqlite3)
4. **JSON Sanitization**: Escape special characters in export/import

## Testing Strategy

### Backend Tests

```python
# test_script_repository.py
def test_create_script()
def test_get_script()
def test_list_scripts_with_filters()
def test_soft_delete()
def test_json_export_import_roundtrip()

# test_script_service.py
def test_upload_script()
def test_get_detail_masks_sensitive_fields()
def test_delete_script()

# test_api_scripts.py
def test_get_scripts_public()
def test_upload_script_requires_admin()
def test_import_scripts()
```

### Frontend Tests

```typescript
// ScriptList.spec.ts
test('displays scripts from API')
test('filters by genre')
test('navigates to detail on click')

// ScriptDetail.spec.ts
test('hides true_killer and clues')
test('shows role descriptions')
```

## Backward Compatibility

- Existing `/api/rooms` endpoints unchanged
- `create_game()` accepts optional `script_id` (defaults to None)
- LLM generation flow preserved for rooms without script_id
- WebSocket message format unchanged

## Future Extensions

- Game history tracking (new `games` table)
- Player ratings (new `script_ratings` table)
- Script versioning (track edits over time)
- Script templates (LLM generates from template + customizations)
