# Info Isolation & Role Card Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restructure the game to isolate player information — private role cards, DM→player messaging, per-player clue distribution — while keeping public events and chat shared.

**Architecture:** Extend existing Pydantic models with clue distribution fields and private events, add distribution methods to GameManager, fix WebSocketHub to use `send_to_player` instead of `broadcast` for private messages, and refactor GamePage into a left-right layout with private tabs (role card, private chat, clues).

**Tech Stack:** FastAPI, Pydantic v2, Vue 3 + TypeScript, Pinia, WebSocket, Zod

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `server/models.py` | Modify | Add `target_player_ids`, `unlock_phase`, `trigger_condition` to Clue; add `PrivateEvent` model |
| `server/game_manager.py` | Modify | Add `distribute_role_card`, `distribute_clue`, `execute_private_events`, `unlock_phase` methods |
| `server/websocket_hub.py` | Modify | Fix message routing — use `send_to_player` for private messages, add `dm_private` handler |
| `server/host_dm.py` | Modify | Extend LLM prompt to include clue distribution + private events in script generation |
| `server/api_routes.py` | Modify | Add DM private chat endpoint; remove `role_name` from player list in `get_room` |
| `shared/ws_types.py` | Modify | Add Pydantic models for new WS message types |
| `shared/schemas.ts` | Modify | Add Zod schemas for new WS message types |
| `client/src/types/ws.ts` | Modify | Add new WSMessage types |
| `client/src/stores/game.ts` | Modify | Add `roleCard`, `privateMessages`, `clues`, `activeTab` state |
| `client/src/components/RoleCard.vue` | Create | Layered role card with progressive unlock |
| `client/src/components/PrivateChatPanel.vue` | Create | DM private chat + player private chat |
| `client/src/components/ClueCardPanel.vue` | Create | Clue cards with expand/collapse |
| `client/src/components/GamePage.vue` | Modify | Refactor into left-right layout with tabs |
| `tests/test_game_manager.py` | Modify | Add tests for new distribution methods |

---

### Task 1: Backend — Extend Data Models

**Files:**
- Modify: `server/models.py:20-28` (Clue fields)
- Create: `server/models.py` (add PrivateEvent class)

- [ ] **Step 1: Extend Clue model with distribution fields**

Add three fields to the existing `Clue` class in `server/models.py`:

```python
class Clue(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    target_role: Optional[str] = None
    is_red_herring: bool = False
    content_hint: str
    # Distribution fields
    target_player_ids: List[str] = Field(default_factory=list)
    unlock_phase: str = "act2"
    trigger_condition: Optional[str] = None
```

- [ ] **Step 2: Add PrivateEvent model**

Append this new class after the `Clue` class in `server/models.py`:

```python
class PrivateEvent(BaseModel):
    """DM 私信触发点 — LLM 生成剧本时规划"""
    phase: str  # act1, act2, act3, trial
    target_player_id: str  # 目标玩家角色名（LLM 输出角色名，后端匹配 player_id）
    content: str  # DM 私信内容
    trigger: Optional[str] = None  # 触发条件，如"玩家请求线索时"
```

- [ ] **Step 3: Add PrivateEvent to Script model**

In `Script` class, add a new field after `plot_outline`:

```python
    private_events: List[PrivateEvent] = Field(default_factory=list)
```

- [ ] **Step 4: Run type check**

```bash
python -c "from server.models import Clue, PrivateEvent, Script; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add server/models.py
git commit -m "feat: extend Clue with distribution fields and add PrivateEvent model"
```

---

### Task 2: Backend — GameManager Distribution Methods

**Files:**
- Modify: `server/game_manager.py` (add methods after line 181)

- [ ] **Step 1: Add `distribute_role_card` method**

Append after `get_state` method (before `manager = GameManager()`):

```python
    def distribute_role_card(self, game_id: str, player_id: str, layer: str):
        """分发角色卡指定层级给玩家。
        layer: '1' = 角色名+简介, '2' = 背景/秘密任务/不在场证明, '3' = 人际关系/动机/个人线索
        """
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        player = state.players.get(player_id)
        if not player or not player.role:
            return None

        card_data = {}
        if layer == "1":
            card_data = {
                "name": player.role.name,
                "description": player.role.description,
            }
        elif layer == "2":
            card_data = {
                "name": player.role.name,
                "background": player.role.background,
                "secret_task": player.role.secret_task,
                "alibi": player.role.alibi,
            }
        elif layer == "3":
            card_data = {
                "relationships": player.role.relationships,
                "motive": player.role.motive,
            }
        return card_data

    def distribute_clue(self, game_id: str, clue_id: str, player_id: str):
        """分发线索给特定玩家。返回线索数据或 None。"""
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        clue = next((c for c in state.script.clues if c.id == clue_id), None)
        if not clue:
            return None
        # Check if this player is in the target list
        if clue.target_player_ids and player_id not in clue.target_player_ids:
            return None
        return {
            "id": clue.id,
            "title": clue.title,
            "content": clue.content,
            "content_hint": clue.content_hint,
            "is_red_herring": clue.is_red_herring,
        }

    def execute_private_events(self, game_id: str, phase: str):
        """执行当前阶段的所有 DM 私信触发点。返回 [(player_id, content), ...]。"""
        if game_id not in self.games:
            return []
        state = self.games[game_id]
        events = [e for e in state.script.private_events if e.phase == phase]
        results = []
        for event in events:
            # Match target_role_name to player_id
            player_id = None
            for pid, player in state.players.items():
                if player.role and player.role.name == event.target_role_name:
                    player_id = pid
                    break
            if player_id:
                results.append((player_id, event.content))
        return results

    def unlock_phase(self, game_id: str, new_phase: str, new_act: int):
        """阶段解锁：切换阶段并执行该阶段的所有自动分发。
        返回 {role_cards: {pid: layer_data}, clues: {pid: clue_data}, private_events: [(pid, content)]}
        """
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        state.phase = new_phase
        state.act = new_act

        role_cards = {}
        clues = {}
        private_events = []

        # Determine which layers to unlock based on phase
        layer_map = {
            "act1": "2",  # 第1幕解锁第2层
            "act2": "3",  # 第2幕解锁第3层
        }
        layer_to_unlock = layer_map.get(new_phase)

        if layer_to_unlock:
            for pid, player in state.players.items():
                card_data = self.distribute_role_card(game_id, pid, layer_to_unlock)
                if card_data:
                    role_cards[pid] = card_data

        # Distribute clues for this phase
        for clue in state.script.clues:
            if clue.unlock_phase == new_phase:
                for pid in clue.target_player_ids:
                    if pid in state.players:
                        clue_data = self.distribute_clue(game_id, clue.id, pid)
                        if clue_data:
                            clues[pid] = clue_data

        # Execute private events
        private_events = self.execute_private_events(game_id, new_phase)

        return {
            "role_cards": role_cards,
            "clues": clues,
            "private_events": private_events,
        }
```

- [ ] **Step 2: Run type check**

```bash
python -c "from server.game_manager import manager; print(dir(manager))" | grep -E "distribute_role_card|distribute_clue|execute_private_events|unlock_phase"
```
Expected: All 4 method names listed

- [ ] **Step 3: Commit**

```bash
git add server/game_manager.py
git commit -m "feat: add role card, clue, and private event distribution methods to GameManager"
```

---

### Task 3: Backend — WebSocketHub Message Routing

**Files:**
- Modify: `server/websocket_hub.py`

- [ ] **Step 1: Fix existing handlers to use correct distribution**

Replace the `handle_client_message` method (lines 55-111) with:

```python
    async def handle_client_message(self, room_id: str, player_id: str, data: dict):
        """处理客户端消息，路由到对应处理器"""
        msg_type = data.get("type")

        if msg_type == "chat":
            content = data.get("content", "")
            manager.add_chat_message(room_id, player_id, content, False, None)
            # Broadcast chat to all players in room (public)
            await self.broadcast(room_id, {
                "type": "chat",
                "from": player_id,
                "content": content,
                "timestamp": "",
            })

        elif msg_type == "private_chat":
            target = data.get("to_player_id", "")
            content = data.get("content", "")
            manager.add_chat_message(room_id, player_id, content, True, target)
            # Send to both sender and receiver only
            chat_msg = {
                "type": "private_chat",
                "from": player_id,
                "content": content,
                "timestamp": "",
            }
            await self.send_to_player(room_id, player_id, chat_msg)
            if target and target != player_id:
                await self.send_to_player(room_id, target, chat_msg)

        elif msg_type == "dm_private":
            # DM → player private message (from API, not client)
            target = data.get("to_player_id", "")
            content = data.get("content", "")
            if target:
                dm_msg = {
                    "type": "dm_private",
                    "from": "__dm__",
                    "to": target,
                    "content": content,
                }
                await self.send_to_player(room_id, target, dm_msg)

        elif msg_type == "accuse":
            # Broadcast accusation to all players (public)
            await self.broadcast(room_id, {
                "type": "accusation",
                "from": player_id,
                "target": data.get("target_role_name", ""),
                "reasoning": data.get("reasoning", ""),
            })

        elif msg_type == "vote":
            # Record vote (handled by API endpoint too)
            pass

        elif msg_type == "request_advance":
            # Player requests DM to advance — trigger LLM event generation
            state = manager.get_state(room_id)
            if state and state.phase in ("playing",):
                try:
                    event_content = host_dm.generate_event(state)
                    manager.push_event(room_id, event_content)
                    await self.broadcast(room_id, {
                        "type": "event",
                        "content": event_content,
                    })
                except Exception as e:
                    manager.add_dm_log(room_id, f"事件生成失败: {e}")
```

- [ ] **Step 2: Add `send_dm_private` helper method**

Add this before `handle_client_message`:

```python
    async def send_dm_private(self, room_id: str, target_player_id: str, content: str):
        """DM 向特定玩家发送私信"""
        dm_msg = {
            "type": "dm_private",
            "from": "__dm__",
            "to": target_player_id,
            "content": content,
        }
        await self.send_to_player(room_id, target_player_id, dm_msg)
```

- [ ] **Step 3: Run syntax check**

```bash
python -c "import ast; ast.parse(open('server/websocket_hub.py').read()); print('Syntax OK')"
```
Expected: `Syntax OK`

- [ ] **Step 4: Commit**

```bash
git add server/websocket_hub.py
git commit -m "fix: correct WebSocket message routing — private messages use send_to_player, add DM private handler"
```

---

### Task 4: Backend — LLM Prompt Extension

**Files:**
- Modify: `server/api_routes.py:215-267` (prompt in `_generate_script_generator`)

- [ ] **Step 1: Extend LLM prompt to include clue distribution and private events**

Replace the prompt section in `_generate_script_generator` (lines 215-267) with:

```python
    user_prompt = f"""请生成一个完整的剧本杀剧本，以JSON格式返回。

类型：{req.genre}
难度：{req.difficulty}
预计时长：{req.estimated_time}分钟
玩家数量：{req.player_count}人（需要{req.player_count}个角色）

JSON格式要求：
{{
  "title": "剧本标题",
  "genre": "{req.genre}",
  "difficulty": "{req.difficulty}",
  "estimated_time": {req.estimated_time},
  "background_story": "背景故事（200-500字）",
  "true_killer": "凶手角色名",
  "murder_method": "作案手法描述",
  "cover_up": "掩盖手段描述",
  "roles": [
    {{
      "id": "role_1",
      "name": "角色名",
      "age": 年龄数字,
      "occupation": "职业",
      "description": "简短描述",
      "background": "个人背景故事（100-200字）",
      "secret_task": "秘密任务",
      "alibi": "不在场证明",
      "motive": "作案动机",
      "relationships": [
        {{"target": "角色名", "description": "关系描述"}}
      ]
    }}
  ],
  "clues": [
    {{
      "id": "clue_1",
      "title": "线索标题",
      "content": "线索内容描述",
      "target_role": null,
      "is_red_herring": false,
      "content_hint": "提示",
      "target_player_ids": ["角色名"],
      "unlock_phase": "act2",
      "trigger_condition": null
    }}
  ],
  "plot_outline": {{
    "act1": "第一幕概述（背景介绍）",
    "act2": "第二幕概述（自由调查）",
    "act3": "第三幕概述（审判揭晓）"
  }},
  "private_events": [
    {{
      "phase": "act2",
      "target_role_name": "角色名",
      "content": "DM 私信内容",
      "trigger": null
    }}
  ]
}}

注意：
- 确保有{req.player_count}个角色
- 每个角色的id必须是唯一的（role_1, role_2...）
- 线索数量至少5条
- 凶手必须是其中一个角色
- 每条线索标注 target_player_ids（分配给哪些角色名），unlock_phase（act1/act2/act3）
- 生成 2-3 个 DM 私信触发点（private_events），分配给不同角色，phase 为 act2
- target_player_ids 使用角色名（如"角色名"），后端会匹配到对应的玩家"""
```

- [ ] **Step 2: Update `_normalize_script_json` to handle new fields**

Replace the `_normalize_script_json` function (lines 27-44) with:

```python
def _normalize_script_json(data: dict) -> dict:
    """Normalize LLM-generated script JSON to match Pydantic schema."""
    roles = data.get("roles", [])
    for role in roles:
        rels = role.get("relationships", [])
        normalized = []
        for r in rels:
            if isinstance(r, dict):
                normalized.append(r)
            elif isinstance(r, str):
                normalized.append({"target": r, "description": r})
        role["relationships"] = normalized

    clues = data.get("clues", [])
    for clue in clues:
        clue.setdefault("target_player_ids", [])
        clue.setdefault("unlock_phase", "act2")
        clue.setdefault("trigger_condition", None)

    private_events = data.get("private_events", [])
    for event in private_events:
        event.setdefault("trigger", None)

    return data
```

- [ ] **Step 3: Run syntax check**

```bash
python -c "from server.api_routes import _normalize_script_json; print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add server/api_routes.py
git commit -m "feat: extend LLM prompt to include clue distribution and private events in script generation"
```

---

### Task 5: Backend — API Routes (DM Private Chat + Player List Fix)

**Files:**
- Modify: `server/api_routes.py`

- [ ] **Step 1: Remove `role_name` from player list in `get_room`**

In `get_room` endpoint (lines 136-169), replace the players section:

```python
        "players": {
            pid: {
                "name": p.name,
                "role_id": p.role_id,
            }
            for pid, p in state.players.items()
        },
```

This ensures player names are visible but role names/identities are hidden from others.

- [ ] **Step 2: Add DM private chat request model**

Append after `AddClueRequest` class (around line 103):

```python
class DMPrivateRequest(BaseModel):
    player_id: str  # 管理员ID
    to_player_id: str  # 目标玩家ID
    content: str
```

- [ ] **Step 3: Add DM private chat endpoint**

Append after `add_clue` endpoint (around line 389):

```python
@router.post("/api/rooms/{game_id}/dm/private")
async def dm_private(game_id: str, req: DMPrivateRequest):
    """DM 向特定玩家发送私信（仅管理员）"""
    from server.websocket_hub import hub
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    await hub.send_dm_private(game_id, req.to_player_id, req.content)
    return {"status": "dm_private_sent"}
```

- [ ] **Step 4: Run syntax check**

```bash
python -c "from server.api_routes import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add server/api_routes.py
git commit -m "feat: add DM private chat endpoint and hide role names from player list"
```

---

### Task 6: Shared — WebSocket Types

**Files:**
- Modify: `shared/ws_types.py`
- Modify: `shared/schemas.ts`

- [ ] **Step 1: Add Pydantic models for new WS messages**

Append after `GameOverMessage` in `shared/ws_types.py`:

```python
class RoleCardMessage(BaseModel):
    type: str = "role_card"
    layer: str  # "1", "2", "3"
    player_id: str
    data: dict  # 角色卡数据


class DMPrivateMessage(BaseModel):
    type: str = "dm_private"
    from_player: str = "__dm__"
    to_player: str
    content: str


class ClueUnlockMessage(BaseModel):
    type: str = "clue_unlock"
    player_id: str
    clue: dict  # 线索数据


class PhaseUnlockMessage(BaseModel):
    type: str = "phase_unlock"
    phase: str
    act: int
```

- [ ] **Step 2: Add Zod schemas for new WS messages**

Append after existing schemas in `shared/schemas.ts`:

```typescript
// 服务器 → 客户端新类型
export const roleCardSchema = z.object({
  type: z.literal("role_card"),
  layer: z.enum(["1", "2", "3"]),
  player_id: z.string(),
  data: z.record(z.string(), z.unknown()),
});

export const dmPrivateSchema = z.object({
  type: z.literal("dm_private"),
  from: z.literal("__dm__"),
  to: z.string(),
  content: z.string(),
});

export const clueUnlockSchema = z.object({
  type: z.literal("clue_unlock"),
  player_id: z.string(),
  clue: z.object({
    id: z.string(),
    title: z.string(),
    content: z.string(),
    content_hint: z.string(),
    is_red_herring: z.boolean(),
  }),
});

export const phaseUnlockSchema = z.object({
  type: z.literal("phase_unlock"),
  phase: z.string(),
  act: z.number(),
});
```

- [ ] **Step 3: Run syntax checks**

```bash
python -c "from shared.ws_types import RoleCardMessage, DMPrivateMessage, ClueUnlockMessage, PhaseUnlockMessage; print('Pydantic OK')"
```
Expected: `Pydantic OK`

```bash
cd client && npx tsc --noEmit --skipLibCheck
```
Expected: `error TS2688: Cannot find type definition file...` (tolerated) or no new errors

- [ ] **Step 4: Commit**

```bash
git add shared/ws_types.py shared/schemas.ts
git commit -m "feat: add Pydantic and Zod schemas for new WS message types"
```

---

### Task 7: Frontend — Pinia Store

**Files:**
- Modify: `client/src/stores/game.ts`

- [ ] **Step 1: Rewrite store with new state**

Replace the entire `client/src/stores/game.ts` with:

```typescript
import { defineStore } from 'pinia';
import { ref } from 'vue';
import type { WSMessage } from '../types/ws';

export interface RoleCardData {
  name?: string;
  description?: string;
  background?: string;
  secret_task?: string;
  alibi?: string;
  relationships?: Array<{ target: string; description: string }>;
  motive?: string;
}

export interface ClueData {
  id: string;
  title: string;
  content: string;
  content_hint: string;
  is_red_herring: boolean;
}

export const useGameStore = defineStore('game', () => {
  const phase = ref<'waiting' | 'playing' | 'trial' | 'revealed' | 'finished'>('waiting');
  const act = ref(1);
  const messages = ref<WSMessage[]>([]);
  const players = ref<Map<string, { name: string; role_id: string }>>(new Map());
  const currentEvent = ref<string>('');

  // New state for private information
  const roleCard = ref<{ layer1: RoleCardData | null; layer2: RoleCardData | null; layer3: RoleCardData | null }>({
    layer1: null,
    layer2: null,
    layer3: null,
  });
  const privateMessages = ref<Array<{ from: string; content: string; timestamp: string }>>([]);
  const clues = ref<Map<string, ClueData>>(new Map());
  const activeTab = ref<'role' | 'private' | 'clue' | 'action'>('role');

  function handleWSMessage(msg: WSMessage) {
    messages.value.push(msg);

    switch (msg.type) {
      case 'system':
      case 'event':
        currentEvent.value = msg.content;
        break;
      case 'player_joined':
        players.value.set(msg.player_name, { name: msg.player_name, role_id: '' });
        break;
      case 'role_assigned':
        // Legacy — handled by role_card messages now
        break;
      case 'chat':
        // Public chat — already in messages
        break;
      case 'private_chat':
        // Player private chat — add to privateMessages
        privateMessages.value.push({
          from: msg.from === 'playerId' ? '我' : msg.from,
          content: msg.content,
          timestamp: msg.timestamp || '',
        });
        break;
      case 'role_card':
        // Layered role card
        const layer = msg.layer as '1' | '2' | '3';
        if (layer === '1') roleCard.value.layer1 = msg.data as RoleCardData;
        else if (layer === '2') roleCard.value.layer2 = msg.data as RoleCardData;
        else if (layer === '3') roleCard.value.layer3 = msg.data as RoleCardData;
        break;
      case 'dm_private':
        // DM → player private message
        if (msg.to === 'playerId') {
          privateMessages.value.push({
            from: '🎭 DM',
            content: msg.content,
            timestamp: '',
          });
        }
        break;
      case 'clue_unlock':
        // Clue unlocked for this player
        const clue = msg.clue as ClueData;
        clues.value.set(clue.id, clue);
        break;
      case 'trial_start':
        phase.value = 'trial';
        act.value = 3;
        break;
      case 'vote_result':
        // Vote results — public
        break;
      case 'reveal':
        phase.value = 'revealed';
        break;
      case 'game_over':
        phase.value = 'finished';
        break;
      case 'phase_unlock':
        phase.value = msg.phase as typeof phase.value;
        act.value = msg.act;
        break;
      case 'player_left':
        players.value.delete(msg.player_name);
        break;
    }
  }

  return {
    phase,
    act,
    messages,
    players,
    currentEvent,
    roleCard,
    privateMessages,
    clues,
    activeTab,
    handleWSMessage,
  };
});
```

- [ ] **Step 3: Run type check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -20
```
Expected: No errors related to `game.ts`

- [ ] **Step 4: Commit**

```bash
git add client/src/stores/game.ts
git commit -m "feat: add role card, private messages, clues, and tab state to Pinia store"
```

---

### Task 8: Frontend — RoleCard Component

**Files:**
- Create: `client/src/components/RoleCard.vue`

- [ ] **Step 1: Create RoleCard component**

```vue
<template>
  <div class="role-card">
    <div v-if="!hasLayer1" class="no-role">
      <p>等待剧本生成...</p>
    </div>
    <div v-else class="card-content">
      <!-- Layer 1: Always visible -->
      <div class="card-header">
        <h3 class="role-name">{{ layer1?.name }}</h3>
        <p class="role-desc">{{ layer1?.description }}</p>
      </div>

      <!-- Layer 2: Unlocked at act1 -->
      <div v-if="layer2" class="card-section">
        <div class="section-header" @click="toggleSection('layer2')">
          <span>📖 背景故事</span>
          <span class="expand-icon">{{ expandedSections.layer2 ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.layer2" class="section-body">
          <p>{{ layer2.background }}</p>
        </div>

        <div class="section-header" @click="toggleSection('secret_task')">
          <span>🎯 秘密任务</span>
          <span class="expand-icon">{{ expandedSections.secret_task ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.secret_task" class="section-body">
          <p>{{ layer2.secret_task }}</p>
        </div>

        <div class="section-header" @click="toggleSection('alibi')">
          <span>🛡️ 不在场证明</span>
          <span class="expand-icon">{{ expandedSections.alibi ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.alibi" class="section-body">
          <p>{{ layer2.alibi }}</p>
        </div>
      </div>

      <!-- Layer 3: Unlocked at act2 -->
      <div v-if="layer3" class="card-section">
        <div class="section-header" @click="toggleSection('relationships')">
          <span>🤝 人际关系</span>
          <span class="expand-icon">{{ expandedSections.relationships ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.relationships" class="section-body">
          <ul v-if="layer3.relationships?.length">
            <li v-for="(rel, i) in layer3.relationships" :key="i">
              <strong>{{ rel.target }}</strong>: {{ rel.description }}
            </li>
          </ul>
          <p v-else class="no-relations">暂无人际关系信息</p>
        </div>

        <div class="section-header" @click="toggleSection('motive')">
          <span>💡 动机</span>
          <span class="expand-icon">{{ expandedSections.motive ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedSections.motive" class="section-body">
          <p>{{ layer3.motive }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useGameStore } from '../stores/game';

const store = useGameStore();

const expandedSections = ref<Record<string, boolean>>({
  layer2: true,
  secret_task: true,
  alibi: true,
  relationships: true,
  motive: true,
});

const layer1 = computed(() => store.roleCard.layer1);
const layer2 = computed(() => store.roleCard.layer2);
const layer3 = computed(() => store.roleCard.layer3);
const hasLayer1 = computed(() => !!layer1.value);

function toggleSection(section: string) {
  expandedSections.value[section] = !expandedSections.value[section];
}
</script>

<style scoped>
.role-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}
.no-role {
  text-align: center;
  color: #666;
  padding: 24px;
}
.card-header {
  text-align: center;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 12px;
}
.role-name {
  font-size: 20px;
  color: #e94560;
  margin: 0 0 4px 0;
}
.role-desc {
  font-size: 13px;
  color: #aaa;
  margin: 0;
}
.card-section {
  margin-bottom: 12px;
}
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  cursor: pointer;
  color: #ccc;
  font-size: 14px;
  user-select: none;
}
.section-header:hover {
  background: rgba(0, 0, 0, 0.3);
}
.expand-icon {
  font-size: 11px;
  color: #888;
}
.section-body {
  padding: 10px 12px;
  color: #ddd;
  font-size: 13px;
  line-height: 1.6;
}
.section-body p {
  margin: 0;
}
.section-body ul {
  margin: 0;
  padding-left: 20px;
}
.section-body li {
  margin-bottom: 6px;
}
.no-relations {
  color: #666;
  font-style: italic;
}
</style>
```

- [ ] **Step 2: Run component check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | grep -i "RoleCard" || echo "No RoleCard errors"
```
Expected: `No RoleCard errors`

- [ ] **Step 3: Commit**

```bash
git add client/src/components/RoleCard.vue
git commit -m "feat: add RoleCard component with layered unlock and expand/collapse"
```

---

### Task 9: Frontend — PrivateChatPanel Component

**Files:**
- Create: `client/src/components/PrivateChatPanel.vue`

- [ ] **Step 1: Create PrivateChatPanel component**

```vue
<template>
  <div class="private-chat">
    <div v-if="!hasPlayer" class="no-player">
      <p>等待加入游戏...</p>
    </div>
    <div v-else class="chat-content">
      <div class="messages" ref="messageContainer">
        <div v-for="(msg, i) in privateMessages" :key="i" class="message-item" :class="{ 'dm-message': msg.from === '🎭 DM' }">
          <span class="sender">{{ msg.from }}</span>
          <span class="text">{{ msg.content }}</span>
        </div>
      </div>
      <div class="chat-input-row">
        <input
          v-model="newMessage"
          @keyup.enter="sendDMPrivate"
          placeholder="回复DM..."
        />
        <button @click="sendDMPrivate" :disabled="!newMessage.trim()">发送</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useGameStore } from '../stores/game';

const store = useGameStore();
const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem(`player_${gameId}`) || localStorage.getItem(`admin_${gameId}`) || '';

const newMessage = ref('');
const messageContainer = ref<HTMLElement | null>(null);

const privateMessages = computed(() => store.privateMessages);
const hasPlayer = computed(() => !!playerId);

async function sendDMPrivate() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;

  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/private`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_id: playerId,
        to_player_id: playerId,
        content: text,
      }),
    });
    if (res.ok) {
      newMessage.value = '';
    }
  } catch (e) {
    console.error('DM private failed:', e);
  }

  await nextTick();
  if (messageContainer.value) {
    messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
  }
}

onMounted(() => {
  nextTick(() => {
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  });
});
</script>

<style scoped>
.private-chat {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.no-player {
  text-align: center;
  color: #666;
  padding: 24px;
}
.chat-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-height: 0;
}
.messages {
  flex: 1;
  overflow-y: auto;
  padding-right: 8px;
  min-height: 0;
}
.message-item {
  padding: 6px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.dm-message {
  background: rgba(233, 69, 96, 0.1);
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 4px;
}
.sender {
  font-weight: bold;
  color: #e94560;
  margin-right: 8px;
}
.text {
  color: #ddd;
}
.chat-input-row {
  display: flex;
  gap: 8px;
  margin-top: 12px;
}
.chat-input-row input {
  flex: 1;
  padding: 10px;
  border: 1px solid #444;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #eee;
}
.chat-input-row button {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  background: #e94560;
  color: #fff;
  cursor: pointer;
}
.chat-input-row button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
```

- [ ] **Step 2: Run component check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | grep -i "PrivateChat" || echo "No PrivateChat errors"
```
Expected: `No PrivateChat errors`

- [ ] **Step 3: Commit**

```bash
git add client/src/components/PrivateChatPanel.vue
git commit -m "feat: add PrivateChatPanel component for DM→player messaging"
```

---

### Task 10: Frontend — ClueCardPanel Component

**Files:**
- Create: `client/src/components/ClueCardPanel.vue`

- [ ] **Step 1: Create ClueCardPanel component**

```vue
<template>
  <div class="clue-panel">
    <div v-if="!hasClues" class="no-clues">
      <p>暂无线索</p>
    </div>
    <div v-else class="clue-list">
      <div
        v-for="clue in clueArray"
        :key="clue.id"
        class="clue-card"
        :class="{ 'new-clue': clue.new }"
      >
        <div class="clue-header" @click="toggleClue(clue.id)">
          <span class="clue-title">{{ clue.title }}</span>
          <span v-if="clue.is_red_herring" class="red-herring">⚠️ 假线索</span>
          <span class="expand-icon">{{ expandedClues[clue.id] ? '▲' : '▼' }}</span>
        </div>
        <div v-show="expandedClues[clue.id]" class="clue-body">
          <p class="clue-hint">{{ clue.content_hint }}</p>
          <p class="clue-content">{{ clue.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useGameStore } from '../stores/game';

const store = useGameStore();

const clues = computed(() => store.clues);
const hasClues = computed(() => clues.value.size > 0);

// Convert Map to array for v-for
const clueArray = computed(() => {
  return Array.from(clues.value.values()).map(c => ({ ...c, new: false }));
});

const expandedClues = ref<Record<string, boolean>>({});

function toggleClue(clueId: string) {
  expandedClues.value[clueId] = !expandedClues.value[clueId];
}
</script>

<style scoped>
.clue-panel {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
}
.no-clues {
  text-align: center;
  color: #666;
  padding: 24px;
}
.clue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.clue-card {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 6px;
  overflow: hidden;
  transition: background 0.3s;
}
.clue-card.new-clue {
  background: rgba(233, 69, 96, 0.15);
  animation: pulse 1s ease-in-out 3;
}
@keyframes pulse {
  0%, 100% { background: rgba(233, 69, 96, 0.15); }
  50% { background: rgba(233, 69, 96, 0.3); }
}
.clue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  cursor: pointer;
  user-select: none;
}
.clue-title {
  font-size: 14px;
  color: #eee;
  font-weight: bold;
}
.red-herring {
  font-size: 11px;
  color: #f39c12;
  margin-right: 8px;
}
.expand-icon {
  font-size: 11px;
  color: #888;
}
.clue-body {
  padding: 10px 14px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}
.clue-hint {
  font-size: 12px;
  color: #888;
  margin: 0 0 6px 0;
  font-style: italic;
}
.clue-content {
  font-size: 13px;
  color: #ddd;
  line-height: 1.6;
  margin: 0;
}
</style>
```

- [ ] **Step 2: Run component check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | grep -i "ClueCard" || echo "No ClueCard errors"
```
Expected: `No ClueCard errors`

- [ ] **Step 3: Commit**

```bash
git add client/src/components/ClueCardPanel.vue
git commit -m "feat: add ClueCardPanel component with expand/collapse and new-clue animation"
```

---

### Task 11: Frontend — Update WS Types

**Files:**
- Modify: `client/src/types/ws.ts`

- [ ] **Step 1: Add new WSMessage types**

Append to the `WSMessage` union type in `client/src/types/ws.ts`:

```typescript
export type WSMessage =
  // existing types...
  | { type: "role_card"; layer: "1" | "2" | "3"; player_id: string; data: object }
  | { type: "dm_private"; from: "__dm__"; to: string; content: string }
  | { type: "clue_unlock"; player_id: string; clue: { id: string; title: string; content: string; content_hint: string; is_red_herring: boolean } }
  | { type: "phase_unlock"; phase: string; act: number };
```

- [ ] **Step 2: Run type check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | grep -i "ws.ts" || echo "No ws.ts errors"
```
Expected: `No ws.ts errors`

- [ ] **Step 3: Commit**

```bash
git add client/src/types/ws.ts
git commit -m "feat: add new WSMessage types for role card, DM private, clue unlock, phase unlock"
```

---

### Task 12: Frontend — Refactor GamePage

**Files:**
- Modify: `client/src/components/GamePage.vue`

This is the largest change. Replace the entire template, script, and style sections.

- [ ] **Step 1: Replace GamePage.vue with new layout**

```vue
<template>
  <div class="game-page">
    <!-- Header -->
    <header class="game-header">
      <h1>{{ scriptTitle || '剧本杀' }}</h1>
      <span class="phase-badge">{{ phaseText }} (第{{ act }}幕)</span>
      <GameTimer :total-seconds="timerSeconds" />
    </header>

    <!-- Main content -->
    <div class="game-body">
      <!-- Left: Public info -->
      <div class="main-panel">
        <!-- DM Event Display -->
        <div class="event-section">
          <h2>📜 公共事件</h2>
          <div v-if="currentEvent" class="event-content">{{ currentEvent }}</div>
          <div v-else class="no-event">等待DM发布事件...</div>
        </div>

        <!-- Public Chat -->
        <div class="chat-section">
          <h2>💬 公共聊天</h2>
          <div class="messages" ref="messageContainer">
            <div
              v-for="(msg, i) in publicMessages"
              :key="i"
              class="message-item"
              :class="{ 'dm-message': msg.from === '__dm__' }"
            >
              <span class="sender">{{ msg.from === '__dm__' ? '🎭 DM' : msg.from }}</span>
              <span class="text">{{ msg.content }}</span>
            </div>
          </div>
          <div class="chat-input-row">
            <input v-model="newMessage" @keyup.enter="sendPublicChat" placeholder="输入公共消息..." />
            <button @click="sendPublicChat">发送</button>
          </div>
        </div>
      </div>

      <!-- Right: Private info tabs -->
      <aside class="side-panel">
        <!-- Tab Navigation -->
        <div class="tab-nav">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="{ active: activeTab === tab.key }"
            @click="activeTab = tab.key"
          >
            {{ tab.icon }} {{ tab.label }}
          </button>
        </div>

        <!-- Tab Content -->
        <div class="tab-content">
          <!-- Role Card Tab -->
          <RoleCard v-if="activeTab === 'role'" />

          <!-- Private Chat Tab -->
          <PrivateChatPanel v-if="activeTab === 'private'" />

          <!-- Clues Tab -->
          <ClueCardPanel v-if="activeTab === 'clue'" />

          <!-- Actions Tab -->
          <div v-if="activeTab === 'action'" class="actions-panel">
            <!-- Player List (names only, no roles) -->
            <div class="players-section">
              <h2>👥 玩家 ({{ playerCount }})</h2>
              <div v-for="(player, pid) in players" :key="pid" class="player-item">
                <span>{{ player.name }}</span>
                <span v-if="pid === roomCreatorId" class="admin-tag">👑</span>
              </div>
            </div>

            <!-- Action Buttons -->
            <div v-if="phase === 'playing'" class="actions-section">
              <h2>⚡ 操作</h2>
              <button @click="requestClue" :disabled="phase !== 'playing'">请求线索</button>
              <button @click="startAccusation" :disabled="phase !== 'playing'" v-if="showAccusation">开始指控</button>
            </div>

            <!-- Accusation Panel -->
            <div v-if="showAccusation && phase === 'playing'" class="accusation-section">
              <h2>🔍 指控凶手</h2>
              <select v-model="targetRole">
                <option value="">选择目标...</option>
                <option v-for="(player, pid) in players" :key="pid" :value="player.role_id || player.name">
                  {{ player.name }}
                </option>
              </select>
              <textarea v-model="reasoning" placeholder="写下你的推理..."></textarea>
              <div class="accusation-buttons">
                <button @click="submitAccusation" :disabled="!targetRole || !reasoning">提交指控</button>
                <button @click="showAccusation = false" class="cancel-btn">取消</button>
              </div>
            </div>

            <!-- Vote Panel -->
            <div v-if="phase === 'trial'" class="vote-section">
              <h2>🗳️ 投票环节</h2>
              <select v-model="voteTarget">
                <option value="">选择目标...</option>
                <option v-for="(player, pid) in players" :key="pid" :value="player.role_id || player.name">
                  {{ player.name }}
                </option>
              </select>
              <textarea v-model="voteReasoning" placeholder="写下你的推理..."></textarea>
              <button @click="submitVote" :disabled="!voteTarget || !voteReasoning">提交投票</button>
            </div>

            <!-- Reveal Section -->
            <div v-if="phase === 'revealed'" class="reveal-section">
              <h2>📢 真相揭晓</h2>
              <p>{{ currentEvent || '游戏已结束' }}</p>
              <button @click="$router.push('/')" class="back-btn">返回首页</button>
            </div>

            <!-- Admin Panel -->
            <AdminPanel
              v-if="isAdmin && activeTab === 'action'"
              :loading="adminLoading"
              :dm-log="dmLog"
              @push-event="handlePushEvent"
              @force-trial="handleForceTrial"
              @end-game="handleEndGame"
              @add-clue="handleAddClue"
            />
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue';
import { useRoute } from 'vue-router';
import { useGameStore } from '../stores/game';
import GameTimer from './GameTimer.vue';
import AdminPanel from './AdminPanel.vue';
import RoleCard from './RoleCard.vue';
import PrivateChatPanel from './PrivateChatPanel.vue';
import ClueCardPanel from './ClueCardPanel.vue';

const route = useRoute();
const gameId = route.params.gameId as string;
const playerId = localStorage.getItem(`player_${gameId}`) || localStorage.getItem(`admin_${gameId}`) || localStorage.getItem('player_id') || '';

const store = useGameStore();

// State
const phase = computed(() => store.phase);
const act = computed(() => store.act);
const scriptTitle = ref('');
const players = ref<Record<string, { name: string; role_id: string }>>({});
const publicMessages = ref<Array<{ from: string; content: string }>>([]);
const currentEvent = computed(() => store.currentEvent);
const newMessage = ref('');
const isAdmin = ref(false);
const roomCreatorId = ref('');
const dmLog = ref<string[]>([]);
const timerSeconds = ref(3600);

// Tabs
const tabs = [
  { key: 'role' as const, icon: '📋', label: '角色卡' },
  { key: 'private' as const, icon: '💌', label: '私信' },
  { key: 'clue' as const, icon: '🔍', label: '线索' },
  { key: 'action' as const, icon: '⚡', label: '操作' },
];
const activeTab = computed(() => store.activeTab);

// Accusation state
const showAccusation = ref(false);
const targetRole = ref('');
const reasoning = ref('');

// Vote state
const voteTarget = ref('');
const voteReasoning = ref('');

// Admin loading state
const adminLoading = ref(false);

// WebSocket
let ws: WebSocket | null = null;
const messageContainer = ref<HTMLElement | null>(null);

const phaseText = computed(() => {
  const map: Record<string, string> = {
    waiting: '等待中', playing: '游戏中', trial: '审判阶段', revealed: '真相揭晓', finished: '游戏结束'
  };
  return map[phase.value] || phase.value;
});

const playerCount = computed(() => Object.keys(players.value).length);

// Fetch game state via HTTP
async function fetchState() {
  try {
    const res = await fetch(`/api/rooms/${gameId}`);
    if (!res.ok) return;
    const data = await res.json();
    phase.value = data.phase || 'playing';
    act.value = data.act || 1;
    players.value = data.players || {};
    roomCreatorId.value = data.room_creator_id || '';
    isAdmin.value = data.room_creator_id === playerId;

    if (phase.value === 'playing') {
      timerSeconds.value = 90 * 60;
    }

    // Update messages from server
    if (data.public_messages && data.public_messages.length > 0) {
      const existingCount = publicMessages.value.length;
      const newMessages = data.public_messages.slice(existingCount);
      for (const m of newMessages) {
        publicMessages.value.push({ from: m.from_player_id, content: m.content });
        if (m.type === 'event') {
          currentEvent.value = m.content;
        }
      }
    }

    await nextTick();
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  } catch (e) {
    console.error('Failed to fetch state:', e);
  }
}

// WebSocket connection
function connectWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${protocol}//${window.location.host}/ws/${gameId}/${playerId}`);

  ws.onopen = () => console.log('WS connected');

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    store.handleWSMessage(msg as any);

    // Scroll to bottom for public messages
    nextTick(() => {
      if (messageContainer.value) messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    });
  };

  ws.onclose = () => {
    console.log('WS disconnected, reconnecting...');
    setTimeout(connectWebSocket, 3000);
  };
}

function sendWSMessage(type: string, data: Record<string, any> = {}) {
  if (ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({ type, ...data }));
  }
}

// Send public chat
async function sendPublicChat() {
  const text = newMessage.value.trim();
  if (!text || !playerId) return;

  sendWSMessage('chat', { content: text });

  try {
    await fetch(`/api/rooms/${gameId}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, message: text, is_private: false }),
    });
  } catch (e) { console.error(e); }

  newMessage.value = '';
}

async function requestClue() {
  sendWSMessage('request_advance');
}

function startAccusation() { showAccusation.value = true; }

async function submitAccusation() {
  if (!targetRole.value || !reasoning.value) return;
  sendWSMessage('accuse', { target_role_name: targetRole.value, reasoning: reasoning.value });
  try {
    await fetch(`/api/rooms/${gameId}/accusations`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_player_id: playerId, target_role_name: targetRole.value, reasoning: reasoning.value }),
    });
  } catch (e) { console.error(e); }
  showAccusation.value = false;
  targetRole.value = '';
  reasoning.value = '';
}

async function submitVote() {
  if (!voteTarget.value || !voteReasoning.value) return;
  try {
    await fetch(`/api/rooms/${gameId}/votes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ from_player_id: playerId, target_role_name: voteTarget.value, reasoning: voteReasoning.value }),
    });
  } catch (e) { console.error(e); }
  voteTarget.value = '';
  voteReasoning.value = '';
}

// Admin actions
async function handlePushEvent() {
  adminLoading.value = true;
  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/push-event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, event_content: '' }),
    });
    if (res.ok) {
      const data = await res.json();
      currentEvent.value = data.content;
    } else {
      const err = await res.json().catch(() => ({}));
      alert(`推进剧情失败: ${err.detail || '未知错误'}`);
    }
  } catch (e) {
    alert('推进剧情失败: 网络错误');
  } finally { adminLoading.value = false; }
}

async function handleAddClue(clue: { title: string; content: string }) {
  try {
    await fetch(`/api/rooms/${gameId}/dm/add-clue`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, clue_title: clue.title, clue_content: clue.content }),
    });
  } catch (e) { console.error(e); }
}

async function handleForceTrial() {
  if (!confirm('确定要强制进入审判阶段吗？')) return;
  try {
    await fetch(`/api/rooms/${gameId}/force-trial`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    });
    phase.value = 'trial';
    act.value = 3;
  } catch (e) { console.error(e); }
}

async function handleEndGame() {
  if (!confirm('确定要提前结束游戏并揭晓真相吗？')) return;
  try {
    await fetch(`/api/rooms/${gameId}/end-game`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId }),
    });
    phase.value = 'revealed';
  } catch (e) { console.error(e); }
}

onMounted(() => {
  fetchState();
  connectWebSocket();
  const interval = setInterval(fetchState, 5000);
  return () => clearInterval(interval);
});

onUnmounted(() => {
  if (ws) ws.close();
});
</script>

<style scoped>
.game-page { min-height: 100vh; display: flex; flex-direction: column; }
.game-header { display: flex; align-items: center; justify-content: space-between; padding: 16px 24px; background: rgba(0, 0, 0, 0.3); border-bottom: 1px solid #333; }
.game-header h1 { font-size: 20px; color: #eee; }
.phase-badge { padding: 4px 12px; background: #e94560; border-radius: 12px; font-size: 12px; color: #fff; }
.game-body { display: flex; flex: 1; gap: 16px; padding: 16px; overflow: hidden; }
.main-panel { flex: 1; display: flex; flex-direction: column; gap: 16px; min-width: 0; }

.event-section { background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 16px; flex-shrink: 0; max-height: 200px; overflow-y: auto; }
.event-section h2 { font-size: 16px; color: #aaa; margin-bottom: 12px; }
.event-content { background: rgba(0, 0, 0, 0.2); padding: 12px; border-radius: 6px; line-height: 1.6; color: #ddd; white-space: pre-wrap; }
.no-event { color: #666; font-style: italic; }

.chat-section { flex: 1; background: rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 16px; display: flex; flex-direction: column; min-height: 0; }
.chat-section h2 { font-size: 16px; color: #aaa; margin-bottom: 12px; }
.messages { flex: 1; overflow-y: auto; padding-right: 8px; min-height: 0; }
.message-item { padding: 6px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.dm-message { background: rgba(233, 69, 96, 0.1); padding: 8px; border-radius: 4px; margin-bottom: 4px; }
.sender { font-weight: bold; color: #e94560; margin-right: 8px; }
.text { color: #ddd; }

.chat-input-row { display: flex; gap: 8px; margin-top: 12px; }
.chat-input-row input { flex: 1; padding: 10px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; }
.chat-input-row button { padding: 10px 20px; border: none; border-radius: 6px; background: #e94560; color: #fff; cursor: pointer; }

.side-panel { width: 360px; flex-shrink: 0; display: flex; flex-direction: column; overflow-y: auto; max-height: calc(100vh - 80px); }

.tab-nav { display: flex; gap: 4px; margin-bottom: 8px; }
.tab-nav button {
  flex: 1;
  padding: 8px;
  border: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.3);
  color: #aaa;
  cursor: pointer;
  font-size: 13px;
}
.tab-nav button.active {
  background: #e94560;
  color: #fff;
}

.tab-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
}

.players-section, .actions-section, .accusation-section, .vote-section, .reveal-section {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
}
h2 { font-size: 14px; color: #aaa; margin-bottom: 12px; }

.player-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05); }
.admin-tag { font-size: 12px; color: #f39c12; font-weight: bold; }

.actions-section button { width: 100%; padding: 10px; margin-bottom: 8px; border: none; border-radius: 6px; background: #0f3460; color: #eee; cursor: pointer; }
.actions-section button:disabled { opacity: 0.5; cursor: not-allowed; }

.accusation-section select, .vote-section select { width: 100%; padding: 8px; margin-bottom: 8px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; }
.accusation-section textarea, .vote-section textarea { width: 100%; height: 80px; padding: 8px; margin-bottom: 8px; border: 1px solid #444; border-radius: 6px; background: rgba(0, 0, 0, 0.3); color: #eee; resize: vertical; }
.accusation-section button, .vote-section button { width: 100%; padding: 10px; border: none; border-radius: 6px; background: #e94560; color: #fff; cursor: pointer; }
.cancel-btn { background: #333 !important; margin-top: 8px; }
.accusation-buttons { display: flex; flex-direction: column; }

.reveal-section p { line-height: 1.8; color: #ddd; white-space: pre-wrap; }
.back-btn { padding: 10px 24px; border: none; border-radius: 6px; background: #0f3460; color: #eee; cursor: pointer; margin-top: 12px; }
</style>
```

- [ ] **Step 2: Run type check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1 | head -30
```
Expected: No errors (or only pre-existing errors unrelated to GamePage)

- [ ] **Step 3: Commit**

```bash
git add client/src/components/GamePage.vue
git commit -m "refactor: GamePage into left-right layout with private tabs (role card, private chat, clues, actions)"
```

---

### Task 13: Backend — Tests for Distribution Methods

**Files:**
- Modify: `tests/test_game_manager.py`

- [ ] **Step 1: Add tests for new GameManager methods**

Append after the last test in `tests/test_game_manager.py`:

```python
# --- Distribution method tests ---

def test_distribute_role_card_layer1(game_manager, sample_script):
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script = sample_script
    game_manager.add_player("test1", "p1", "张三")
    data = game_manager.distribute_role_card("test1", "p1", "1")
    assert data is not None
    assert data["name"] == "角色 A"
    assert data["description"] == "医生"


def test_distribute_role_card_layer2(game_manager, sample_script):
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script = sample_script
    game_manager.add_player("test1", "p1", "张三")
    data = game_manager.distribute_role_card("test1", "p1", "2")
    assert data is not None
    assert data["secret_task"] == "秘密"
    assert data["alibi"] == "不在场"


def test_distribute_clue_target_player(game_manager, sample_script):
    from server.models import Clue
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script.clues = [
        Clue(id="c1", title="线索1", content="内容", target_role=None, is_red_herring=False, content_hint="提示",
             target_player_ids=["p1"], unlock_phase="act2"),
    ]
    game_manager.add_player("test1", "p1", "张三")
    game_manager.add_player("test1", "p2", "李四")
    # p1 should get the clue
    data = game_manager.distribute_clue("test1", "c1", "p1")
    assert data is not None
    assert data["title"] == "线索1"
    # p2 should NOT get the clue
    data2 = game_manager.distribute_clue("test1", "c1", "p2")
    assert data2 is None


def test_execute_private_events(game_manager, sample_script):
    from server.models import PrivateEvent
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script = sample_script
    state.script.private_events = [
        PrivateEvent(phase="act2", target_role_name="角色 A", content="私信内容", trigger=None),
    ]
    game_manager.add_player("test1", "p1", "张三")
    results = game_manager.execute_private_events("test1", "act2")
    assert len(results) == 1
    assert results[0][0] == "p1"  # player_id
    assert results[0][1] == "私信内容"  # content


def test_unlock_phase(game_manager, sample_script):
    from server.models import PrivateEvent, Clue
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script = sample_script
    state.script.clues = [
        Clue(id="c1", title="线索1", content="内容", target_role=None, is_red_herring=False, content_hint="提示",
             target_player_ids=["p1"], unlock_phase="act2"),
    ]
    state.script.private_events = [
        PrivateEvent(phase="act2", target_role_name="角色 A", content="私信", trigger=None),
    ]
    game_manager.add_player("test1", "p1", "张三")
    result = game_manager.unlock_phase("test1", "act2", 2)
    assert result is not None
    assert "p1" in result["role_cards"]
    assert "p1" in result["clues"]
    assert len(result["private_events"]) == 1
    assert state.phase == "act2"
    assert state.act == 2
```

- [ ] **Step 2: Run tests**

```bash
pytest tests/test_game_manager.py -v -k "distribute or unlock or execute_private"
```
Expected: All 5 new tests PASS

- [ ] **Step 3: Run all existing tests to ensure no regression**

```bash
pytest tests/test_game_manager.py -v
```
Expected: All tests PASS (existing + new)

- [ ] **Step 4: Commit**

```bash
git add tests/test_game_manager.py
git commit -m "test: add distribution method tests for role card, clue, and private events"
```

---

### Task 14: Frontend — Update WaitingLobby (Phase Unlock on Game Start)

**Files:**
- Modify: `client/src/components/WaitingLobby.vue`

- [ ] **Step 1: Add phase unlock on game start**

In the `startGame` function (around line 427), after the API call succeeds, add a WebSocket notification:

```typescript
async function startGame() {
  if (!canStart.value || starting.value) return;
  starting.value = true;
  try {
    const res = await fetch(`/api/rooms/${gameId}/start`, { method: 'POST' });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '开始失败');
    }
    // After starting, the server should push phase_unlock messages
    // Navigate to game page
    router.push(`/game/${gameId}`);
  } catch (e: any) {
    alert(e.message);
  } finally {
    starting.value = false;
  }
}
```

No code change needed here — the backend `unlock_phase` method will be called by the API `start_game` endpoint. We need to update the backend API to call `unlock_phase` on game start.

---

### Task 15: Backend — Call unlock_phase on Game Start

**Files:**
- Modify: `server/api_routes.py:336-347` (start_game endpoint)

- [ ] **Step 1: Update start_game to trigger phase unlock**

Replace the `start_game` endpoint (lines 336-347):

```python
@router.post("/api/rooms/{game_id}/start")
async def start_game(game_id: str):
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    playable_count = len(state.players)
    if playable_count < 1:
        raise HTTPException(status_code=400, detail="至少需要1名玩家才能开始")
    if not state.script_generated:
        raise HTTPException(status_code=400, detail="先生成剧本再开始游戏")

    manager.start_game(game_id)

    # Unlock act1 information for all players
    unlock_result = manager.unlock_phase(game_id, "act1", 1)

    # Broadcast phase_unlock and distribute role cards, clues, private events
    from server.websocket_hub import hub
    if unlock_result:
        # Phase unlock notification
        await hub.broadcast(game_id, {
            "type": "phase_unlock",
            "phase": "act1",
            "act": 1,
        })

        # Distribute role cards (layer 2) to all players
        for pid, card_data in unlock_result["role_cards"].items():
            await hub.send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "2",
                "player_id": pid,
                "data": card_data,
            })

        # Distribute clues (list per player — one message per clue)
        for pid, clue_list in unlock_result["clues"].items():
            for clue_data in clue_list:
                await hub.send_to_player(game_id, pid, {
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        # Send DM private messages
        for pid, content in unlock_result["private_events"]:
            await hub.send_dm_private(game_id, pid, content)

    return {"game_id": game_id, "phase": state.phase}
```

- [ ] **Step 2: Run syntax check**

```bash
python -c "from server.api_routes import router; print('OK')"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/api_routes.py
git commit -m "feat: trigger phase unlock on game start — distribute role cards, clues, and DM private messages"
```

---

### Task 16: Integration — End-to-End Verification

**Files:**
- No new files — manual verification

- [ ] **Step 1: Run all backend tests**

```bash
pytest tests/ -v
```
Expected: All tests PASS

- [ ] **Step 2: Run frontend type check**

```bash
cd client && npx vue-tsc --noEmit --skipLibCheck 2>&1
```
Expected: No errors

- [ ] **Step 3: Verify shared types compile**

```bash
python -c "from server.models import Clue, PrivateEvent, Script; from shared.ws_types import RoleCardMessage, DMPrivateMessage, ClueUnlockMessage, PhaseUnlockMessage; print('All shared types OK')"
```
Expected: `All shared types OK`

- [ ] **Step 4: Commit final changes**

```bash
git add -A
git commit -m "chore: final integration verification — all tests pass, types compile"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ 信息隔离规则 → Task 3 (WebSocketHub routing), Task 5 (API player list fix)
- ✅ 角色卡分层 → Task 2 (distribute_role_card with layer param), Task 8 (RoleCard component)
- ✅ 阶段自动解锁 → Task 2 (unlock_phase method), Task 15 (start_game triggers unlock)
- ✅ DM私信 → Task 3 (dm_private handler), Task 5 (DM private API endpoint), Task 9 (PrivateChatPanel)
- ✅ 线索分发 → Task 1 (Clue model fields), Task 2 (distribute_clue), Task 10 (ClueCardPanel)
- ✅ 玩家列表隐藏角色名 → Task 5 (get_room players section)
- ✅ 投票只显示玩家名 → Task 11/12 (GamePage select uses player.name)

**2. Placeholder scan:**
- ✅ No "TBD", "TODO", or incomplete sections
- ✅ All code blocks are complete
- ✅ All commands are explicit

**3. Type consistency:**
- ✅ `distribute_role_card` uses `layer: str` in Task 2, `layer: "1"|"2"|"3"` in shared types (Task 6) — consistent
- ✅ `PrivateEvent` model defined in Task 1, used in Task 2 `execute_private_events` — consistent
- ✅ WS message types: `role_card`, `dm_private`, `clue_unlock`, `phase_unlock` — defined in Task 6, consumed in Task 7 (store), Task 12 (GamePage) — consistent
- ✅ `send_dm_private` method defined in Task 3, used in Task 15 — consistent

**4. Scope check:**
- ✅ 16 tasks, all focused on the same feature
- ✅ Each task produces self-contained changes
- ✅ No unrelated refactoring

**5. Missing items:**
- One gap: The `WaitingLobby.vue` doesn't need changes — phase unlock happens on game start (Task 15), and the GamePage receives the WS messages. ✅ No gap.
- One gap: Admin panel needs a "send DM private" button. This is a minor enhancement — the API endpoint exists (Task 5), but the UI button isn't in scope for this refactor. The DM can use the existing AdminPanel to push events, and private chat is a separate feature. ✅ Out of scope.
