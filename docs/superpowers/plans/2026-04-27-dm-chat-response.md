> ⚠️ **STATUS: COMPLETED** — This plan was fully implemented with deviations:
> - `chat_stream` uses shared `_stream_chat()` helper (not standalone), `timeout=300`
> - `respond_to_chat` + `respond_to_chat_stream` use shared `_build_chat_prompt()` helper
> - `DM_CHAT_SYSTEM_PROMPT` is a class constant, sender name resolution uses player names
> - Endpoint uses player-identity check (not admin-only), 30s rate limiting per player
> - Player's own message immediately pushed to `store.privateMessages` before SSE stream
> - `seenPrivateKeys` Set for dedup, `distributed_dm_private` cache for reconnect
> See CLAUDE.md for current architecture.

# DM Chat Response Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a player sends a private message to the DM, the LLM generates a contextual response streamed via SSE to the frontend in real-time.

**Architecture:** Player POSTs to `/api/rooms/{gameId}/dm/chat-response` → server calls `host_dm.respond_to_chat_stream()` → SSE stream with `start`/`chunk`/`done`/`error` events → frontend SSE reader displays tokens in real-time → full reply stored in `private_messages` + `distributed_dm_private` cache.

**Tech Stack:** FastAPI StreamingResponse, OpenAI-compatible LLM streaming, Vue 3 SSE reader (same pattern as `push-event`), Pinia store for private messages.

---

### Task 1: Add `chat_stream` method to LLMClient

**Files:**
- Modify: `server/llm_client.py:93-124` (add after `generate_script_stream`)

- [ ] **Step 1: Add `chat_stream` method**

Add after the existing `generate_script_stream` method (line 124):

```python
    def chat_stream(self, system_prompt: str, user_prompt: str):
        """Chat response, streaming content chunks."""
        url = self._chat_url()
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.8,
            "stream": True,
        }
        response = requests.post(url, headers=headers, json=payload, timeout=None, stream=True)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                text = line.decode("utf-8")
                if text.startswith("data: "):
                    data_str = text[6:]
                    if data_str == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import server.llm_client; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/llm_client.py
git commit -m "feat(llm): add chat_stream method for streaming DM responses"
```

---

### Task 2: Add `respond_to_chat` and `respond_to_chat_stream` to HostDM

**Files:**
- Modify: `server/host_dm.py:121-126` (add after `generate_script`)

- [ ] **Step 1: Add two new methods**

Add after line 123 (`generate_script` method):

```python
    DM_CHAT_SYSTEM_PROMPT = """你是一名专业的剧本杀主持人（DM）。玩家正在通过私信与你对话。

你的职责：
1. 根据当前游戏阶段和剧本设定，给玩家合适的回应
2. 如果玩家询问线索，根据阶段决定是否透露（第一幕给模糊提示，第二幕给具体线索）
3. 如果玩家询问规则，简洁说明
4. 如果玩家表达推理，给予鼓励或引导
5. 保持DM身份，不要直接透露凶手或关键剧情

规则：
- 回复使用中文，语气亲切但保持神秘感
- 不要一次性透露太多信息
- 根据玩家角色和当前幕次给出差异化回应
- 回复长度控制在 50-200 字
- 只回复纯文本，不要JSON格式"""

    def respond_to_chat(self, game_state: GameState, player_id: str, player_message: str) -> str:
        """Generate a DM response to a player's private message. Returns plain text."""
        player = game_state.players.get(player_id)
        role_name = player.role.name if player and player.role else "未分配"

        chat_summary = []
        for msg in game_state.private_messages[-10:]:
            sender = "🎭 DM" if msg.from_player_id == "__dm__" else msg.from_player_id
            chat_summary.append(f"{sender}: {msg.content}")

        user_input = f"""你正在与一名玩家私信对话。
当前是第{game_state.current_round}轮，第{game_state.act}幕。
玩家角色：{role_name}
玩家消息：{player_message}
私信历史：
{''.join(chat_summary) if chat_summary else '暂无私信记录'}

请给玩家一个符合DM身份的回复。"""

        return self.llm.chat_stream_generator(self.DM_CHAT_SYSTEM_PROMPT, user_input)

    def respond_to_chat_stream(self, game_state: GameState, player_id: str, player_message: str):
        """Stream a DM response to a player's private message. Yields content chunks."""
        player = game_state.players.get(player_id)
        role_name = player.role.name if player and player.role else "未分配"

        chat_summary = []
        for msg in game_state.private_messages[-10:]:
            sender = "🎭 DM" if msg.from_player_id == "__dm__" else msg.from_player_id
            chat_summary.append(f"{sender}: {msg.content}")

        user_input = f"""你正在与一名玩家私信对话。
当前是第{game_state.current_round}轮，第{game_state.act}幕。
玩家角色：{role_name}
玩家消息：{player_message}
私信历史：
{''.join(chat_summary) if chat_summary else '暂无私信记录'}

请给玩家一个符合DM身份的回复。"""

        yield from self.llm.chat_stream(self.DM_CHAT_SYSTEM_PROMPT, user_input)
```

- [ ] **Step 2: Verify syntax**

Run: `python -c "import server.host_dm; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add server/host_dm.py
git commit -m "feat(dm): add respond_to_chat and respond_to_chat_stream methods"
```

---

### Task 3: Add SSE endpoint for DM chat response

**Files:**
- Modify: `server/api_routes.py` (add new request model + endpoint)

- [ ] **Step 1: Add ChatResponseRequest model**

Add after `DMPrivateRequest` (line 117):

```python
class ChatResponseRequest(BaseModel):
    player_id: str
    content: str
```

- [ ] **Step 2: Add SSE generator**

Add after `_push_event_generator` (line 522):

```python
def _chat_response_generator(game_id: str, player_id: str, player_message: str, state):
    """SSE generator for DM chat response."""
    if state.phase not in ("playing", "waiting"):
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待中或游戏中与DM对话\"}}\n\n"
        return

    log.info(f"[chat-response] Player {player_id} chatting: {player_message[:50]}")

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_reply = ""
        for chunk in host_dm.respond_to_chat_stream(game_id, player_id, player_message):
            full_reply += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        # Store the full reply
        manager.add_dm_chat_response(game_id, player_id, player_message, full_reply)

        done_payload = json.dumps({
            "type": "done",
            "content": full_reply,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        log.error(f"[chat-response] Failed: {type(e).__name__}: {e}", exc_info=True)
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"
```

- [ ] **Step 3: Add endpoint**

Add after `dm_private` endpoint (line 567):

```python
@router.post("/api/rooms/{game_id}/dm/chat-response")
async def chat_response(game_id: str, req: ChatResponseRequest):
    """流式DM私信回复（SSE），实时返回生成进度。"""
    state = manager.get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    # Store player's message first (so it appears immediately)
    manager.add_chat_message(game_id, req.player_id, req.content, is_private=True, target_player_id="__dm__")

    return StreamingResponse(
        _chat_response_generator(game_id, req.player_id, req.content, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

- [ ] **Step 4: Verify syntax**

Run: `python -c "import server.api_routes; print('OK')"`
Expected: `OK`

- [ ] **Step 5: Commit**

```bash
git add server/api_routes.py
git commit -m "feat(api): add SSE endpoint for DM chat response streaming"
```

---

### Task 4: Add `add_dm_chat_response` to GameManager

**Files:**
- Modify: `server/game_manager.py` (add method)

- [ ] **Step 1: Add method**

Add after `add_chat_message` (around line 214):

```python
    def add_dm_chat_response(self, game_id: str, player_id: str, player_message: str, dm_reply: str):
        """Store DM's chat response in private_messages and cache for WS reconnect."""
        if game_id not in self.games:
            return
        state = self.games[game_id]

        # Store DM reply as private message
        reply_msg = Message(
            from_player_id="__dm__",
            content=dm_reply,
            type="private",
            to_player_id=player_id,
        )
        state.private_messages.append(reply_msg)

        # Cache for WS reconnect
        if player_id not in state.distributed_dm_private:
            state.distributed_dm_private[player_id] = []
        state.distributed_dm_private[player_id].append({
            "type": "dm_private",
            "from": "__dm__",
            "to": player_id,
            "content": dm_reply,
        })
```

- [ ] **Step 2: Add unit test**

Create `tests/test_dm_chat_response.py`:

```python
import pytest
from server.game_manager import manager
from server.models import Script, Role, GameState, Message, PlotOutline


@pytest.fixture
def game_state():
    script = Script(
        title="Test Script",
        genre="悬疑推理",
        difficulty="中等",
        estimated_time=90,
        background_story="test",
        true_killer="test",
        murder_method="test",
        cover_up="test",
        roles=[Role(id="r1", name="张三", age=25, occupation="医生", description="医生", background="test", secret_task="test", alibi="test", motive="test", relationships=[])],
        clues=[],
        plot_outline=PlotOutline(act1="", act2="", act3=""),
    )
    state = GameState(
        game_id="test-game",
        phase="playing",
        act=1,
        room_creator_id="p1",
        players={"p1": manager.create_game("dummy", "p1").players["p1"]},
        script=script,
    )
    # Fix: properly create player with role
    from server.models import Player
    state.players["p1"] = Player(id="p1", name="张三", role_id="r1", role=script.roles[0])
    manager.games["test-game"] = state
    return state


def test_add_dm_chat_response_stores_message(game_state):
    manager.add_dm_chat_response("test-game", "p1", "你好", "你好，我是DM")

    # Check private_messages has the reply
    reply = game_state.private_messages[-1]
    assert reply.from_player_id == "__dm__"
    assert reply.content == "你好，我是DM"
    assert reply.type == "private"
    assert reply.to_player_id == "p1"


def test_add_dm_chat_response_caches_for_reconnect(game_state):
    manager.add_dm_chat_response("test-game", "p1", "你好", "你好，我是DM")

    pending = manager.get_pending_distributions("test-game", "p1")
    dm_private_msgs = [m for m in pending if m.get("type") == "dm_private"]
    assert len(dm_private_msgs) >= 1
    assert dm_private_msgs[-1]["content"] == "你好，我是DM"
```

- [ ] **Step 3: Run test**

Run: `pytest tests/test_dm_chat_response.py -v`
Expected: 2 passed

- [ ] **Step 4: Commit**

```bash
git add server/game_manager.py tests/test_dm_chat_response.py
git commit -m "feat(game): add add_dm_chat_response method with caching for WS reconnect"
```

---

### Task 5: Update PrivateChatPanel.vue — SSE reader + streaming UI

**Files:**
- Modify: `client/src/components/PrivateChatPanel.vue`

- [ ] **Step 1: Update template — add streaming status and DM reply display**

Replace the `chat-input-row` section (lines 18-25):

```vue
      <div v-if="isStreaming" class="streaming-status">
        🤖 DM正在思考...
      </div>
      <div v-if="pendingReply" class="pending-reply">
        <span class="sender">🎭 DM</span>
        <span class="text">{{ pendingReply }}</span>
      </div>
      <div class="chat-input-row">
        <input
          v-model="newMessage"
          @keyup.enter="sendDMPrivate"
          placeholder="向DM提问..."
        />
        <button @click="sendDMPrivate" :disabled="!newMessage.trim() || isStreaming">发送</button>
      </div>
```

- [ ] **Step 2: Update script setup — add SSE reader logic**

Replace the entire `<script setup>` block (lines 30-82):

```vue
<script setup lang="ts">
import { ref, computed, onMounted, nextTick } from 'vue';
import { useGameStore } from '../stores/game';
import { useRoute } from 'vue-router';

const store = useGameStore();
const route = useRoute();
const gameId = route.params.gameId as string;
const playerId =
  localStorage.getItem(`player_${gameId}`) ||
  localStorage.getItem(`admin_${gameId}`) ||
  '';

const newMessage = ref('');
const messageContainer = ref<HTMLElement | null>(null);

const privateMessages = computed(() => store.privateMessages);
const hasPlayer = computed(() => !!playerId);

// Streaming state
const isStreaming = ref(false);
const pendingReply = ref('');

async function sendDMPrivate() {
  const text = newMessage.value.trim();
  if (!text || !playerId || isStreaming.value) return;

  isStreaming.value = true;
  pendingReply.value = '';
  newMessage.value = '';

  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/chat-response`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        player_id: playerId,
        content: text,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error('DM回复失败:', err.detail || '未知错误');
      pendingReply.value = 'DM 暂时无法回应，请稍后再试。';
      return;
    }

    // Consume SSE stream — same pattern as GamePage.vue handlePushEvent
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
            let data;
            try {
              data = JSON.parse(line.slice(6));
            } catch {
              /* skip malformed SSE */
              continue;
            }
            switch (data.type) {
              case 'start':
                console.log('[chat-response] DM starting...');
                break;
              case 'chunk':
                pendingReply.value += data.content;
                await nextTick();
                if (messageContainer.value) {
                  messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
                }
                break;
              case 'done':
                // Full reply stored by server — store it in Pinia via WS dm_private
                // Also append to store for immediate display
                store.privateMessages.push({
                  from: '🎭 DM',
                  content: data.content,
                  timestamp: '',
                });
                console.log(`[chat-response] Done: ${data.content.length} chars`);
                break;
              case 'error':
                throw new Error(data.message);
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (e: any) {
    console.warn('DM私信请求失败:', e);
    pendingReply.value = 'DM 暂时无法回应，请稍后再试。';
  } finally {
    isStreaming.value = false;
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
```

- [ ] **Step 3: Add CSS for streaming status**

Add after existing `.chat-input-row button:disabled` (line 151):

```css
.streaming-status {
  text-align: center; color: #e94560; font-size: 13px; margin-bottom: 8px;
  animation: pulse 1.5s ease-in-out infinite;
}
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }

.pending-reply {
  padding: 8px 0; border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}
.pending-reply .sender { font-weight: bold; color: #e94560; margin-right: 8px; }
.pending-reply .text { color: #ddd; font-size: 13px; line-height: 1.6; }
```

- [ ] **Step 4: Verify TypeScript**

Run: `cd client && npx vue-tsc --noEmit`
Expected: clean (no errors)

- [ ] **Step 5: Commit**

```bash
git add client/src/components/PrivateChatPanel.vue
git commit -m "feat(frontend): add SSE streaming reader for DM chat response"
```

---

### Task 6: Run all tests and verify

**Files:**
- All modified files

- [ ] **Step 1: Run backend tests**

Run: `pytest tests/ -v`
Expected: all 42 tests pass (40 existing + 2 new)

- [ ] **Step 2: Run frontend tests**

Run: `cd client && npm test`
Expected: 2 tests pass

- [ ] **Step 3: Run TypeScript check**

Run: `cd client && npx vue-tsc --noEmit`
Expected: clean (no errors)

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "chore: verify all tests pass for DM chat response feature"
```

---

## Self-Review

1. **Spec coverage:** All 5 design sections covered — endpoint (Task 3), LLM method (Task 2), frontend SSE reader (Task 5), store handling (Task 4), data flow (Task 4 caching).
2. **Placeholder scan:** No "TBD", "TODO", or vague requirements. All code is complete.
3. **Type consistency:** `dm_private` WS message type already exists in `ws.ts` with `from: "__dm__"`, `to`, `content`. Store `handleWSMessage` already handles `dm_private` case. No type changes needed.
4. **Ambiguity check:** SSE event types match `push-event` pattern exactly (`start`/`chunk`/`done`/`error`). Frontend reader pattern is identical to `GamePage.vue` `handlePushEvent`.
