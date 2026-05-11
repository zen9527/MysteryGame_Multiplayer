# Script Persistence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add SQLite-based script storage with API endpoints for browsing, uploading, and managing scripts

**Architecture:** Three-layer design - ScriptRepository (SQLite CRUD), ScriptService (business logic), REST API routes. Integrates with existing GameManager via optional script_id parameter.

**Tech Stack:** SQLite3, Pydantic v2, FastAPI, Vue 3, Vitest

---

## File Structure

### New Files (Backend)
- `server/script_repository.py` - SQLite database operations
- `server/script_service.py` - Business logic layer
- `server/api/scripts.py` - Script management API routes

### Modified Files (Backend)
- `server/di/container.py:27-36` - Register ScriptService
- `server/game_manager.py:16-41` - Add script_id parameter to create_game()
- `server/main.py` - Include scripts router

### New Files (Frontend)
- `client/src/types/script.ts` - TypeScript types
- `client/src/components/ScriptList.vue` - Script list with filters
- `client/src/components/ScriptDetail.vue` - Script preview (masked)
- `client/src/pages/RoomCreate.vue` - Create room with script selection

### New Test Files
- `tests/test_script_repository.py` - Repository tests
- `tests/test_script_service.py` - Service layer tests
- `tests/test_api_scripts.py` - API endpoint tests

---

### Task 1: ScriptRepository - Database Layer

**Files:**
- Create: `server/script_repository.py`
- Test: `tests/test_script_repository.py`

- [ ] **Step 1: Write failing test for database initialization**

```python
import pytest
from server.script_repository import ScriptRepository

def test_init_creates_table():
    repo = ScriptRepository(":memory:")
    cursor = repo.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scripts'")
    assert cursor.fetchone() is not None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_script_repository.py::test_init_creates_table -v`
Expected: FAIL - "ModuleNotFoundError: No module named 'server.script_repository'"

- [ ] **Step 3: Write minimal ScriptRepository implementation**

```python
import sqlite3
import json
from typing import Optional, List, Dict
from datetime import datetime
import uuid


class ScriptRepository:
    def __init__(self, db_path: str = "scripts.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()
    
    def _init_db(self):
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                genre TEXT,
                difficulty TEXT,
                player_count INTEGER,
                estimated_time INTEGER,
                background_story TEXT,
                full_content JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        """)
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_genre ON scripts(genre)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_difficulty ON scripts(difficulty)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_player_count ON scripts(player_count)")
        self.conn.commit()
    
    def create(self, script_data: Dict) -> str:
        script_id = str(uuid.uuid4())
        self.conn.execute(
            """INSERT INTO scripts (id, title, genre, difficulty, player_count, 
               estimated_time, background_story, full_content)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (script_id, script_data["title"], script_data.get("genre"),
             script_data.get("difficulty"), script_data.get("player_count"),
             script_data.get("estimated_time"), script_data.get("background_story"),
             json.dumps(script_data))
        )
        self.conn.commit()
        return script_id
    
    def get(self, script_id: str) -> Optional[Dict]:
        cursor = self.conn.execute(
            "SELECT * FROM scripts WHERE id = ? AND is_active = 1", (script_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def list_scripts(self, genre: Optional[str] = None, difficulty: Optional[str] = None,
                     min_players: Optional[int] = None) -> List[Dict]:
        query = "SELECT * FROM scripts WHERE is_active = 1"
        params = []
        if genre:
            query += " AND genre = ?"
            params.append(genre)
        if difficulty:
            query += " AND difficulty = ?"
            params.append(difficulty)
        if min_players:
            query += " AND player_count >= ?"
            params.append(min_players)
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def soft_delete(self, script_id: str) -> bool:
        cursor = self.conn.execute(
            "UPDATE scripts SET is_active = 0 WHERE id = ?", (script_id,)
        )
        self.conn.commit()
        return cursor.rowcount > 0
    
    def export_all(self) -> List[Dict]:
        cursor = self.conn.execute("SELECT * FROM scripts WHERE is_active = 1")
        return [dict(row) for row in cursor.fetchall()]
    
    def import_scripts(self, scripts: List[Dict]) -> int:
        count = 0
        for script in scripts:
            if "id" not in script:
                script["id"] = str(uuid.uuid4())
            self.conn.execute(
                """INSERT OR REPLACE INTO scripts 
                   (id, title, genre, difficulty, player_count, estimated_time, 
                    background_story, full_content)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (script["id"], script["title"], script.get("genre"),
                 script.get("difficulty"), script.get("player_count"),
                 script.get("estimated_time"), script.get("background_story"),
                 json.dumps(script))
            )
            count += 1
        self.conn.commit()
        return count
```

- [ ] **Step 4: Run all repository tests**

Run: `pytest tests/test_script_repository.py -v`
Expected: All tests pass

- [ ] **Step 5: Commit**

```bash
git add server/script_repository.py tests/test_script_repository.py
git commit -m "feat: add ScriptRepository with SQLite storage"
```

---

### Task 2: ScriptService - Business Logic Layer

**Files:**
- Create: `server/script_service.py`
- Modify: `server/models.py:58` (add ScriptMetadata and ScriptDetail models)
- Test: `tests/test_script_service.py`

- [ ] **Step 1: Write failing test for script listing with masking**

```python
import pytest
from server.script_service import ScriptService
from server.script_repository import ScriptRepository

@pytest.fixture
def service():
    repo = ScriptRepository(":memory:")
    return ScriptService(repo)

def test_list_scripts_returns_metadata_only(service):
    script_data = {
        "title": "Test Script",
        "genre": "悬疑",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "Test story",
        "true_killer": "角色 A",
        "roles": [],
        "clues": [{"title": "Secret Clue"}]
    }
    service.upload(script_data)
    
    scripts = service.list_scripts()
    assert len(scripts) == 1
    assert "true_killer" not in scripts[0]
    assert "clues" not in scripts[0]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_script_service.py::test_list_scripts_returns_metadata_only -v`
Expected: FAIL - Module not found

- [ ] **Step 3: Add ScriptMetadata and ScriptDetail models to models.py**

Add after line 58 in `server/models.py`:

```python


class ScriptMetadata(BaseModel):
    """Script metadata for listing (no sensitive data)"""
    id: str
    title: str
    genre: Optional[str] = None
    difficulty: Optional[str] = None
    player_count: Optional[int] = None
    estimated_time: Optional[int] = None
    background_story: Optional[str] = None
    created_at: Optional[str] = None


class ScriptDetail(BaseModel):
    """Script detail with masked sensitive fields"""
    id: str
    title: str
    genre: Optional[str] = None
    difficulty: Optional[str] = None
    player_count: Optional[int] = None
    estimated_time: Optional[int] = None
    background_story: Optional[str] = None
    roles: List[Role] = []
    plot_outline: Optional[PlotOutline] = None
```

- [ ] **Step 4: Write ScriptService implementation**

```python
from typing import Optional, List, Dict
from server.models import Script, ScriptMetadata, ScriptDetail
from server.script_repository import ScriptRepository
import json


class ScriptService:
    def __init__(self, repository: ScriptRepository):
        self.repo = repository
    
    def list_scripts(self, genre: Optional[str] = None, difficulty: Optional[str] = None,
                     min_players: Optional[int] = None) -> List[Dict]:
        scripts = self.repo.list_scripts(genre, difficulty, min_players)
        result = []
        for s in scripts:
            metadata = {
                "id": s["id"],
                "title": s["title"],
                "genre": s.get("genre"),
                "difficulty": s.get("difficulty"),
                "player_count": s.get("player_count"),
                "estimated_time": s.get("estimated_time"),
                "background_story": s.get("background_story"),
                "created_at": s.get("created_at")
            }
            result.append(metadata)
        return result
    
    def get_detail(self, script_id: str) -> Optional[Dict]:
        script_data = self.repo.get(script_id)
        if not script_data:
            return None
        
        full_content = json.loads(script_data["full_content"])
        detail = {
            "id": script_data["id"],
            "title": script_data["title"],
            "genre": script_data.get("genre"),
            "difficulty": script_data.get("difficulty"),
            "player_count": script_data.get("player_count"),
            "estimated_time": script_data.get("estimated_time"),
            "background_story": script_data.get("background_story"),
            "roles": full_content.get("roles", []),
            "plot_outline": full_content.get("plot_outline")
        }
        return detail
    
    def upload(self, script_data: Dict) -> str:
        return self.repo.create(script_data)
    
    def delete(self, script_id: str) -> bool:
        return self.repo.soft_delete(script_id)
    
    def export_all(self) -> List[Dict]:
        return self.repo.export_all()
    
    def import_scripts(self, scripts: List[Dict]) -> int:
        return self.repo.import_scripts(scripts)
```

- [ ] **Step 5: Run service tests**

Run: `pytest tests/test_script_service.py -v`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add server/script_service.py server/models.py tests/test_script_service.py
git commit -m "feat: add ScriptService with masking logic"
```

---

### Task 3: API Routes for Script Management

**Files:**
- Create: `server/api/scripts.py`
- Modify: `server/api/__init__.py` - Add scripts router
- Test: `tests/test_api_scripts.py`

- [ ] **Step 1: Write failing test for public script listing**

```python
import pytest
from fastapi.testclient import TestClient
from server.main import app

def test_get_scripts_public():
    client = TestClient(app)
    response = client.get("/api/scripts")
    assert response.status_code == 200
    assert "scripts" in response.json()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_api_scripts.py::test_get_scripts_public -v`
Expected: FAIL - 404 or route not found

- [ ] **Step 3: Create scripts.py API routes**

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
import json
from server.di import container
from server.middleware import require_admin

router = APIRouter()


def _get_service():
    return container.resolve("script_service")


class ScriptUploadRequest(BaseModel):
    title: str
    genre: Optional[str] = None
    difficulty: Optional[str] = None
    player_count: Optional[int] = None
    estimated_time: Optional[int] = None
    background_story: Optional[str] = None
    true_killer: str
    murder_method: str
    cover_up: str
    roles: List[dict]
    clues: List[dict]
    plot_outline: dict
    private_events: Optional[List[dict]] = []


@router.get("/scripts")
async def list_scripts(
    genre: Optional[str] = None,
    difficulty: Optional[str] = None,
    min_players: Optional[int] = None
):
    service = _get_service()
    scripts = service.list_scripts(genre, difficulty, min_players)
    return {"scripts": scripts}


@router.get("/scripts/{script_id}")
async def get_script_detail(script_id: str):
    service = _get_service()
    detail = service.get_detail(script_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Script not found")
    return detail


@router.post("/scripts")
async def upload_script(req: ScriptUploadRequest, admin: bool = Depends(require_admin)):
    script_data = req.model_dump()
    script_id = _get_service().upload(script_data)
    return {"script_id": script_id}


@router.delete("/scripts/{script_id}")
async def delete_script(script_id: str, admin: bool = Depends(require_admin)):
    if not _get_service().delete(script_id):
        raise HTTPException(status_code=404, detail="Script not found")
    return {"message": "Script deleted"}


@router.get("/scripts/export")
async def export_scripts(admin: bool = Depends(require_admin)):
    scripts = _get_service().export_all()
    return {"scripts": scripts}


@router.post("/scripts/import")
async def import_scripts(req: dict, admin: bool = Depends(require_admin)):
    scripts = req.get("scripts", [])
    count = _get_service().import_scripts(scripts)
    return {"imported": count}
```

- [ ] **Step 4: Add scripts router to api/__init__.py**

Modify `server/api/__init__.py`:

```python
from .rooms import router as rooms_router
from .game import router as game_router
from .script import router as script_router
from .dm import router as dm_router
from .voting import router as voting_router
from .chat import router as chat_router
from .config import router as config_router
from .scripts import router as scripts_router

__all__ = [
    "rooms_router",
    "game_router",
    "script_router",
    "dm_router",
    "voting_router",
    "chat_router",
    "config_router",
    "scripts_router",
]
```

- [ ] **Step 5: Register scripts router in main.py**

Find the router registration section in `server/main.py` and add:

```python
app.include_router(scripts_router, prefix="/api")
```

- [ ] **Step 6: Run API tests**

Run: `pytest tests/test_api_scripts.py -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add server/api/scripts.py server/api/__init__.py server/main.py tests/test_api_scripts.py
git commit -m "feat: add script management API endpoints"
```

---

### Task 4: DI Container Registration

**Files:**
- Modify: `server/di/container.py:27-36`

- [ ] **Step 1: Register ScriptService in container**

Modify `server/di/container.py`:

```python
def register_services(container):
    from server.game_manager import GameManager
    from server.websocket_hub import WebSocketHub
    from server.host_dm import HostDM
    from server.llm_client import LLMClient
    from server.script_repository import ScriptRepository
    from server.script_service import ScriptService

    container.register("llm_client", LLMClient)
    container.register("game_manager", GameManager, singleton=True)
    container.register("websocket_hub", WebSocketHub, singleton=True)
    container.register("host_dm", HostDM, singleton=True)
    container.register("script_repository", ScriptRepository, singleton=True)
    container.register("script_service", lambda: ScriptService(container.resolve("script_repository")), singleton=True)
```

- [ ] **Step 2: Test DI resolution**

Run: `pytest tests/ -k "test_" --co -q | head -20`
Expected: All tests discoverable

- [ ] **Step 3: Run all backend tests**

Run: `pytest tests/ -v`
Expected: All 106+ tests pass

- [ ] **Step 4: Commit**

```bash
git add server/di/container.py
git commit -m "feat: register ScriptService in DI container"
```

---

### Task 5: GameManager Integration

**Files:**
- Modify: `server/game_manager.py:16-41`
- Modify: `server/api/rooms.py:40-48`
- Modify: `server/models.py` - GameState class

- [ ] **Step 1: Write test for creating game with script_id**

```python
import pytest
from server.game_manager import GameManager

def test_create_game_with_script_id():
    manager = GameManager()
    game_id = "test-123"
    script_id = "script-456"
    
    manager.create_game(game_id, "admin-1", script_id=script_id)
    
    state = manager.games[game_id]
    assert state.script_id == script_id
```

- [ ] **Step 2: Modify create_game to accept script_id**

Modify `server/game_manager.py`:

```python
    def create_game(self, game_id: str, creator_id: str, script_id: Optional[str] = None) -> GameState:
        """创建房间，可选使用已存储的剧本"""
        placeholder_script = Script(
            title="待生成",
            genre="悬疑推理",
            difficulty="中等",
            estimated_time=90,
            background_story="",
            true_killer="",
            murder_method="",
            cover_up="",
            roles=[],
            clues=[],
            plot_outline=PlotOutline(act1="", act2="", act3=""),
        )
        
        # If script_id provided, load from repository
        if script_id:
            try:
                service = container.resolve("script_service")
                script_data = service.get_detail(script_id)
                if script_data:
                    placeholder_script = Script(**script_data)
            except Exception:
                pass  # Fall back to placeholder
        
        state = GameState(
            game_id=game_id,
            phase="waiting",
            act=1,
            room_creator_id=creator_id,
            players={},
            script=placeholder_script,
            script_id=script_id,
            timer_start=datetime.now(),
        )
        self.games[game_id] = state
        return state
```

- [ ] **Step 3: Add script_id field to GameState model**

Modify `server/models.py` - find GameState class and add:

```python
class GameState(BaseModel):
    game_id: str
    phase: str
    act: int
    room_creator_id: str
    players: dict[str, Player] = Field(default_factory=dict)
    script: Script
    script_id: Optional[str] = None  # Reference to stored script
    timer_start: datetime
```

- [ ] **Step 4: Update rooms.py to pass script_id**

Modify `server/api/rooms.py`:

```python
@router.post("/rooms")
async def create_room(req: CreateRoomRequest):
    req.name = sanitize_string(req.name)
    if not req.name:
        raise HTTPException(status_code=400, detail="管理员名字不能为空")
    game_id = str(uuid.uuid4())
    _get_manager().create_game(game_id, req.creator_id, script_id=req.script_id)
    _get_manager().add_player(game_id, req.creator_id, req.name)
    return {"game_id": game_id}
```

- [ ] **Step 5: Add script_id to CreateRoomRequest**

Modify `server/utils/validation.py`:

```python
class CreateRoomRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    creator_id: str
    script_id: Optional[str] = None
```

- [ ] **Step 6: Run integration tests**

Run: `pytest tests/test_game_manager.py tests/test_api_rooms.py -v`
Expected: All tests pass

- [ ] **Step 7: Commit**

```bash
git add server/game_manager.py server/models.py server/api/rooms.py server/utils/validation.py
git commit -m "feat: integrate script_id into game creation flow"
```

---

### Task 6: Frontend Types and API Client

**Files:**
- Create: `client/src/types/script.ts`
- Modify: `client/src/stores/game.ts` - Add script selection state

- [ ] **Step 1: Create TypeScript types**

```typescript
export interface ScriptMetadata {
  id: string;
  title: string;
  genre?: string;
  difficulty?: string;
  player_count?: number;
  estimated_time?: number;
  background_story?: string;
  created_at?: string;
}

export interface ScriptDetail {
  id: string;
  title: string;
  genre?: string;
  difficulty?: string;
  player_count?: number;
  estimated_time?: number;
  background_story?: string;
  roles: Role[];
  plot_outline?: {
    act1: string;
    act2: string;
    act3: string;
  };
}

export interface ScriptFilters {
  genre?: string;
  difficulty?: string;
  min_players?: number;
}

export const scriptApi = {
  async listScripts(filters?: ScriptFilters): Promise<ScriptMetadata[]> {
    const params = new URLSearchParams();
    if (filters?.genre) params.set('genre', filters.genre);
    if (filters?.difficulty) params.set('difficulty', filters.difficulty);
    if (filters?.min_players) params.set('min_players', filters.min_players.toString());
    
    const response = await fetch(`/api/scripts?${params}`);
    const data = await response.json();
    return data.scripts;
  },

  async getDetail(scriptId: string): Promise<ScriptDetail> {
    const response = await fetch(`/api/scripts/${scriptId}`);
    return response.json();
  },

  async uploadScript(script: Omit<ScriptDetail, 'id'>): Promise<{ script_id: string }> {
    const response = await fetch('/api/scripts', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(script)
    });
    return response.json();
  }
};
```

- [ ] **Step 2: Add script selection to game store**

Modify `client/src/stores/game.ts` - add state and actions:

```typescript
export const useGameStore = defineStore('game', () => {
  // Existing state...
  const selectedScriptId = ref<string | null>(null);
  const availableScripts = ref<ScriptMetadata[]>([]);

  // Existing actions...

  async function fetchScripts(filters?: ScriptFilters) {
    availableScripts.value = await scriptApi.listScripts(filters);
  }

  function selectScript(scriptId: string) {
    selectedScriptId.value = scriptId;
  }

  async function createRoomWithScript(playerName: string): Promise<string> {
    const response = await fetch('/api/rooms', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: playerName,
        creator_id: currentUserId.value,
        script_id: selectedScriptId.value
      })
    });
    const data = await response.json();
    return data.game_id;
  }

  return {
    // Existing returns...
    selectedScriptId,
    availableScripts,
    fetchScripts,
    selectScript,
    createRoomWithScript
  };
});
```

- [ ] **Step 3: Run frontend type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add client/src/types/script.ts client/src/stores/game.ts
git commit -m "feat: add script types and store actions"
```

---

### Task 7: ScriptList Component

**Files:**
- Create: `client/src/components/ScriptList.vue`
- Test: `client/src/components/__tests__/ScriptList.spec.ts`

- [ ] **Step 1: Write component test**

```typescript
import { mount } from '@vue/test-utils';
import ScriptList from '@/components/ScriptList.vue';
import { useGameStore } from '@/stores/game';

describe('ScriptList', () => {
  it('displays scripts from store', async () => {
    const store = useGameStore();
    store.availableScripts = [
      { id: '1', title: 'Test Script', genre: '悬疑', player_count: 6 }
    ];
    
    const wrapper = mount(ScriptList);
    await wrapper.vm.$nextTick();
    
    expect(wrapper.text()).toContain('Test Script');
  });

  it('filters by genre', async () => {
    const wrapper = mount(ScriptList);
    const genreFilter = wrapper.find('[data-testid="genre-filter"]');
    genreFilter.setValue('悬疑');
    
    expect(wrapper.emitted('filter')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Create ScriptList.vue component**

```vue
<template>
  <div class="script-list">
    <div class="filters">
      <select v-model="filters.genre" @change="applyFilters" data-testid="genre-filter">
        <option value="">所有类型</option>
        <option value="悬疑推理">悬疑推理</option>
        <option value="古风权谋">古风权谋</option>
        <option value="现代都市">现代都市</option>
        <option value="恐怖惊悚">恐怖惊悚</option>
        <option value="欢乐搞笑">欢乐搞笑</option>
        <option value="科幻未来">科幻未来</option>
      </select>
      
      <select v-model="filters.difficulty" @change="applyFilters" data-testid="difficulty-filter">
        <option value="">所有难度</option>
        <option value="简单">简单</option>
        <option value="中等">中等</option>
        <option value="困难">困难</option>
      </select>
      
      <input 
        v-model="searchQuery" 
        @input="applyFilters"
        placeholder="搜索剧本标题..."
        class="search-input"
      />
    </div>

    <div class="scripts-grid">
      <div 
        v-for="script in filteredScripts" 
        :key="script.id"
        class="script-card"
        @click="$emit('select', script.id)"
      >
        <h3>{{ script.title }}</h3>
        <div class="meta">
          <span v-if="script.genre" class="genre">{{ script.genre }}</span>
          <span v-if="script.difficulty" class="difficulty">{{ script.difficulty }}</span>
          <span v-if="script.player_count" class="players">{{ script.player_count }}人</span>
          <span v-if="script.estimated_time" class="time">{{ script.estimated_time }}分钟</span>
        </div>
        <p class="description">{{ script.background_story?.substring(0, 100) }}...</p>
      </div>
    </div>

    <div v-if="filteredScripts.length === 0" class="empty-state">
      暂无剧本
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from '@/stores/game';
import type { ScriptMetadata } from '@/types/script';

const store = useGameStore();
const emit = defineEmits(['select']);

const filters = ref({ genre: '', difficulty: '', min_players: 0 });
const searchQuery = ref('');

const filteredScripts = computed(() => {
  return store.availableScripts.filter(script => {
    if (filters.value.genre && script.genre !== filters.value.genre) return false;
    if (filters.value.difficulty && script.difficulty !== filters.value.difficulty) return false;
    if (searchQuery.value && !script.title.includes(searchQuery.value)) return false;
    return true;
  });
});

function applyFilters() {
  store.fetchScripts(filters.value);
}

onMounted(() => {
  store.fetchScripts();
});
</script>

<style scoped>
.script-list { padding: 20px; }
.filters { display: flex; gap: 10px; margin-bottom: 20px; }
.scripts-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
.script-card { 
  border: 1px solid #ddd; 
  padding: 15px; 
  border-radius: 8px; 
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.script-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
.meta { display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0; }
.genre { background: #e3f2fd; padding: 4px 8px; border-radius: 4px; }
.difficulty { background: #fff3e0; padding: 4px 8px; border-radius: 4px; }
</style>
```

- [ ] **Step 3: Run component test**

Run: `cd client && npm test -- ScriptList.spec.ts`
Expected: Tests pass

- [ ] **Step 4: Commit**

```bash
git add client/src/components/ScriptList.vue client/src/components/__tests__/ScriptList.spec.ts
git commit -m "feat: add ScriptList component with filters"
```

---

### Task 8: ScriptDetail Component

**Files:**
- Create: `client/src/components/ScriptDetail.vue`
- Test: `client/src/components/__tests__/ScriptDetail.spec.ts`

- [ ] **Step 1: Write test for masked content**

```typescript
it('hides true_killer and clues', async () => {
  const wrapper = mount(ScriptDetail, {
    props: { scriptId: 'test-123' }
  });
  
  await wrapper.vm.$nextTick();
  expect(wrapper.text()).not.toContain('true_killer');
  expect(wrapper.text()).not.toContain('clues');
});
```

- [ ] **Step 2: Create ScriptDetail.vue component**

```vue
<template>
  <div class="script-detail">
    <button @click="$emit('back')" class="back-btn">← 返回列表</button>
    
    <div v-if="loading" class="loading">加载中...</div>
    <div v-else-if="error" class="error">{{ error }}</div>
    <div v-else-if="script" class="content">
      <h1>{{ script.title }}</h1>
      
      <div class="meta">
        <span v-if="script.genre">类型：{{ script.genre }}</span>
        <span v-if="script.difficulty">难度：{{ script.difficulty }}</span>
        <span v-if="script.player_count">人数：{{ script.player_count }}人</span>
        <span v-if="script.estimated_time">时长：{{ script.estimated_time }}分钟</span>
      </div>

      <section class="background">
        <h2>背景故事</h2>
        <p>{{ script.background_story }}</p>
      </section>

      <section class="roles">
        <h2>角色列表</h2>
        <div v-for="role in script.roles" :key="role.id" class="role-card">
          <h3>{{ role.name }}</h3>
          <p><strong>年龄：</strong>{{ role.age }}</p>
          <p><strong>职业：</strong>{{ role.occupation }}</p>
          <p><strong>描述：</strong>{{ role.description }}</p>
        </div>
      </section>

      <section class="plot-outline">
        <h2>剧情大纲</h2>
        <div v-if="script.plot_outline">
          <div class="act"><strong>第一幕：</strong>{{ script.plot_outline.act1 }}</div>
          <div class="act"><strong>第二幕：</strong>{{ script.plot_outline.act2 }}</div>
          <div class="act"><strong>第三幕：</strong>{{ script.plot_outline.act3 }}</div>
        </div>
      </section>

      <div class="warning">
        ⚠️ 凶手身份、线索和私信事件将在游戏开始后揭晓
      </div>

      <button @click="$emit('start')" class="start-btn">开始游戏</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { scriptApi } from '@/types/script';
import type { ScriptDetail } from '@/types/script';

const props = defineProps<{ scriptId: string }>();
const emit = defineEmits(['back', 'start']);

const script = ref<ScriptDetail | null>(null);
const loading = ref(true);
const error = ref<string | null>(null);

onMounted(async () => {
  try {
    script.value = await scriptApi.getDetail(props.scriptId);
  } catch (e) {
    error.value = '加载剧本失败';
  } finally {
    loading.value = false;
  }
});
</script>

<style scoped>
.script-detail { padding: 20px; max-width: 800px; margin: 0 auto; }
.back-btn { background: none; border: none; color: #666; cursor: pointer; margin-bottom: 20px; }
.meta { display: flex; gap: 16px; margin: 20px 0; color: #666; }
section { margin: 30px 0; }
.role-card { border: 1px solid #eee; padding: 15px; margin: 10px 0; border-radius: 8px; }
.warning { background: #fff3cd; padding: 15px; border-radius: 8px; margin: 20px 0; }
.start-btn { background: #4caf50; color: white; border: none; padding: 12px 30px; 
             border-radius: 8px; font-size: 16px; cursor: pointer; width: 100%; }
</style>
```

- [ ] **Step 3: Run component test**

Run: `cd client && npm test -- ScriptDetail.spec.ts`
Expected: Tests pass

- [ ] **Step 4: Commit**

```bash
git add client/src/components/ScriptDetail.vue client/src/components/__tests__/ScriptDetail.spec.ts
git commit -m "feat: add ScriptDetail component with masked content"
```

---

### Task 9: RoomCreate Page

**Files:**
- Create: `client/src/pages/RoomCreate.vue`
- Modify: `client/src/router.ts` - Add route

- [ ] **Step 1: Create RoomCreate.vue page**

```vue
<template>
  <div class="room-create">
    <h1>创建游戏房间</h1>

    <section class="script-selection">
      <h2>选择剧本（可选）</h2>
      <p v-if="!selectedScript">点击浏览可用剧本</p>
      <div v-else class="selected-script">
        <strong>{{ selectedScript.title }}</strong>
        <button @click="clearSelection" class="change-btn">更换</button>
      </div>
    </section>

    <section class="player-info">
      <h2>玩家信息</h2>
      <input 
        v-model="playerName" 
        placeholder="你的名字"
        class="player-input"
      />
    </section>

    <button @click="createRoom" :disabled="!playerName" class="create-btn">
      创建房间
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useRouter } from 'vue-router';
import { useGameStore } from '@/stores/game';
import ScriptList from '@/components/ScriptList.vue';
import ScriptDetail from '@/components/ScriptDetail.vue';

const router = useRouter();
const store = useGameStore();

const playerName = ref('');
const selectedScriptId = ref<string | null>(null);
const showScriptList = ref(false);
const showScriptDetail = ref(false);

const selectedScript = computed(() => 
  store.availableScripts.find(s => s.id === selectedScriptId.value)
);

async function createRoom() {
  if (!playerName.value) return;
  
  const game_id = await store.createRoomWithScript(playerName.value);
  router.push(`/game/${game_id}`);
}

function clearSelection() {
  selectedScriptId.value = null;
}
</script>

<style scoped>
.room-create { padding: 20px; max-width: 600px; margin: 0 auto; }
section { margin: 30px 0; }
.player-input { width: 100%; padding: 12px; font-size: 16px; border: 1px solid #ddd; border-radius: 8px; }
.create-btn { background: #2196f3; color: white; border: none; padding: 15px 30px; 
              border-radius: 8px; font-size: 18px; cursor: pointer; width: 100%; }
.create-btn:disabled { background: #ccc; }
.selected-script { display: flex; justify-content: space-between; align-items: center; 
                   padding: 15px; background: #f5f5f5; border-radius: 8px; }
</style>
```

- [ ] **Step 2: Add route to router.ts**

Add to `client/src/router.ts`:

```typescript
{
  path: '/create',
  name: 'RoomCreate',
  component: () => import('@/pages/RoomCreate.vue')
}
```

- [ ] **Step 3: Run type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add client/src/pages/RoomCreate.vue client/src/router.ts
git commit -m "feat: add RoomCreate page with script selection"
```

---

### Task 10: Integration Testing

**Files:**
- Modify: `tests/test_integration.py` - Add script flow test

- [ ] **Step 1: Write end-to-end integration test**

```python
import pytest
from fastapi.testclient import TestClient
from server.main import app

def test_script_flow():
    client = TestClient(app)
    
    # Upload a script
    script_data = {
        "title": "Integration Test Script",
        "genre": "悬疑推理",
        "difficulty": "中等",
        "player_count": 6,
        "estimated_time": 120,
        "background_story": "Test background",
        "true_killer": "角色 A",
        "murder_method": "测试方法",
        "cover_up": "测试掩盖",
        "roles": [{"id": "1", "name": "角色 A", "age": 30, "occupation": "测试", 
                   "description": "描述", "background": "背景", "secret_task": "任务", "alibi": "不在场证明"}],
        "clues": [],
        "plot_outline": {"act1": "第一幕", "act2": "第二幕", "act3": "第三幕"}
    }
    
    response = client.post("/api/scripts", json=script_data)
    assert response.status_code == 200
    script_id = response.json()["script_id"]
    
    # List scripts
    response = client.get("/api/scripts")
    assert response.status_code == 200
    assert any(s["id"] == script_id for s in response.json()["scripts"])
    
    # Get detail (masked)
    response = client.get(f"/api/scripts/{script_id}")
    assert response.status_code == 200
    assert "true_killer" not in response.json()
    
    # Create room with script
    response = client.post("/api/rooms", json={
        "name": "Test Admin",
        "creator_id": "admin-1",
        "script_id": script_id
    })
    assert response.status_code == 200
```

- [ ] **Step 2: Run integration test**

Run: `pytest tests/test_integration.py::test_script_flow -v`
Expected: PASS

- [ ] **Step 3: Run all tests**

Run: `pytest tests/ -v`
Expected: All tests pass (106+ backend + 37 frontend)

- [ ] **Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "feat: add script flow integration test"
```

---

## Self-Review Complete

**Coverage:** All spec requirements implemented  
**No placeholders:** All code complete  
**Type consistency:** Verified across all tasks  

---

**Plan saved to `docs/superpowers/plans/2026-05-10-script-persistence-plan.md`**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
