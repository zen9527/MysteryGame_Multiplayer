import pytest
from server.models import Script, Role, GameState, Message, PlotOutline
from server.game_manager import GameManager


@pytest.fixture
def game_manager():
    return GameManager()


@pytest.fixture
def game_state(game_manager):
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
    from server.models import Player
    state = GameState(
        game_id="test-game",
        phase="playing",
        act=1,
        room_creator_id="p1",
        players={"p1": Player(id="p1", name="张三", role_id="r1", role=script.roles[0])},
        script=script,
    )
    game_manager.games["test-game"] = state
    return state


def test_add_dm_chat_response_stores_message(game_state, game_manager):
    game_manager.add_dm_chat_response("test-game", "p1", "你好", "你好，我是DM")

    reply = game_state.private_messages[-1]
    assert reply.from_player_id == "__dm__"
    assert reply.content == "你好，我是DM"
    assert reply.type == "private"
    assert reply.to_player_id == "p1"


def test_add_dm_chat_response_caches_for_reconnect(game_state, game_manager):
    game_manager.add_dm_chat_response("test-game", "p1", "你好", "你好，我是DM")

    pending = game_manager.get_pending_distributions("test-game", "p1")
    dm_private_msgs = [m for m in pending if m.get("type") == "dm_private"]
    assert len(dm_private_msgs) >= 1
    assert dm_private_msgs[-1]["content"] == "你好，我是DM"


def test_add_dm_chat_response_nonexistent_game(game_manager):
    game_manager.add_dm_chat_response("nonexistent", "p1", "你好", "你好，我是DM")
    assert True


def test_add_dm_chat_response_multiple_responses(game_state, game_manager):
    game_manager.add_dm_chat_response("test-game", "p1", "你好", "你好，我是DM")
    game_manager.add_dm_chat_response("test-game", "p1", "第二个问题", "这是第二个回复")

    assert len(game_state.private_messages) == 2
    assert game_state.private_messages[0].content == "你好，我是DM"
    assert game_state.private_messages[1].content == "这是第二个回复"

    pending = game_manager.get_pending_distributions("test-game", "p1")
    dm_private_msgs = [m for m in pending if m.get("type") == "dm_private"]
    assert len(dm_private_msgs) == 2
