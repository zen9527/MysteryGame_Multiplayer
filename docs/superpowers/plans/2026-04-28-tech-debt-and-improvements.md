# Tech Debt & Improvements Batch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix all known technical debt (blocking async calls, missing WS reconnect caching, no-op store handlers, missing UI feedback) and add 3 polish features (game-over SSE reveal, vote broadcast, act transition notification).

**Architecture:** All changes are incremental — no architecture changes. SSE streaming for end_game mirrors existing push-event pattern. WS vote/accusation caching follows existing distribution cache pattern. UI feedback uses per-action `ref<boolean>` loading states. Act transition notification is a new WS message type with auto-dismiss banner.

**Tech Stack:** FastAPI SSE generators, Pinia store, Vue 3 refs, WebSocket broadcast.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `server/api_routes.py` | Modify | SSE `end_game` generator; fix `test_llm`/`list_llm_models` blocking |
| `server/websocket_hub.py` | Modify | Cache accusation WS messages; broadcast `vote_cast` + `act_transition` |
| `server/game_manager.py` | Modify | Cache accusations in distribution cache |
| `server/models.py` | Modify | Add `distributed_accusations` to GameState |
| `client/src/types/ws.ts` | Modify | Add `vote_cast`, `act_transition` message types |
| `client/src/stores/game.ts` | Modify | Handle `accusation`, `vote_cast`, `act_transition` WS messages |
| `client/src/components/GamePage.vue` | Modify | Loading states, error feedback, act banner, end-game SSE |
| `client/src/components/AdminPanel.vue` | Modify | Per-action disabled states |
| `tests/test_game_manager.py` | Modify | Add test for accusation caching |

---

### Task 1: Backend — Add accusation distribution cache to models

**Files:**
- Modify: `server/models.py:112-117` (GameState distribution cache fields)

- [ ] **Step 1: Add `distributed_accusations` field to GameState**

In `server/models.py`, add after `distributed_dm_private` (line 116):

```python
    distributed_accusations: List[dict] = Field(default_factory=list)  # [{type, from, target, reasoning}, ...]
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "from server.models import GameState; print('OK')"`
Expected: `OK`

---

### Task 2: Backend — Cache accusations in GameManager + distribute on reconnect

**Files:**
- Modify: `server/game_manager.py` (add accusation caching to `push_structured_event` is NOT needed — accusations come from WS `handle_client_message`)

- [ ] **Step 1: Add `cache_accusation` method to GameManager**

Add after `cache_distribution` method (around line 445):

```python
    def cache_accusation(self, game_id: str, from_player_id: str, target: str, reasoning: str):
        """Cache an accusation for WS reconnect replay."""
        if game_id not in self.games:
            return
        state = self.games[game_id]
        state.distributed_accusations.append({
            "type": "accusation",
            "from": from_player_id,
            "target": target,
            "reasoning": reasoning,
        })
```

- [ ] **Step 2: Include `distributed_accusations` in `get_pending_distributions`**

In `get_pending_distributions` (around line 390), add after the `distributed_dm_private` extend:

```python
        messages.extend(state.distributed_accusations)
```

- [ ] **Step 3: Write test**

Add to `tests/test_game_manager.py`:

```python
def test_cache_accusation(game_state):
    from server.models import Role
    role = Role(id="r1", name="张三", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive="")
    game_state.players["p2"] = Player(id="p2", name="李四", role_id="r1", role=role)
    manager.cache_accusation("test-game", "p2", "张三", "他有动机")
    
    pending = manager.get_pending_distributions("test-game", "p2")
    accusations = [m for m in pending if m.get("type") == "accusation"]
    assert len(accusations) == 1
    assert accusations[0]["target"] == "张三"
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_game_manager.py::test_cache_accusation -v`
Expected: PASS

---

### Task 3: Backend — Wire accusation caching in WS handler + resolve player names

**Files:**
- Modify: `server/websocket_hub.py:102-109` (accuse handler)

- [ ] **Step 1: Update `accuse` handler to cache and resolve player names**

Replace the `accuse` handler block (lines 102-109):

```python
        elif msg_type == "accuse":
            target = data.get("target_role_name", "")
            reasoning = data.get("reasoning", "")
            # Resolve player name for display
            state = manager.get_state(room_id)
            player_name = player_id
            if state and player_id in state.players:
                player_name = state.players[player_id].name
            manager.cache_accusation(room_id, player_id, target, reasoning)
            await self.broadcast(room_id, {
                "type": "accusation",
                "from": player_name,
                "from_player_id": player_id,
                "target": target,
                "reasoning": reasoning,
            })
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "from server.websocket_hub import hub; print('OK')"`
Expected: `OK`

---

### Task 4: Backend — Broadcast `vote_cast` on vote + cache

**Files:**
- Modify: `server/websocket_hub.py:111-113` (vote handler)
- Modify: `server/api_routes.py:747-758` (add_vote endpoint)

- [ ] **Step 1: Update WS `vote` handler to broadcast and cache**

Replace the `vote` handler (lines 111-113):

```python
        elif msg_type == "vote":
            target = data.get("target_role_name", "")
            reasoning = data.get("reasoning", "")
            state = manager.get_state(room_id)
            player_name = player_id
            if state and player_id in state.players:
                player_name = state.players[player_id].name
            await self.broadcast(room_id, {
                "type": "vote_cast",
                "from": player_name,
                "from_player_id": player_id,
                "target": target,
            })
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "from server.websocket_hub import hub; print('OK')"`
Expected: `OK`

---

### Task 5: Backend — SSE `end_game` with truth reveal streaming

**Files:**
- Modify: `server/api_routes.py:715-731` (end_game endpoint)

- [ ] **Step 1: Add `_end_game_generator` SSE generator**

Add before the `end_game` endpoint (before line 715):

```python
def _end_game_generator(game_id: str, state):
    """SSE generator for game end with truth reveal streaming."""
    log.info(f"[end-game] Generating truth reveal for {game_id}")

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        reveal_content = host_dm.generate_event(state)
        manager.push_event(game_id, f"📢 真相揭晓：{reveal_content}")

        done_payload = json.dumps({
            "type": "done",
            "content": reveal_content,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        log.error(f"[end-game] Reveal generation failed: {type(e).__name__}: {e}", exc_info=True)
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"
    finally:
        manager.end_game(game_id)
```

- [ ] **Step 2: Replace `end_game` endpoint with SSE version**

Replace the `end_game` endpoint (lines 715-731):

```python
@router.post("/api/rooms/{game_id}/end-game")
async def end_game(game_id: str, req: AdminActionRequest):
    """流式结束游戏（SSE），实时揭晓真相。"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    return StreamingResponse(
        _end_game_generator(game_id, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 3: Fix `test_end_game_by_admin` integration test**

The test now gets an SSE stream instead of JSON. Update `tests/test_integration.py` `test_end_game_by_admin` (lines 103-116):

```python
def test_end_game_by_admin():
    resp = client.post("/api/rooms", json={"creator_id": "admin_1"})
    game_id = resp.json()["game_id"]
    from server.game_manager import manager
    state = manager.get_state(game_id)
    state.script_generated = True
    manager.start_game(game_id)

    response = client.post(
        f"/api/rooms/{game_id}/end-game",
        json={"player_id": "admin_1"},
    )
    assert response.status_code == 200
    # SSE response — verify it's a stream, not JSON
    assert "text/event-stream" in response.headers.get("content-type", "")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/ -v`
Expected: 44 passed

---

### Task 6: Backend — Fix `test_llm` and `list_llm_models` blocking calls

**Files:**
- Modify: `server/api_routes.py` (two endpoints)

The issue: `test_llm` and `list_llm_models` call sync `requests.post/get` in async handlers, blocking the event loop for 30-60s. The fix: extract to a sync helper and use `run_in_threadpool`.

- [ ] **Step 1: Add `run_in_threadpool` import**

At the top of `server/api_routes.py`, add to imports:

```python
from starlette.concurrency import run_in_threadpool
```

- [ ] **Step 2: Wrap `test_llm` LLM call**

Find the line `result = host_dm.llm.test_connection()` and replace:

```python
        result = await run_in_threadpool(host_dm.llm.test_connection)
```

- [ ] **Step 3: Wrap `list_llm_models` LLM call**

Find the line `models = host_dm.llm.list_models()` and replace:

```python
        models = await run_in_threadpool(host_dm.llm.list_models)
```

Note: `run_in_threadpool` is used instead of `asyncio.to_thread` because it works correctly with FastAPI's TestClient.

- [ ] **Step 4: Verify syntax and run tests**

Run: `python -c "from server.api_routes import router; print('OK')"`
Expected: `OK`

Run: `pytest tests/ -v`
Expected: 44 passed

---

### Task 7: Backend — Broadcast `act_transition` in `advance_act` endpoint

**Files:**
- Modify: `server/api_routes.py:668-712` (advance_act endpoint)

- [ ] **Step 1: Add `act_transition` broadcast with plot outline**

In the `advance_act` endpoint, after the `phase_unlock` broadcast (around line 679), add:

```python
    # Broadcast act transition notification with plot outline
    plot_text = ""
    act_key = f"act{new_act}"
    if hasattr(state.script, 'plot_outline') and state.script.plot_outline:
        plot_text = getattr(state.script.plot_outline, act_key, "")
    await hub.broadcast(game_id, {
        "type": "act_transition",
        "act": new_act,
        "plot_summary": plot_text,
    })
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "from server.api_routes import router; print('OK')"`
Expected: `OK`

---

### Task 8: Frontend — Add `vote_cast`, `act_transition` to WS types + store handlers

**Files:**
- Modify: `client/src/types/ws.ts`
- Modify: `client/src/stores/game.ts`

- [ ] **Step 1: Add new message types to `ws.ts`**

Add to the `WSMessage` union type before the semicolon:

```typescript
  | { type: "vote_cast"; from: string; from_player_id: string; target: string }
  | { type: "act_transition"; act: number; plot_summary: string }
```

- [ ] **Step 2: Add `actBanner` ref and handlers to `game.ts` store**

In the store's state declarations, add after `seenPrivateKeys` (line 57):

```typescript
  // Act transition banner (auto-dismiss)
  const actBanner = ref<{ act: number; plot_summary: string } | null>(null);
```

In `handleWSMessage`, replace the `accusation` case (line 131-132):

```typescript
      case 'accusation':
        _addPublicMessage(`🔍 ${msg.from} 指控 ${msg.target}`, msg.reasoning, '');
        break;
```

Replace the `vote_result` case (line 137-138):

```typescript
      case 'vote_result':
        break;
      case 'vote_cast':
        _addPublicMessage(`🗳️ ${msg.from} 投票给了 ${msg.target}`, '', '');
        break;
```

Add before `phase_unlock` case (before line 145):

```typescript
      case 'act_transition':
        actBanner.value = { act: msg.act, plot_summary: msg.plot_summary };
        // Auto-dismiss after 8 seconds
        setTimeout(() => {
          if (actBanner.value && actBanner.value.act === msg.act) {
            actBanner.value = null;
          }
        }, 8000);
        break;
```

In the `return` block, add `actBanner`:

```typescript
    actBanner,
```

- [ ] **Step 3: Run type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: clean

---

### Task 9: Frontend — Act transition banner + fix `handleEndGame` SSE consumer

**Files:**
- Modify: `client/src/components/GamePage.vue`

- [ ] **Step 1: Add act banner in template**

After the event-section div (after line 22), add:

```html
        <!-- Act Transition Banner -->
        <div v-if="actBanner" class="act-banner">
          <div class="act-banner-content">
            <span class="act-banner-title">📖 第{{ actBanner.act }}幕开始</span>
            <span v-if="actBanner.plot_summary" class="act-banner-text">{{ actBanner.plot_summary }}</span>
          </div>
        </div>
```

- [ ] **Step 2: Add `actBanner` computed ref in script**

Add after the `publicMessages` computed (around line 168):

```typescript
const actBanner = computed(() => store.actBanner);
```

- [ ] **Step 3: Replace `handleEndGame` with SSE consumer**

Replace the `handleEndGame` function (lines 463-472):

```typescript
  async function handleEndGame() {
    if (!confirm('确定要提前结束游戏并揭晓真相吗？')) return;
    adminLoading.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/end-game`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '结束游戏失败');
        return;
      }

      // Consume SSE stream
      const reader = res.body!.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                switch (data.type) {
                  case 'start':
                    currentEvent.value = '🎭 正在揭晓真相...';
                    break;
                  case 'done':
                    currentEvent.value = data.content || '';
                    fetchState();
                    break;
                  case 'error':
                    console.error('[end-game] Error:', data.message);
                    break;
                }
              } catch { /* skip malformed SSE */ }
            }
          }
        }
      } finally {
        reader.releaseLock();
      }
    } catch (e) {
      console.error('结束游戏失败:', e);
      alert('结束游戏失败: 网络错误');
    } finally {
      adminLoading.value = false;
    }
  }
```

- [ ] **Step 4: Add banner CSS**

Add in the `<style>` section:

```css
.act-banner {
  background: linear-gradient(135deg, #8e44ad, #0f3460);
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  animation: banner-appear 0.5s ease-out;
}
.act-banner-content { text-align: center; }
.act-banner-title { font-size: 18px; font-weight: bold; color: #fff; display: block; margin-bottom: 8px; }
.act-banner-text { font-size: 13px; color: #ddd; line-height: 1.6; }
@keyframes banner-appear { from { opacity: 0; transform: translateY(-10px); } to { opacity: 1; transform: translateY(0); } }
```

- [ ] **Step 5: Run type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: clean

---

### Task 10: Frontend — UI feedback for all actions

**Files:**
- Modify: `client/src/components/GamePage.vue`
- Modify: `client/src/components/AdminPanel.vue`

- [ ] **Step 1: Add loading refs for all actions in GamePage**

Add after `requestingClue` ref (around line 209):

```typescript
const submittingAccusation = ref(false);
const submittingVote = ref(false);
const addingClue = ref(false);
const advancingAct = ref(false);
const forcingTrial = ref(false);
```

- [ ] **Step 2: Update `submitAccusation` with loading + error handling**

Replace `submitAccusation` function:

```typescript
  async function submitAccusation() {
    if (!targetRole.value || !reasoning.value || submittingAccusation.value) return;
    submittingAccusation.value = true;
    sendWSMessage('accuse', { target_role_name: targetRole.value, reasoning: reasoning.value });
    try {
      const res = await fetch(`/api/rooms/${gameId}/accusations`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_player_id: playerId, target_role_name: targetRole.value, reasoning: reasoning.value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '提交指控失败');
      }
    } catch (e) {
      alert('提交指控失败: 网络错误');
    } finally {
      submittingAccusation.value = false;
    }
    showAccusation.value = false;
    targetRole.value = '';
    reasoning.value = '';
  }
```

- [ ] **Step 3: Update `submitVote` with loading + error handling**

Replace `submitVote` function:

```typescript
  async function submitVote() {
    if (!voteTarget.value || !voteReasoning.value || submittingVote.value) return;
    submittingVote.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/votes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from_player_id: playerId, target_role_name: voteTarget.value, reasoning: voteReasoning.value }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '提交投票失败');
      }
    } catch (e) {
      alert('提交投票失败: 网络错误');
    } finally {
      submittingVote.value = false;
    }
    voteTarget.value = '';
    voteReasoning.value = '';
  }
```

- [ ] **Step 4: Update `handleAddClue` with loading + feedback**

Replace `handleAddClue`:

```typescript
  async function handleAddClue(clue: { title: string; content: string }) {
    addingClue.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/dm/add-clue`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId, clue_title: clue.title, clue_content: clue.content }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '追加线索失败');
      }
    } catch (e) {
      alert('追加线索失败: 网络错误');
    } finally {
      addingClue.value = false;
    }
  }
```

- [ ] **Step 5: Update `handleAdvanceAct` with loading**

Add `advancingAct.value = true` at start, `advancingAct.value = false` in finally:

Replace `handleAdvanceAct`:

```typescript
  async function handleAdvanceAct() {
    if (!confirm(`确定要推进到第${act.value + 1}幕吗？这将解锁新的角色卡、线索和私信。`)) return;
    advancingAct.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/advance-act`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '推进失败');
      } else {
        const data = await res.json();
        console.log(`[advance-act] Now at act ${data.act}`);
        fetchState();
      }
    } catch (e) {
      alert('推进失败: 网络错误');
    } finally {
      advancingAct.value = false;
    }
  }
```

- [ ] **Step 6: Update `handleForceTrial` with loading**

Replace `handleForceTrial`:

```typescript
  async function handleForceTrial() {
    if (!confirm('确定要强制进入审判阶段吗？')) return;
    forcingTrial.value = true;
    try {
      const res = await fetch(`/api/rooms/${gameId}/force-trial`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ player_id: playerId }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || '操作失败');
      } else {
        fetchState();
      }
    } catch (e) {
      alert('操作失败: 网络错误');
    } finally {
      forcingTrial.value = false;
    }
  }
```

- [ ] **Step 7: Update template button disabled states**

In the accusation section, update the submit button:

```html
<button @click="submitAccusation" :disabled="!targetRole || !reasoning || submittingAccusation">
  {{ submittingAccusation ? '提交中...' : '提交指控' }}
</button>
```

In the vote section, update the submit button:

```html
<button @click="submitVote" :disabled="!voteTarget || !voteReasoning || submittingVote">
  {{ submittingVote ? '提交中...' : '提交投票' }}
</button>
```

- [ ] **Step 8: Update AdminPanel to accept and pass through loading states**

Replace `AdminPanel.vue` `<script setup>`:

```typescript
import { ref } from 'vue';

defineProps<{
  loading: boolean;
  dmLog: string[];
}>();

const emit = defineEmits(['push-event', 'advance-act', 'force-trial', 'end-game', 'add-clue']);

const showClueInput = ref(false);
const clueTitle = ref('');
const clueContent = ref('');

function submitClue() {
  if (!clueTitle.value || !clueContent.value) return;
  emit('add-clue', { title: clueTitle.value, content: clueContent.value });
  showClueInput.value = false;
  clueTitle.value = '';
  clueContent.value = '';
}
```

Update AdminPanel template buttons to use `loading` prop for all admin actions:

```html
      <button @click="$emit('push-event')" :disabled="loading" class="action-btn advance">
        ⏭️ {{ loading ? '生成中...' : '推进剧情' }}
      </button>
      <button @click="$emit('advance-act')" :disabled="loading" class="action-btn next-act">
        📖 {{ loading ? '处理中...' : '推进下一幕' }}
      </button>
      <button @click="showClueInput = true" :disabled="loading" class="action-btn clue">🔍 追加线索</button>
      <button @click="$emit('force-trial')" :disabled="loading" class="action-btn trial">⚖️ 强制审判</button>
      <button @click="$emit('end-game')" :disabled="loading" class="action-btn end">🛑 提前结束</button>
```

- [ ] **Step 9: Run type check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: clean

---

### Task 11: Verification

- [ ] **Step 1: Run backend tests**

Run: `pytest tests/ -v`
Expected: 45 passed (44 existing + 1 new `test_cache_accusation`)

- [ ] **Step 2: Run frontend tests**

Run: `cd client && npm test`
Expected: 2 passed

- [ ] **Step 3: Run frontend build**

Run: `cd client && npm run build`
Expected: build succeeds

- [ ] **Step 4: Final commit**

```bash
git add -A
git commit -m "fix: resolve all technical debt + add game-end SSE, vote broadcast, act transition banner, UI feedback"
```

---

## Self-Review

**1. Spec coverage:**
- ✅ A1: `end_game` → SSE streaming (Task 5)
- ✅ A2: `private_chat` reconnect cache → already fixed in prior session
- ✅ A3: `accusation` cache + store handler (Tasks 1-3, 8)
- ✅ B4: `submitAccusation`/`submitVote` loading + error (Task 10)
- ✅ B5: `handleForceTrial`/`handleEndGame` loading + error (Tasks 9, 10)
- ✅ B6: `handleAddClue` loading + error (Task 10)
- ✅ C7: `test_llm`/`list_llm_models` blocking → `run_in_threadpool` (Task 6)
- ✅ D8: Game-over SSE truth reveal (Task 5)
- ✅ D9: Vote broadcast `vote_cast` WS (Task 4, 8)
- ✅ D10: Act transition notification (Task 7, 8, 9)

**2. Placeholder scan:** No TBDs, TODOs, or vague steps. All code is complete.

**3. Type consistency:**
- `vote_cast`: `{ from: string, from_player_id: string, target: string }` — defined in ws.ts, used in store handler, broadcast from websocket_hub
- `act_transition`: `{ act: number, plot_summary: string }` — defined in ws.ts, used in store handler, broadcast from api_routes
- `accusation` now has `from_player_id` field added in WS broadcast
- `distributed_accusations` is `List[dict]` on GameState, returned by `get_pending_distributions` as list of messages
- `actBanner` is `ref<{ act: number; plot_summary: string } | null>` in store, consumed as computed in GamePage
- `run_in_threadpool` is from starlette.concurrency, compatible with TestClient (unlike `asyncio.to_thread`)
