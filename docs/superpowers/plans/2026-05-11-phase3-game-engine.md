# Phase 3: Game Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create an autonomous Game Engine that lets the DM monitor game progress, nudge idle players, manage act transitions, and handle the full game lifecycle — replacing the manual-only DM approach.

**Architecture:** New `server/game_engine/` package with `GameHost` (autonomous DM logic), `GameScheduler` (periodic monitoring via asyncio tasks), and `DMPrompts` (centralized prompt management). GameState extended with auto-DM fields. Admin can toggle autonomous mode on/off.

**Tech Stack:** Python, asyncio, FastAPI, LLMRegistry (Phase 1)

**Spec:** `docs/superpowers/specs/2026-05-11-modular-refactor-design.md` Section 3

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `server/game_engine/__init__.py` | Package init |
| Create | `server/game_engine/prompts.py` | Centralized DM prompt templates |
| Create | `server/game_engine/host.py` | GameHost — autonomous DM logic |
| Create | `server/game_engine/scheduler.py` | GameScheduler — periodic monitoring |
| Create | `tests/test_game_engine.py` | Tests for prompts, host, scheduler |
| Modify | `server/models.py` | Add GameState auto-DM fields |
| Modify | `server/websocket_hub.py` | Update player activity tracking |
| Modify | `server/api/game.py` | Integrate GameHost + scheduler |
| Modify | `server/api/dm.py` | Update to use GameHost |
| Modify | `server/di/container.py` | Register GameHost, GameScheduler |
| Delete | `server/host_dm.py` | Replaced by game_engine |

---

### Task 1: Centralized DM Prompts

**Files:**
- Create: `server/game_engine/__init__.py`
- Create: `server/game_engine/prompts.py`
- Create: `tests/test_game_engine.py`

- [ ] **Step 1: Create package init**

```python
# server/game_engine/__init__.py
from server.game_engine.host import GameHost
from server.game_engine.scheduler import GameScheduler

__all__ = ["GameHost", "GameScheduler"]
```

- [ ] **Step 2: Create prompts module**

```python
# server/game_engine/prompts.py


class DMPrompts:
    SYSTEM_EVENT = """你是一名专业的剧本杀主持人（DM）。你的职责：
1. 动态发布事件 — 每轮给玩家一个情境或发现
2. 投放线索 — 根据游戏进度和玩家行为决定何时放出什么线索
3. 维持剧情一致性 — 所有事件和线索必须符合剧本设定
4. 引导节奏 — 玩家卡住时给提示，讨论热烈时推进剧情
5. 处理指控 — 当有指控时，宣布进入审判环节
6. 揭晓真相 — 投票达成共识后，完整复盘故事
7. 评价玩家 — 为每个玩家生成表现评价

规则：
- 不要单方面宣布游戏结束（除非超时）
- 所有正常结束必须经过玩家投票
- 线索投放要有节奏感，不要一次性全部放出
- 给不同角色投放个性化线索
- 保持悬疑感和趣味性

=== 输出格式（严格遵守）===

你必须返回一个 JSON 对象，包含以下字段：
{
  "public_event": "面向所有玩家公开的叙事/事件/线索。使用emoji和markdown增强可读性。如果没有公共内容，填空字符串。",
  "private_clues": [
    {"role": "角色名", "content": "该角色专属的线索内容"},
    ...
  ],
  "dm_instruction": "仅DM可见的行动指引。不要暴露给玩家。"
}

注意：
- private_clues 的 role 字段必须是当前在场玩家的**角色名**
- 不要给所有玩家相同的专属线索——专属线索应该有差异性
- 只返回JSON，不要添加任何解释文字"""

    SYSTEM_CHAT = """你是一名专业的剧本杀主持人（DM）。玩家正在通过私信与你对话。

你的职责：
1. 根据当前游戏阶段和剧本设定，给玩家合适的回应
2. 如果玩家询问线索，根据阶段决定是否透露
3. 保持DM身份，不要直接透露凶手或关键剧情
4. 回复使用中文，语气亲切但保持神秘感
5. 回复长度控制在 50-200 字
6. 只回复纯文本，不要JSON格式"""

    SYSTEM_REVEAL = """你是一名剧本杀主持人（DM）。现在游戏进入真相揭晓阶段。

请根据以下信息生成完整的真相揭晓：
1. 完整还原凶手的作案过程
2. 解释所有线索的含义
3. 揭示每个角色的秘密
4. 复盘整个故事的时间线
5. 对每个玩家的推理过程进行评价

输出格式：自由文本，使用markdown格式增强可读性。"""

    SYSTEM_OPENING = """你是一名剧本杀主持人（DM）。游戏刚刚开始，请生成开场叙事。

要求：
1. 营造与剧本类型匹配的氛围
2. 介绍故事背景和场景
3. 提及在场的所有角色（但不要透露秘密）
4. 设置悬念，引导玩家开始互动
5. 长度 200-400 字

输出格式：与事件格式相同的JSON，包含 public_event 和 private_clues（开场可以给每个角色一条个性化提示）。"""

    SYSTEM_IDLE_NUDGE = """你是一名剧本杀主持人（DM）。玩家们似乎陷入了沉默，请生成一条引导性的消息来推动游戏。

要求：
1. 不要太突兀，像自然发生的一样
2. 可以提示某个线索方向
3. 或者引入一个新事件打破僵局
4. 保持简短（50-100字）
5. 只返回JSON格式的 public_event（private_clues可以为空）"""

    @staticmethod
    def build_event_user_prompt(game_state) -> str:
        player_info = []
        role_names = []
        for pid, p in game_state.players.items():
            role_name = p.role.name if p.role else "未分配"
            player_info.append(f"{p.name}({role_name})")
            role_names.append(role_name)

        chat_summary = []
        for msg in game_state.public_messages[-20:]:
            sender = next(
                (p.name for pid, p in game_state.players.items() if pid == msg.from_player_id),
                msg.from_player_id,
            )
            chat_summary.append(f"{sender}: {msg.content}")

        return f"""当前是第{game_state.current_round}轮，阶段: 第{game_state.act}幕
玩家状态：{', '.join(player_info)}
在场角色名：{', '.join(role_names)}
最近聊天：
{''.join(chat_summary) if chat_summary else '暂无聊天记录'}

请根据以上信息生成下一个游戏事件。严格按JSON格式返回，包含 public_event、private_clues、dm_instruction 三个字段。"""

    @staticmethod
    def build_chat_user_prompt(game_state, player_id: str, player_message: str) -> str:
        player = game_state.players.get(player_id)
        role_name = player.role.name if player and player.role else "未分配"

        chat_summary = []
        for msg in game_state.private_messages[-10:]:
            if msg.from_player_id == "__dm__":
                sender = "🎭 DM"
            elif msg.from_player_id in game_state.players:
                sender = game_state.players[msg.from_player_id].name
            else:
                sender = msg.from_player_id
            chat_summary.append(f"{sender}: {msg.content}")

        return f"""你正在与一名玩家私信对话。
当前是第{game_state.current_round}轮，第{game_state.act}幕。
玩家角色：{role_name}
玩家消息：{player_message}
私信历史：
{''.join(chat_summary) if chat_summary else '暂无私信记录'}

请给玩家一个符合DM身份的回复。"""
```

- [ ] **Step 3: Write prompt tests**

```python
# tests/test_game_engine.py
import pytest
from server.game_engine.prompts import DMPrompts
from server.models import GameState, Script, PlotOutline, Player, Role


def _make_state(**overrides):
    defaults = dict(
        game_id="test",
        phase="playing",
        act=1,
        room_creator_id="admin",
        players={},
        script=Script(
            title="T", genre="悬疑推理", difficulty="中等", estimated_time=90,
            background_story="", true_killer="", murder_method="", cover_up="",
            roles=[], clues=[], plot_outline=PlotOutline(act1="", act2="", act3=""),
        ),
    )
    defaults.update(overrides)
    return GameState(**defaults)


def test_prompts_are_strings():
    assert isinstance(DMPrompts.SYSTEM_EVENT, str)
    assert isinstance(DMPrompts.SYSTEM_CHAT, str)
    assert isinstance(DMPrompts.SYSTEM_REVEAL, str)
    assert isinstance(DMPrompts.SYSTEM_OPENING, str)
    assert isinstance(DMPrompts.SYSTEM_IDLE_NUDGE, str)


def test_build_event_user_prompt():
    state = _make_state(
        players={"p1": Player(id="p1", name="张三", role_id="r1",
                               role=Role(name="侦探", age=30, occupation="侦探",
                                         description="聪明", background="x",
                                         secret_task="x", alibi="x", motive="x"))},
        current_round=3,
    )
    prompt = DMPrompts.build_event_user_prompt(state)
    assert "第3轮" in prompt
    assert "张三" in prompt
    assert "侦探" in prompt


def test_build_chat_user_prompt():
    state = _make_state(
        players={"p1": Player(id="p1", name="李四", role_id="r1",
                               role=Role(name="嫌疑人", age=25, occupation="作家",
                                         description="神秘", background="x",
                                         secret_task="x", alibi="x", motive="x"))},
        current_round=2,
    )
    prompt = DMPrompts.build_chat_user_prompt(state, "p1", "我想了解更多线索")
    assert "嫌疑人" in prompt
    assert "我想了解更多线索" in prompt


def test_build_event_prompt_no_players():
    state = _make_state()
    prompt = DMPrompts.build_event_user_prompt(state)
    assert "暂无聊天记录" in prompt
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_game_engine.py -v`
Expected: 5 passed

- [ ] **Step 5: Commit**

```bash
git add server/game_engine/__init__.py server/game_engine/prompts.py tests/test_game_engine.py
git commit -m "feat(game_engine): add centralized DM prompt management"
```

---

### Task 2: GameHost

**Files:**
- Create: `server/game_engine/host.py`
- Modify: `tests/test_game_engine.py`

- [ ] **Step 1: Write host tests**

Append to `tests/test_game_engine.py`:

```python
from unittest.mock import MagicMock, patch, AsyncMock
from server.game_engine.host import GameHost


def _make_host():
    registry = MagicMock()
    provider = MagicMock()
    registry.get_active.return_value = provider
    registry.resolve = MagicMock(return_value=registry)

    manager = MagicMock()
    hub = MagicMock()
    hub.broadcast = AsyncMock()
    hub.send_dm_private = AsyncMock()

    host = GameHost(registry, manager, hub)
    return host, registry, provider, manager, hub


def test_host_generate_event():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state()
    provider.chat.return_value = '{"public_event":"事件","private_clues":[],"dm_instruction":""}'

    result = host.generate_event(state)
    assert result["public_event"] == "事件"
    provider.chat.assert_called_once()


def test_host_generate_event_json_in_codeblock():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state()
    provider.chat.return_value = '```json\n{"public_event":"测试","private_clues":[],"dm_instruction":""}\n```'

    result = host.generate_event(state)
    assert result["public_event"] == "测试"


def test_host_generate_event_fallback_on_bad_json():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state()
    provider.chat.return_value = '这不是JSON格式'

    result = host.generate_event(state)
    assert "public_event" in result
    assert result["public_event"] == "这不是JSON格式"


def test_host_respond_to_chat():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state()
    provider.chat_stream.return_value = iter(["你好", "，我是DM"])

    result = host.respond_to_chat(state, "p1", "hello")
    assert result == "你好，我是DM"


def test_host_respond_to_chat_stream():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state()
    provider.chat_stream.return_value = iter(["chunk1", "chunk2"])

    chunks = list(host.respond_to_chat_stream(state, "p1", "hello"))
    assert chunks == ["chunk1", "chunk2"]


def test_host_should_intervene_idle():
    host, registry, provider, manager, hub = _make_host()
    from datetime import datetime, timedelta
    state = _make_state(
        phase="playing",
        dm_auto=True,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is True


def test_host_should_not_intervene_recent_activity():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state(
        phase="playing",
        dm_auto=True,
        last_player_activity=datetime.now(),
    )
    assert host.should_intervene(state) is False


def test_host_should_not_intervene_auto_disabled():
    host, registry, provider, manager, hub = _make_host()
    from datetime import datetime, timedelta
    state = _make_state(
        phase="playing",
        dm_auto=False,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is False


def test_host_should_not_intervene_not_playing():
    host, registry, provider, manager, hub = _make_host()
    from datetime import datetime, timedelta
    state = _make_state(
        phase="waiting",
        dm_auto=True,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is False
```

- [ ] **Step 2: Implement GameHost**

```python
# server/game_engine/host.py
import json
import logging
from typing import Generator
from server.models import GameState
from server.game_engine.prompts import DMPrompts

log = logging.getLogger(__name__)


class GameHost:
    def __init__(self, llm_registry, game_manager, ws_hub):
        self._registry = llm_registry
        self._manager = game_manager
        self._hub = ws_hub

    @staticmethod
    def parse_event_response(raw: str) -> dict:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            log.warning(f"[GameHost] JSON parse failed: {e}")
            return {"public_event": raw, "private_clues": [], "dm_instruction": ""}
        return {
            "public_event": data.get("public_event", ""),
            "private_clues": data.get("private_clues", []),
            "dm_instruction": data.get("dm_instruction", ""),
        }

    def generate_event(self, game_state: GameState) -> dict:
        messages = [{"role": "system", "content": DMPrompts.SYSTEM_EVENT}]
        history = game_state.host_message_history[-10:]
        for msg in history:
            messages.append({"role": "assistant", "content": msg})
        messages.append({"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)})

        raw = self._registry.get_active().chat(messages, temperature=0.8, timeout=300)
        return self.parse_event_response(raw)

    def generate_opening(self, game_state: GameState) -> dict:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_OPENING},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        raw = self._registry.get_active().chat(messages, temperature=0.8, timeout=300)
        return self.parse_event_response(raw)

    def generate_idle_nudge(self, game_state: GameState) -> dict:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_IDLE_NUDGE},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        raw = self._registry.get_active().chat(messages, temperature=0.7, timeout=120)
        return self.parse_event_response(raw)

    def respond_to_chat(self, game_state: GameState, player_id: str, player_message: str) -> str:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_CHAT},
            {"role": "user", "content": DMPrompts.build_chat_user_prompt(game_state, player_id, player_message)},
        ]
        full_reply = ""
        for chunk in self._registry.get_active().chat_stream(messages, temperature=0.8):
            full_reply += chunk
        return full_reply

    def respond_to_chat_stream(self, game_state: GameState, player_id: str, player_message: str) -> Generator[str, None, None]:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_CHAT},
            {"role": "user", "content": DMPrompts.build_chat_user_prompt(game_state, player_id, player_message)},
        ]
        yield from self._registry.get_active().chat_stream(messages, temperature=0.8)

    def generate_reveal(self, game_state: GameState) -> str:
        messages = [
            {"role": "system", "content": DMPrompts.SYSTEM_REVEAL},
            {"role": "user", "content": DMPrompts.build_event_user_prompt(game_state)},
        ]
        return self._registry.get_active().chat(messages, temperature=0.7, timeout=300)

    def should_intervene(self, game_state: GameState) -> bool:
        """Check if DM should autonomously intervene."""
        if not game_state.dm_auto:
            return False
        if game_state.phase != "playing":
            return False
        from datetime import datetime, timedelta
        if game_state.last_player_activity:
            idle_seconds = (datetime.now() - game_state.last_player_activity).total_seconds()
            return idle_seconds > 60
        return False
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_game_engine.py -v`
Expected: 14 passed

- [ ] **Step 4: Commit**

```bash
git add server/game_engine/host.py tests/test_game_engine.py
git commit -m "feat(game_engine): add GameHost with autonomous DM logic"
```

---

### Task 3: GameState Extensions + GameScheduler

**Files:**
- Modify: `server/models.py` — add auto-DM fields to GameState
- Create: `server/game_engine/scheduler.py`
- Modify: `tests/test_game_engine.py`

- [ ] **Step 1: Extend GameState**

Add these fields to `GameState` in `server/models.py`:

```python
    # Auto-DM fields
    dm_auto: bool = True
    last_player_activity: Optional[datetime] = None
    dm_intervention_history: List[dict] = Field(default_factory=list)
```

Add `Optional` to the typing import if not already there (it is: `from typing import Optional, List`).

- [ ] **Step 2: Write scheduler tests**

Append to `tests/test_game_engine.py`:

```python
import asyncio
from server.game_engine.scheduler import GameScheduler


def test_scheduler_start_stop():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.start("game1")
    assert "game1" in scheduler._tasks
    scheduler.stop("game1")
    # After stop, task should be cancelled
    assert "game1" not in scheduler._tasks


def test_scheduler_stop_nonexistent():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.stop("nonexistent")  # should not raise


def test_scheduler_start_already_running():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.start("game1")
    assert "game1" in scheduler._tasks
    scheduler.start("game1")  # should not duplicate
    assert "game1" in scheduler._tasks
```

- [ ] **Step 3: Implement GameScheduler**

```python
# server/game_engine/scheduler.py
import asyncio
import logging
from datetime import datetime
from typing import Optional

log = logging.getLogger(__name__)


class GameScheduler:
    """Periodic monitor that triggers autonomous DM behavior."""

    def __init__(self, game_host, game_manager, ws_hub):
        self._host = game_host
        self._manager = game_manager
        self._hub = ws_hub
        self._tasks: dict[str, asyncio.Task] = {}

    def start(self, game_id: str):
        if game_id in self._tasks:
            return
        self._tasks[game_id] = asyncio.create_task(self._monitor_loop(game_id))
        log.info(f"[Scheduler] Started monitoring game {game_id}")

    def stop(self, game_id: str):
        task = self._tasks.pop(game_id, None)
        if task:
            task.cancel()
            log.info(f"[Scheduler] Stopped monitoring game {game_id}")

    def stop_all(self):
        for game_id in list(self._tasks.keys()):
            self.stop(game_id)

    async def _monitor_loop(self, game_id: str):
        try:
            while True:
                await asyncio.sleep(30)
                state = self._manager.get_state(game_id)
                if not state or state.phase in ("revealed", "finished"):
                    break
                if self._host.should_intervene(state):
                    await self._do_intervention(game_id, state)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            log.error(f"[Scheduler] Error monitoring {game_id}: {e}")
        finally:
            self._tasks.pop(game_id, None)

    async def _do_intervention(self, game_id: str, state):
        try:
            event = await asyncio.wait_for(
                asyncio.to_thread(self._host.generate_idle_nudge, state),
                timeout=60,
            )
            result = self._manager.push_structured_event(game_id, event)
            if result and result["public_event"]:
                await self._hub.broadcast(game_id, {
                    "type": "event",
                    "content": result["public_event"],
                })
                for clue in result["private_clues"]:
                    await self._hub.send_dm_private(game_id, clue["player_id"], clue["content"])

            state.dm_intervention_history.append({
                "type": "idle_nudge",
                "timestamp": datetime.now().isoformat(),
                "event": event.get("public_event", "")[:100],
            })
            state.last_player_activity = datetime.now()
        except asyncio.TimeoutError:
            self._manager.add_dm_log(game_id, "自动干预超时（60s）")
        except Exception as e:
            self._manager.add_dm_log(game_id, f"自动干预失败: {e}")
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_game_engine.py -v`
Expected: 17 passed

- [ ] **Step 5: Commit**

```bash
git add server/models.py server/game_engine/scheduler.py tests/test_game_engine.py
git commit -m "feat(game_engine): add GameScheduler and GameState auto-DM fields"
```

---

### Task 4: Integration — Replace HostDM with GameHost

**Files:**
- Modify: `server/di/container.py` — register GameHost + GameScheduler
- Modify: `server/api/game.py` — use GameHost + scheduler
- Modify: `server/api/dm.py` — use GameHost
- Modify: `server/websocket_hub.py` — update player activity tracking
- Delete: `server/host_dm.py`

- [ ] **Step 1: Update DI container**

In `server/di/container.py`, update `register_services()`:

```python
def register_services(container):
    from server.game_manager import GameManager
    from server.websocket_hub import WebSocketHub
    from server.script_repository import ScriptRepository
    from server.script_service import ScriptService
    from server.script_engine.generator import ScriptGenerator
    from server.llm.registry import LLMRegistry
    from server.llm.openai_provider import OpenAIProvider
    from server.game_engine.host import GameHost
    from server.game_engine.scheduler import GameScheduler
    from server.config import config as app_config

    def _create_registry():
        registry = LLMRegistry()
        default = OpenAIProvider(
            name="default",
            endpoint=app_config.LLM_ENDPOINT,
            model=app_config.LLM_MODEL,
            api_key=app_config.LLM_API_KEY,
        )
        registry.register("default", default)
        return registry

    container.register("llm_registry", _create_registry, singleton=True)
    container.register("game_manager", GameManager, singleton=True)
    container.register("websocket_hub", WebSocketHub, singleton=True)
    container.register("script_repository", ScriptRepository, singleton=True)
    container.register("script_service", lambda: ScriptService(container.resolve("script_repository")), singleton=True)
    container.register("script_generator", lambda: ScriptGenerator(container.resolve("llm_registry")), singleton=True)

    def _create_host():
        return GameHost(
            container.resolve("llm_registry"),
            container.resolve("game_manager"),
            container.resolve("websocket_hub"),
        )

    def _create_scheduler():
        return GameScheduler(
            container.resolve("game_host"),
            container.resolve("game_manager"),
            container.resolve("websocket_hub"),
        )

    container.register("game_host", _create_host, singleton=True)
    container.register("game_scheduler", _create_scheduler, singleton=True)
```

Remove `from server.host_dm import HostDM` and the `host_dm` registration.

- [ ] **Step 2: Update `server/api/game.py`**

Replace all `_get_host_dm()` calls with `_get_game_host()` and `_get_scheduler()`.

```python
# server/api/game.py — updated
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json
import asyncio
from server.models import Script, Role, Clue, PlotOutline
from server.di import container
from server.middleware import require_admin
from server.utils.validation import AdminActionRequest
from server.constants import ACT_UNLOCK_MAP

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_game_host():
    return container.resolve("game_host")


def _get_hub():
    return container.resolve("websocket_hub")


def _get_scheduler():
    return container.resolve("game_scheduler")


@router.post("/rooms/{game_id}/start")
async def start_game(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    playable_count = len(state.players)
    if playable_count < 2:
        raise HTTPException(status_code=400, detail="至少需要 2 名玩家才能开始")
    if not state.script_generated:
        raise HTTPException(status_code=400, detail="先生成剧本再开始游戏")
    _get_manager().start_game(game_id)

    unlock_result = _get_manager().unlock_phase(game_id, "playing", 1)

    for pid, player in state.players.items():
        if player.role:
            if pid not in state.distributed_role_cards:
                state.distributed_role_cards[pid] = []
            state.distributed_role_cards[pid].append({
                "type": "role_card",
                "layer": "1",
                "player_id": pid,
                "data": {
                    "name": player.role.name,
                    "description": player.role.description,
                },
            })

    await _get_hub().broadcast(game_id, {
        "type": "phase_unlock",
        "phase": "playing",
        "act": 1,
    })

    for pid, player in state.players.items():
        if player.role:
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "1",
                "player_id": pid,
                "data": {
                    "name": player.role.name,
                    "description": player.role.description,
                },
            })

    if unlock_result:
        for pid, card_data in unlock_result["role_cards"].items():
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": "2",
                "player_id": pid,
                "data": card_data,
            })

        for pid, clue_list in unlock_result["clues"].items():
            for clue_data in clue_list:
                await _get_hub().send_to_player(game_id, pid, {
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        for pid, content in unlock_result["private_events"]:
            await _get_hub().send_dm_private(game_id, pid, content)

    # Start scheduler for autonomous DM
    _get_scheduler().start(game_id)

    asyncio.create_task(_auto_generate_opening(game_id))

    return {"game_id": game_id, "phase": state.phase}


async def _auto_generate_opening(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state or state.phase != "playing":
        return
    try:
        event = await asyncio.wait_for(
            asyncio.to_thread(_get_game_host().generate_opening, state),
            timeout=60,
        )
        result = _get_manager().push_structured_event(game_id, event)
        if result:
            if result["public_event"]:
                await _get_hub().broadcast(game_id, {
                    "type": "event",
                    "content": result["public_event"],
                })
            for clue in result["private_clues"]:
                await _get_hub().send_dm_private(game_id, clue["player_id"], clue["content"])
    except asyncio.TimeoutError:
        _get_manager().add_dm_log(game_id, "开场白生成超时（60s）")
    except Exception as e:
        _get_manager().add_dm_log(game_id, f"开场白生成失败：{e}")


def _push_event_generator(game_id: str, state):
    if state.phase != "playing":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在游戏进行中推进剧情\"}}\n\n"
        return

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        event = _get_game_host().generate_event(state)
        state.current_round += 1
        result = _get_manager().push_structured_event(game_id, event)

        done_payload = json.dumps({
            "type": "done",
            "public_event": result["public_event"] if result else "",
            "private_clues_count": len(result["private_clues"]) if result else 0,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/rooms/{game_id}/dm/push-event")
async def push_event(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    return StreamingResponse(
        _push_event_generator(game_id, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/rooms/{game_id}/advance-act")
async def advance_act(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    if state.phase not in ("playing",):
        raise HTTPException(status_code=400, detail="只能在游戏进行中推进幕")

    new_act = state.act + 1
    if new_act > 3:
        raise HTTPException(status_code=400, detail="已经是最后一幕，无法继续推进")

    unlock_result = _get_manager().unlock_phase(game_id, "playing", new_act)

    await _get_hub().broadcast(game_id, {
        "type": "phase_unlock",
        "phase": "playing",
        "act": new_act,
    })

    plot_text = ""
    act_key = f"act{new_act}"
    if hasattr(state.script, 'plot_outline') and state.script.plot_outline:
        plot_text = getattr(state.script.plot_outline, act_key, "")
    await _get_hub().broadcast(game_id, {
        "type": "act_transition",
        "act": new_act,
        "plot_summary": plot_text,
    })

    if unlock_result:
        act_key = f"act{new_act}"
        layer_to_unlock = ACT_UNLOCK_MAP.get(act_key, "2")

        for pid, card_data in unlock_result["role_cards"].items():
            await _get_hub().send_to_player(game_id, pid, {
                "type": "role_card",
                "layer": layer_to_unlock,
                "player_id": pid,
                "data": card_data,
            })

        for pid, clue_list in unlock_result["clues"].items():
            for clue_data in clue_list:
                await _get_hub().send_to_player(game_id, pid, {
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        for pid, content in unlock_result["private_events"]:
            await _get_hub().send_dm_private(game_id, pid, content)

    return {"status": "act_advanced", "act": new_act}


@router.post("/rooms/{game_id}/force-trial")
async def force_trial(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().force_trial(game_id)
    return {"status": "trial_started", "phase": state.phase}


def _end_game_generator(game_id: str, state):
    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        reveal_text = _get_game_host().generate_reveal(state)
        _get_manager().push_event(game_id, f"📢 真相揭晓：{reveal_text}")

        done_payload = json.dumps({
            "type": "done",
            "content": reveal_text,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"
    finally:
        _get_scheduler().stop(game_id)
        _get_manager().end_game(game_id)


@router.post("/rooms/{game_id}/end-game")
async def end_game(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
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


@router.post("/rooms/{game_id}/dm/toggle-auto")
async def toggle_auto(game_id: str, req: AdminActionRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)
    state.dm_auto = not state.dm_auto
    return {"auto": state.dm_auto}


@router.get("/rooms/{game_id}/dm/status")
async def dm_status(game_id: str):
    from datetime import datetime
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    idle_seconds = 0
    if state.last_player_activity:
        idle_seconds = (datetime.now() - state.last_player_activity).total_seconds()
    return {
        "auto": state.dm_auto,
        "phase": state.phase,
        "act": state.act,
        "idle_seconds": round(idle_seconds),
        "interventions": len(state.dm_intervention_history),
    }
```

- [ ] **Step 3: Update `server/api/dm.py`**

Replace `_get_host_dm()` with `_get_game_host()`:

```python
# server/api/dm.py — updated
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from datetime import datetime
from server.constants import DM_CHAT_RATE_LIMIT_SECONDS
from server.di import container
from server.middleware import require_admin
import json

router = APIRouter()


def _get_manager():
    return container.resolve("game_manager")


def _get_game_host():
    return container.resolve("game_host")


def _get_hub():
    return container.resolve("websocket_hub")


class PushEventRequest(BaseModel):
    player_id: str


class AddClueRequest(BaseModel):
    player_id: str
    clue_title: str
    clue_content: str


class DMPrivateRequest(BaseModel):
    player_id: str
    to_player_id: str
    content: str


class ChatResponseRequest(BaseModel):
    player_id: str
    content: str = Field(min_length=1, max_length=500)


@router.post("/rooms/{game_id}/dm/add-clue")
async def add_clue(game_id: str, req: AddClueRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().add_clue(game_id, req.clue_title, req.clue_content)
    _get_manager().push_event(game_id, f"🔍 新线索发现：{req.clue_title} — {req.clue_content}")
    return {"status": "clue_added"}


@router.post("/rooms/{game_id}/dm/private")
async def dm_private(game_id: str, req: DMPrivateRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    require_admin(req.player_id, game_id)

    _get_manager().add_chat_message(game_id, "__dm__", req.content, is_private=True, target_player_id=req.to_player_id)

    if req.to_player_id not in state.distributed_dm_private:
        state.distributed_dm_private[req.to_player_id] = []
    state.distributed_dm_private[req.to_player_id].append({
        "type": "dm_private",
        "from": "__dm__",
        "to": req.to_player_id,
        "content": req.content,
    })

    await _get_hub().send_dm_private(game_id, req.to_player_id, req.content)
    return {"status": "dm_private_sent"}


def _chat_response_generator(game_id: str, player_id: str, player_message: str, state):
    if state.phase not in ("playing", "waiting"):
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待中或游戏中与 DM 对话\"}}\n\n"
        return

    last_chat = state.dm_chat_cooldowns.get(player_id)
    if last_chat and (datetime.now() - last_chat).total_seconds() < DM_CHAT_RATE_LIMIT_SECONDS:
        yield f"data: {{\"type\": \"error\", \"message\": \"请等待 {DM_CHAT_RATE_LIMIT_SECONDS} 秒后再向 DM 提问\"}}\n\n"
        return

    state.dm_chat_cooldowns[player_id] = datetime.now()

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_reply = ""
        for chunk in _get_game_host().respond_to_chat_stream(state, player_id, player_message):
            full_reply += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        _get_manager().add_dm_chat_response(game_id, player_id, player_message, full_reply)

        done_payload = json.dumps({
            "type": "done",
            "content": full_reply,
        }, ensure_ascii=False)
        yield f"data: {done_payload}\n\n"

    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"


@router.post("/rooms/{game_id}/dm/chat-response")
async def chat_response(game_id: str, req: ChatResponseRequest):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    if req.player_id not in state.players:
        raise HTTPException(status_code=403, detail="Player not in room")

    _get_manager().add_chat_message(game_id, req.player_id, req.content, is_private=True, target_player_id="__dm__")

    return StreamingResponse(
        _chat_response_generator(game_id, req.player_id, req.content, state),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/rooms/{game_id}/dm/log")
async def get_dm_log(game_id: str):
    state = _get_manager().get_state(game_id)
    if not state:
        raise HTTPException(status_code=404, detail="Room not found")
    return {"dm_log": state.dm_log}
```

- [ ] **Step 4: Update `server/websocket_hub.py`**

In `handle_client_message`, update the `chat` and `private_chat` and `request_advance` handlers to:
1. Update `last_player_activity` on player messages
2. Use `_get_game_host()` instead of `host_dm`

Replace the module-level imports and `request_advance` handler:

At the top, replace:
```python
from server.game_manager import manager
from server.host_dm import host as host_dm
```
with:
```python
from server.game_manager import manager
from server.di import container
```

In `request_advance` handler, replace:
```python
event = await asyncio.to_thread(host_dm.generate_event, state)
```
with:
```python
game_host = container.resolve("game_host")
event = await asyncio.to_thread(game_host.generate_event, state)
```

Also add `last_player_activity` update in chat/private_chat handlers:
```python
state.last_player_activity = __import__('datetime').datetime.now()
```

- [ ] **Step 5: Delete `server/host_dm.py`**

```bash
rm server/host_dm.py
```

- [ ] **Step 6: Update `server/websocket_hub.py` module-level references**

The `hub = WebSocketHub()` singleton at the bottom is still used. The `manager` import is still used for direct access. Only `host_dm` import needs removal.

- [ ] **Step 7: Run full test suite**

Run: `pytest tests/test_game_engine.py tests/test_game_manager.py tests/test_api_rooms.py tests/test_llm_providers.py tests/test_script_engine.py -v`
Expected: all passed

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "refactor: replace HostDM with GameHost + GameScheduler, add autonomous DM mode"
```
