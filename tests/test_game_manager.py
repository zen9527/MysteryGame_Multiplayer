import pytest
from server.models import Script, Role, Clue, PlotOutline
from server.game_manager import GameManager


@pytest.fixture
def sample_script():
    return Script(
        title="测试剧本",
        genre="悬疑推理",
        difficulty="中等",
        estimated_time=60,
        background_story="测试背景",
        true_killer="角色 A",
        murder_method="测试手法",
        cover_up="测试掩盖",
        roles=[
            Role(id="1", name="角色 A", age=30, occupation="医生", description="医生", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
            Role(id="2", name="角色 B", age=25, occupation="教师", description="教师", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
        ],
        clues=[Clue(id="1", title="线索 1", content="内容", target_role=None, is_red_herring=False, content_hint="提示")],
        plot_outline=PlotOutline(act1="第一幕", act2="第二幕", act3="第三幕")
    )


@pytest.fixture
def game_manager():
    return GameManager()


# --- Original tests (adapted for new create_game signature) ---

def test_create_game(game_manager, sample_script):
    state = game_manager.create_game("test1", "creator_1")
    assert state.game_id == "test1"
    assert state.phase == "waiting"
    assert len(state.players) == 0


def test_add_player(game_manager, sample_script):
    game_manager.create_game("test1", "creator_1")
    # Need to set script with roles first
    state = game_manager.get_state("test1")
    state.script = sample_script
    player = game_manager.add_player("test1", "player1", "张三")
    assert player is not None
    assert player.name == "张三"
    assert len(game_manager.get_state("test1").players) == 1


def test_room_full(game_manager, sample_script):
    game_manager.create_game("test1", "creator_1")
    state = game_manager.get_state("test1")
    state.script = sample_script
    game_manager.add_player("test1", "player1", "张三")
    game_manager.add_player("test1", "player2", "李四")
    player = game_manager.add_player("test1", "player3", "王五")
    assert player is None  # 房间已满


def test_add_player_to_nonexistent_game(game_manager):
    player = game_manager.add_player("nonexistent", "player1", "张三")
    assert player is None


def test_get_state_nonexistent_game(game_manager):
    state = game_manager.get_state("nonexistent")
    assert state is None


def test_start_game(game_manager, sample_script):
    game_manager.create_game("test1", "creator_1")
    game_manager.start_game("test1")
    assert game_manager.get_state("test1").phase == "playing"


def test_check_consensus_no_votes(game_manager, sample_script):
    game_manager.create_game("test1", "creator_1")
    state = game_manager.get_state("test1")
    state.script = sample_script
    game_manager.add_player("test1", "player1", "张三")
    game_manager.add_player("test1", "player2", "李四")
    assert game_manager.check_consensus("test1") is False


def test_check_consensus_reached(game_manager, sample_script):
    from server.models import Vote
    game_manager.create_game("test1", "creator_1")
    state = game_manager.get_state("test1")
    state.script = sample_script
    game_manager.add_player("test1", "player1", "张三")
    game_manager.add_player("test1", "player2", "李四")
    game_manager.add_vote("test1", Vote(from_player_id="player1", target_role_name="角色 A", reasoning="推理"))
    game_manager.add_vote("test1", Vote(from_player_id="player2", target_role_name="角色 A", reasoning="推理"))
    assert game_manager.check_consensus("test1") is True


def test_check_consensus_not_reached(game_manager, sample_script):
    from server.models import Vote
    script = Script(
        title="测试剧本",
        genre="悬疑推理",
        difficulty="中等",
        estimated_time=60,
        background_story="测试背景",
        true_killer="角色 A",
        murder_method="测试手法",
        cover_up="测试掩盖",
        roles=[
            Role(id="1", name="角色 A", age=30, occupation="医生", description="医生", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
            Role(id="2", name="角色 B", age=25, occupation="教师", description="教师", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
            Role(id="3", name="角色 C", age=28, occupation="律师", description="律师", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
            Role(id="4", name="角色 D", age=35, occupation="警察", description="警察", background="背景", secret_task="秘密", alibi="不在场", motive="动机", relationships=[]),
        ],
        clues=[Clue(id="1", title="线索 1", content="内容", target_role=None, is_red_herring=False, content_hint="提示")],
        plot_outline=PlotOutline(act1="第一幕", act2="第二幕", act3="第三幕")
    )
    game_manager.create_game("test1", "creator_1")
    state = game_manager.get_state("test1")
    state.script = script
    game_manager.add_player("test1", "player1", "张三")
    game_manager.add_player("test1", "player2", "李四")
    game_manager.add_player("test1", "player3", "王五")
    game_manager.add_player("test1", "player4", "赵六")
    game_manager.add_vote("test1", Vote(from_player_id="player1", target_role_name="角色 A", reasoning="推理"))
    game_manager.add_vote("test1", Vote(from_player_id="player2", target_role_name="角色 B", reasoning="推理"))
    game_manager.add_vote("test1", Vote(from_player_id="player3", target_role_name="角色 C", reasoning="推理"))
    game_manager.add_vote("test1", Vote(from_player_id="player4", target_role_name="角色 D", reasoning="推理"))
    assert game_manager.check_consensus("test1") is False


# --- New admin method tests ---

def test_create_game_with_creator(game_manager):
    state = game_manager.create_game("test1", "creator_1")
    assert state.room_creator_id == "creator_1"
    assert state.phase == "waiting"
    assert state.act == 1
    assert not state.script_generated


def test_is_admin_true(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    assert game_manager.is_admin("test1", "admin_user") is True


def test_is_admin_false(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    assert game_manager.is_admin("test1", "other_user") is False


def test_kick_player(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    state = game_manager.get_state("test1")
    state.script.roles = [
        Role(id="1", name="角色A", age=30, occupation="医生", description="", background="", secret_task="", alibi="", motive=""),
        Role(id="2", name="角色B", age=25, occupation="教师", description="", background="", secret_task="", alibi="", motive=""),
    ]
    game_manager.add_player("test1", "p1", "张三")
    game_manager.add_player("test1", "p2", "李四")
    assert len(game_manager.get_state("test1").players) == 2
    game_manager.kick_player("test1", "p1")
    assert len(game_manager.get_state("test1").players) == 1


def test_force_trial(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    game_manager.start_game("test1")
    assert game_manager.get_state("test1").phase == "playing"
    game_manager.force_trial("test1")
    state = game_manager.get_state("test1")
    assert state.phase == "trial"
    assert state.act == 3


def test_end_game(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    game_manager.start_game("test1")
    game_manager.end_game("test1")
    assert game_manager.get_state("test1").phase == "revealed"


def test_push_event(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    game_manager.push_event("test1", "DM: 你发现了一封神秘信件...")
    state = game_manager.get_state("test1")
    assert len(state.public_messages) == 1
    assert state.public_messages[0].type == "event"


def test_add_clue(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    initial_count = len(game_manager.get_state("test1").script.clues)
    game_manager.add_clue("test1", "新线索", "血迹在地板上")
    assert len(game_manager.get_state("test1").script.clues) == initial_count + 1


def test_add_dm_log(game_manager, sample_script):
    game_manager.create_game("test1", "admin_user")
    game_manager.add_dm_log("test1", "LLM思考: 玩家已讨论5分钟，该推线索了")
    state = game_manager.get_state("test1")
    assert len(state.dm_log) == 1


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
    state.script = sample_script
    state.script.clues = [
        Clue(id="c1", title="线索1", content="内容", target_role=None, is_red_herring=False, content_hint="提示",
             target_player_ids=["角色 A"], unlock_phase="act2"),
    ]
    game_manager.add_player("test1", "p1", "张三")
    game_manager.add_player("test1", "p2", "李四")
    data = game_manager.distribute_clue("test1", "c1", "p1")
    assert data is not None
    assert data["title"] == "线索1"
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
    assert results[0][0] == "p1"
    assert results[0][1] == "私信内容"


def test_unlock_phase(game_manager, sample_script):
    from server.models import PrivateEvent, Clue
    game_manager.create_game("test1", "admin")
    state = game_manager.get_state("test1")
    state.script = sample_script
    state.script.clues = [
        Clue(id="c1", title="线索1", content="内容", target_role=None, is_red_herring=False, content_hint="提示",
             target_player_ids=["角色 A"], unlock_phase="act2"),
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
    assert state.phase == "playing"  # phase stays "playing", act changes
    assert state.act == 2
