import pytest
from server.game_engine.prompts import DMPrompts
from server.models import GameState, Script, PlotOutline, Player, Role
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock
from server.game_engine.host import GameHost
from server.game_engine.scheduler import GameScheduler


def _make_state(**overrides):
    defaults = dict(
        game_id="test", phase="playing", act=1, room_creator_id="admin",
        players={},
        script=Script(
            title="T", genre="悬疑推理", difficulty="中等", estimated_time=90,
            background_story="", true_killer="", murder_method="", cover_up="",
            roles=[], clues=[], plot_outline=PlotOutline(act1="", act2="", act3=""),
        ),
    )
    defaults.update(overrides)
    return GameState(**defaults)


# Prompts
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


# GameHost
def _make_host():
    registry = MagicMock()
    provider = MagicMock()
    registry.get_active.return_value = provider
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
    state = _make_state(
        dm_auto=True,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is True


def test_host_should_not_intervene_recent_activity():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state(dm_auto=True, last_player_activity=datetime.now())
    assert host.should_intervene(state) is False


def test_host_should_not_intervene_auto_disabled():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state(
        dm_auto=False,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is False


def test_host_should_not_intervene_not_playing():
    host, registry, provider, manager, hub = _make_host()
    state = _make_state(
        phase="waiting",
        dm_auto=True,
        last_player_activity=datetime.now() - timedelta(seconds=120),
    )
    assert host.should_intervene(state) is False


# Scheduler
@pytest.mark.asyncio
async def test_scheduler_start_stop():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.start("game1")
    assert "game1" in scheduler._tasks
    scheduler.stop("game1")
    assert "game1" not in scheduler._tasks


def test_scheduler_stop_nonexistent():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.stop("nonexistent")  # should not raise


@pytest.mark.asyncio
async def test_scheduler_start_already_running():
    scheduler = GameScheduler(MagicMock(), MagicMock(), MagicMock())
    scheduler.start("game1")
    assert "game1" in scheduler._tasks
    scheduler.start("game1")  # should not duplicate
    assert "game1" in scheduler._tasks
