import pytest
import json
from server.script_engine.models import ScriptV2, NPC, TimelineEntry, Relationship
from server.models import Script, Role, Clue, PlotOutline
from server.script_engine.templates import get_template, get_all_genres, GENRE_TEMPLATES


def test_script_v2_inherits_script():
    script = ScriptV2(
        title="测试剧本",
        genre="悬疑推理",
        difficulty="中等",
        estimated_time=90,
        background_story="故事背景",
        true_killer="角色A",
        murder_method="毒杀",
        cover_up="伪装自杀",
        roles=[],
        clues=[],
        plot_outline=PlotOutline(act1="", act2="", act3=""),
    )
    assert isinstance(script, Script)
    assert script.title == "测试剧本"
    assert script.npcs == []
    assert script.timeline == []
    assert script.relationships == []
    assert script.atmosphere == ""


def test_script_v2_with_enhanced_fields():
    npc = NPC(
        name="张老三", age=50, occupation="酒馆老板",
        description="神秘的老头", relationship_to_victim="债主",
        knows=["受害者的秘密"],
    )
    entry = TimelineEntry(time="21:30", event="一声尖叫", witnesses=["角色A"])
    rel = Relationship(from_role="角色A", to_role="角色B", relation="情人", tension=8)

    script = ScriptV2(
        title="迷雾之夜", genre="悬疑推理", difficulty="困难", estimated_time=120,
        background_story="暴风雪山庄", true_killer="角色C",
        murder_method="密室杀人", cover_up="伪造不在场证明",
        roles=[], clues=[], plot_outline=PlotOutline(act1="", act2="", act3=""),
        npcs=[npc], timeline=[entry], relationships=[rel],
        atmosphere="紧张压抑", key_questions=["谁是凶手？", "动机是什么？"],
    )
    assert len(script.npcs) == 1
    assert script.npcs[0].name == "张老三"
    assert len(script.timeline) == 1
    assert len(script.relationships) == 1
    assert script.relationships[0].tension == 8
    assert script.atmosphere == "紧张压抑"
    assert len(script.key_questions) == 2


def test_script_v2_defaults():
    script = ScriptV2(
        title="X", genre="悬疑推理", difficulty="中等", estimated_time=90,
        background_story="", true_killer="", murder_method="", cover_up="",
        roles=[], clues=[], plot_outline=PlotOutline(act1="", act2="", act3=""),
    )
    assert script.npcs == []
    assert script.atmosphere == ""


def test_npc_model():
    npc = NPC(name="王五", age=35, occupation="商人", description="富有但吝啬",
              relationship_to_victim="合伙人", knows=["商业秘密", "债务纠纷"])
    assert npc.knows == ["商业秘密", "债务纠纷"]


def test_timeline_entry():
    entry = TimelineEntry(time="22:00", event="发现尸体", witnesses=["A", "B"])
    assert len(entry.witnesses) == 2


def test_relationship():
    rel = Relationship(from_role="A", to_role="B", relation="仇人", tension=9)
    assert rel.tension == 9


# Templates
def test_get_template_known():
    t = get_template("悬疑推理")
    assert "atmosphere_hint" in t
    assert "tone" in t
    assert "clue_style" in t
    assert "key_elements" in t


def test_get_template_fallback():
    t = get_template("未知类型")
    assert t == GENRE_TEMPLATES["悬疑推理"]


def test_get_all_genres():
    genres = get_all_genres()
    assert "悬疑推理" in genres
    assert "古风权谋" in genres
    assert len(genres) == 6


# Generator
from unittest.mock import MagicMock
from server.script_engine.generator import ScriptGenerator


def _make_registry(response='{"title":"测试","genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"故事","true_killer":"A","murder_method":"毒","cover_up":"伪装","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}'):
    provider = MagicMock()
    provider.chat.return_value = response
    provider.chat_stream.return_value = iter([response])
    registry = MagicMock()
    registry.get_active.return_value = provider
    return registry


def test_generator_build_prompt():
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    prompt = gen.build_prompt("悬疑推理", "中等", 4, 90)
    assert "悬疑推理" in prompt
    assert "中等" in prompt
    assert "4" in prompt


def test_generator_build_prompt_includes_template():
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    prompt = gen.build_prompt("古风权谋", "困难", 5, 120)
    assert "朝堂" in prompt


def test_generator_build_prompt_includes_v2_fields():
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    prompt = gen.build_prompt("悬疑推理", "中等", 4, 90)
    assert "npcs" in prompt.lower() or "NPC" in prompt
    assert "timeline" in prompt.lower()
    assert "relationship" in prompt.lower() or "关系" in prompt


def test_generator_generate():
    good_json = json.dumps({
        "title": "迷雾山庄", "genre": "悬疑推理", "difficulty": "中等", "estimated_time": 90,
        "background_story": "暴风雪山庄杀人事件", "true_killer": "张三",
        "murder_method": "毒杀", "cover_up": "伪装自杀",
        "roles": [{"name": "张三", "age": 30, "occupation": "医生", "description": "沉默寡言",
                   "background": "曾经军医", "secret_task": "隐藏身份", "alibi": "在书房看书",
                   "motive": "复仇", "relationships": []}],
        "clues": [{"title": "毒瓶", "content": "一个装有毒药的小瓶", "target_role": None,
                    "is_red_herring": False, "content_hint": "有毒",
                    "target_player_ids": [], "unlock_phase": "act1", "trigger_condition": None}],
        "plot_outline": {"act1": "背景", "act2": "调查", "act3": "审判"},
        "private_events": [], "npcs": [], "timeline": [],
        "relationships": [], "atmosphere": "紧张", "key_questions": ["谁杀了人？"],
    })
    registry = _make_registry(good_json)
    gen = ScriptGenerator(registry)
    script = gen.generate("悬疑推理", "中等", 4, 90)
    assert script.title == "迷雾山庄"
    assert len(script.roles) == 1
    assert isinstance(script, ScriptV2)


def test_generator_normalize_wraps_json_in_code_block():
    raw = '```json\n{"title":"T","genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}\n```'
    gen = ScriptGenerator(_make_registry())
    data = gen.normalize_script_json(raw)
    assert data["title"] == "T"


def test_generator_normalize_plain_json():
    raw = '{"title":"T","genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}'
    gen = ScriptGenerator(_make_registry())
    data = gen.normalize_script_json(raw)
    assert data["title"] == "T"


def test_generator_normalize_adds_defaults():
    raw = json.dumps({
        "title": "T", "genre": "悬疑推理", "difficulty": "中等", "estimated_time": 90,
        "background_story": "", "true_killer": "", "murder_method": "", "cover_up": "",
        "roles": [{"name": "A", "age": 20, "occupation": "x", "description": "x",
                   "background": "x", "secret_task": "x", "alibi": "x", "motive": "x",
                   "relationships": ["string_target"]}],
        "clues": [{"title": "c", "content": "c", "target_role": None,
                    "is_red_herring": False, "content_hint": "h"}],
        "plot_outline": {"act1": "", "act2": "", "act3": ""},
    })
    gen = ScriptGenerator(_make_registry())
    data = gen.normalize_script_json(raw)
    assert isinstance(data["roles"][0]["relationships"][0], dict)
    assert data["clues"][0]["unlock_phase"] == "act1"
    assert data["clues"][0]["target_player_ids"] == []


def test_generator_generate_stream():
    chunks = ['{"title":', '"测试"', ', "genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}']
    registry = _make_registry()
    registry.get_active.return_value.chat_stream.return_value = iter(chunks)
    gen = ScriptGenerator(registry)
    collected = list(gen.generate_stream("悬疑推理", "中等", 4, 90))
    assert len(collected) == 3
