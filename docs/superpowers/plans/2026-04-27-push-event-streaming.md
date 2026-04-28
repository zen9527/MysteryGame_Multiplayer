# Push-Event Streaming & Progress Bar Improvement Plan

> **For agentic workers:** Use superpowers:subagent-driven-development to implement task-by-task.

**Goal:**
1. Convert `push-event` from blocking HTTP fetch + timeout to SSE streaming (like `generate-script` already does)
2. Fix script generation progress bar to be meaningful instead of arbitrary `chunkCount / 10`

**Architecture:**
- `push-event` endpoint mirrors existing `generate-script` SSE pattern: `start` → `chunk` → `done` events
- Frontend `handlePushEvent` uses `ReadableStream` reader instead of plain `fetch` + `AbortController` timeout
- Script generation progress bar uses elapsed time + chunk count for more realistic feedback

**Tech Stack:** FastAPI `StreamingResponse`, SSE, Vue 3 `fetch` + `ReadableStream`, WebSocket broadcast (unchanged).

---

### Task 1: SSE push-event endpoint in api_routes.py

**Files:**
- Modify: `server/api_routes.py:458-496`

- [ ] **Step 1: Replace blocking push-event with SSE streaming**

Replace the entire `push_event` endpoint block (lines 458-496) with:

```python
def _push_event_generator(game_id: str, req: PushEventRequest):
    """SSE generator for DM event generation."""
    state = manager.get_state(game_id)
    if not state:
        yield f"data: {{\"type\": \"error\", \"message\": \"Room not found\"}}\n\n"
        return
    require_admin(req.player_id, game_id)

    log = logging.getLogger(__name__)
    log.info(f"[push-event-stream] Generating event for {game_id}, act={state.act}, round={state.current_round}")

    try:
        # Send start event immediately — admin sees "generating" right away
        yield f"data: {{\"type\": \"start\"}}\n\n"

        # LLM generates structured event (blocking, but streamed to client)
        event = host_dm.generate_event(state)
        log.info(f"[push-event-stream] Event generated successfully")

        state.current_round += 1
        result = manager.push_structured_event(game_id, event)

        # Send done event with result summary
        done_payload = json.dumps({
            "type": "done",
            "public_event": result["public_event"] if result else "",
            "private_clues_count": len(result["private_clues"]) if result else 0,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"[push-event-stream] Event generation failed: {type(e).__name__}: {e}", exc_info=True)
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/api/rooms/{game_id}/dm/push-event")
async def push_event(game_id: str, req: PushEventRequest):
    """流式推进剧情（SSE），实时返回生成进度。"""
    return StreamingResponse(
        _push_event_generator(game_id, req),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
```

Key changes:
- Remove `hub.broadcast` from endpoint — WS broadcast is handled by `push_structured_event` persistence + WS reconnect resend. Other players see event via their existing WS connection (the event is already in `public_messages`).
- Return `StreamingResponse` with SSE events
- `start` event lets admin know LLM has started immediately
- `done` event contains `public_event` and `private_clues_count`
- No `AbortController` timeout needed — stream naturally ends when LLM finishes or errors

- [ ] **Step 2: Verify imports compile**

```bash
python -c "from server.api_routes import router; print('api_routes OK')"
```

Expected: `api_routes OK`

- [ ] **Step 3: Commit**

```bash
git add server/api_routes.py
git commit -m "feat: push-event endpoint converts to SSE streaming"
```

---

### Task 2: Frontend handlePushEvent consumes SSE stream

**Files:**
- Modify: `client/src/components/GamePage.vue:327-345`

- [ ] **Step 1: Rewrite handlePushEvent to use SSE reader**

Replace the current `handlePushEvent` function (lines 327-345):

```ts
async function handlePushEvent() {
  adminLoading.value = true;
  currentEvent.value = '';
  try {
    const res = await fetch(`/api/rooms/${gameId}/dm/push-event`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_id: playerId, event_content: '' }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      console.error('推进剧情失败:', err.detail || '未知错误');
      return;
    }

    // Consume SSE stream — same pattern as WaitingLobby.vue generateScript
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

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
                console.log('[push-event] LLM starting...');
                break;
              case 'chunk':
                console.log('[push-event] Token chunk received');
                break;
              case 'done':
                currentEvent.value = data.public_event || '';
                console.log(`[push-event] Done: ${data.private_clues_count} private clues`);
                break;
              case 'error':
                console.error('[push-event] Error:', data.message);
                break;
            }
          } catch { /* skip malformed SSE */ }
        }
      }
    }
  } catch (e) {
    console.warn('推进剧情请求失败:', e);
  } finally {
    adminLoading.value = false;
  }
}
```

Key changes:
- Remove `AbortController` and 310s timeout — not needed with streaming
- Use `ReadableStream` + `TextDecoder` SSE parsing (identical pattern to `WaitingLobby.vue` lines 337-372)
- On `done`, update `currentEvent.value` directly
- No `alert()` — errors go to console, event still persisted on server
- `adminLoading` stays `true` during entire stream

- [ ] **Step 2: Run frontend type check**

```bash
cd client && npx vue-tsc --noEmit
```

Expected: clean (no errors)

- [ ] **Step 3: Run frontend tests**

```bash
cd client && npm test
```

Expected: 2 tests pass

- [ ] **Step 4: Commit**

```bash
git add client/src/components/GamePage.vue
git commit -m "fix: push-event frontend consumes SSE stream instead of blocking fetch"
```

---

### Task 3: Improve script generation progress bar

**Files:**
- Modify: `client/src/components/WaitingLobby.vue:317-378` (generateScript function)

- [ ] **Step 1: Replace chunk-count progress with time-based progress + status text**

Replace the `generateScript` function's progress logic (lines 317-378):

```ts
async function generateScript() {
  generating.value = true;
  genProgress.value = 0;
  genStatus.value = '正在初始化...';
  genError.value = '';
  try {
    const res = await fetch(`/api/rooms/${gameId}/generate-script`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        genre: selectedGenre.value,
        difficulty: selectedDifficulty.value,
        estimated_time: estimatedTime.value,
        player_count: playerCountTarget.value,
      }),
    });
    if (!res.ok) {
      const data = await res.json();
      throw new Error(data.detail || '生成失败');
    }
    // Read SSE stream
    const reader = res.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let chunkCount = 0;
    const startTime = Date.now();

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
                chunkCount = 0;
                startTime = Date.now();
                genStatus.value = '正在初始化...';
                break;
              case 'chunk':
                chunkCount++;
                const elapsed = (Date.now() - startTime) / 1000;
                if (elapsed < 3) {
                  genProgress.value = 0;
                  genStatus.value = '正在初始化...';
                } else if (elapsed < 10) {
                  genProgress.value = Math.min(40, Math.floor(chunkCount / 15));
                  genStatus.value = '正在生成剧本...';
                } else {
                  genProgress.value = Math.min(95, Math.floor(40 + (chunkCount - 15) / 20));
                  genStatus.value = '正在生成剧本...';
                }
                break;
              case 'done':
                genProgress.value = 100;
                genStatus.value = '生成完成';
                await fetchState();
                break;
              case 'error':
                throw new Error(data.message);
            }
          } catch { /* skip malformed SSE */ }
        }
      }
    }
  } catch (e: any) {
    genError.value = e.message;
    genStatus.value = '生成失败';
  } finally {
    generating.value = false;
  }
}
```

Add `genStatus` ref near line 163:

```ts
const genStatus = ref('');
```

Update template (lines 87-90) to show status text:

```html
<div v-if="generating" class="gen-progress">
  <div class="progress-bar" :style="{ width: genProgress + '%' }"></div>
  <span class="progress-text">{{ genProgress }}%</span>
</div>
<div v-if="generating && genStatus" class="gen-status">{{ genStatus }}</div>
```

Add CSS for `.gen-status` after line 629:

```css
.gen-status {
  text-align: center; color: #aaa; font-size: 12px; margin-top: 4px;
}
```

- [ ] **Step 2: Run frontend type check**

```bash
cd client && npx vue-tsc --noEmit
```

Expected: clean

- [ ] **Step 3: Run frontend tests**

```bash
cd client && npm test
```

Expected: 2 tests pass

- [ ] **Step 4: Commit**

```bash
git add client/src/components/WaitingLobby.vue
git commit -m "feat: script generation progress uses time-based feedback with status text"
```

---

### Task 4: Verification

- [ ] **Step 1: Backend imports**

```bash
python -c "from server.api_routes import router; from server.host_dm import host; from server.game_manager import manager; print('All imports OK')"
```

Expected: `All imports OK`

- [ ] **Step 2: Backend tests**

```bash
python -m pytest tests/test_game_manager.py -v
```

Expected: 29 passed

- [ ] **Step 3: Frontend tests**

```bash
cd client && npm test
```

Expected: 2 passed

- [ ] **Step 4: Frontend type check**

```bash
cd client && npx vue-tsc --noEmit
```

Expected: clean

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: verify streaming push-event and progress bar improvements"
```

---

## Self-Review

**Spec coverage:**
- ✅ Progress bar percentage question answered (chunkCount / 10, arbitrary)
- ✅ push-event SSE streaming (mirrors generate-script pattern)
- ✅ Frontend SSE reader (mirrors WaitingLobby.vue pattern)
- ✅ No timeout needed — streaming handles duration naturally
- ✅ Script generation progress improved with time-based status

**Placeholder scan:** No placeholders found. All code blocks complete.

**Type consistency:**
- `PushEventRequest` model already exists in api_routes.py
- `StreamingResponse` already used in generate-script endpoint
- `host_dm.generate_event()` returns dict (from previous commit)
- `manager.push_structured_event()` exists (from previous commit)
- SSE parsing pattern identical to WaitingLobby.vue

**Edge cases:**
- Error during streaming: `error` SSE event → frontend logs to console, `adminLoading` still cleared in `finally`
- LLM takes very long (5+ minutes): streaming handles this naturally, no timeout error
- Other players see event: event persisted in `public_messages`, resent on WS reconnect, and available via 5s polling (`fetchState`)
