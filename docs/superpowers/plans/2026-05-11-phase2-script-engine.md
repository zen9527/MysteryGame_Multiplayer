# Phase 2: Script Engine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create a dedicated Script Engine module with enhanced script models (NPCs, timeline, relationships) and a generator that produces richer scripts via LLM.

**Architecture:** New `server/script_engine/` package with `ScriptV2` extending `Script` for backward compatibility, `ScriptGenerator` class that encapsulates all LLM script generation prompts and JSON normalization, and genre templates for better output quality. `api/script.py` delegates to `ScriptGenerator` instead of calling LLM directly.

**Tech Stack:** Python, Pydantic v2, LLMRegistry (from Phase 1)

**Spec:** `docs/superpowers/specs/2026-05-11-modular-refactor-design.md` Section 2

---

## File Map

| Action | Path | Responsibility |
|--------|------|---------------|
| Create | `server/script_engine/__init__.py` | Package init |
| Create | `server/script_engine/models.py` | ScriptV2, NPC, TimelineEntry, Relationship |
| Create | `server/script_engine/templates.py` | Genre-specific generation templates |
| Create | `server/script_engine/generator.py` | ScriptGenerator — prompt building, JSON normalization, generation |
| Create | `tests/test_script_engine.py` | Tests for models, templates, generator |
| Modify | `server/api/script.py` | Use ScriptGenerator instead of direct LLM calls |
| Modify | `server/di/container.py` | Register ScriptGenerator |

---

### Task 1: Enhanced Script Models

**Files:**
- Create: `server/script_engine/__init__.py`
- Create: `server/script_engine/models.py`
- Create: `tests/test_script_engine.py`

- [ ] **Step 1: Create package init**

```python
# server/script_engine/__init__.py
from server.script_engine.models import ScriptV2, NPC, TimelineEntry, Relationship
from server.script_engine.generator import ScriptGenerator

__all__ = ["ScriptV2", "NPC", "TimelineEntry", "Relationship", "ScriptGenerator"]
```

- [ ] **Step 2: Create enhanced models**

```python
# server/script_engine/models.py
from pydantic import BaseModel, Field
from typing import List, Optional
from server.models import Script


class NPC(BaseModel):
    name: str
    age: int
    occupation: str
    description: str
    relationship_to_victim: str
    knows: List[str] = Field(default_factory=list)


class TimelineEntry(BaseModel):
    time: str  # "21:30" or "案发前2小时"
    event: str
    witnesses: List[str] = Field(default_factory=list)


class Relationship(BaseModel):
    from_role: str
    to_role: str
    relation: str
    tension: int = 0  # 0-10


class ScriptV2(Script):
    """Extended script model — backward compatible with Script."""
    npcs: List[NPC] = Field(default_factory=list)
    timeline: List[TimelineEntry] = Field(default_factory=list)
    relationships: List[Relationship] = Field(default_factory=list)
    atmosphere: str = ""
    key_questions: List[str] = Field(default_factory=list)
```

- [ ] **Step 3: Write tests for models**

```python
# tests/test_script_engine.py
import pytest
from server.script_engine.models import ScriptV2, NPC, TimelineEntry, Relationship
from server.models import Script, Role, Clue, PlotOutline


def test_script_v2_inherits_script():
    """ScriptV2 is backward compatible with Script."""
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
        name="张老三",
        age=50,
        occupation="酒馆老板",
        description="神秘的老头",
        relationship_to_victim="债主",
        knows=["受害者的秘密"],
    )
    entry = TimelineEntry(time="21:30", event="一声尖叫", witnesses=["角色A"])
    rel = Relationship(from_role="角色A", to_role="角色B", relation="情人", tension=8)

    script = ScriptV2(
        title="迷雾之夜",
        genre="悬疑推理",
        difficulty="困难",
        estimated_time=120,
        background_story="暴风雪山庄",
        true_killer="角色C",
        murder_method="密室杀人",
        cover_up="伪造不在场证明",
        roles=[],
        clues=[],
        plot_outline=PlotOutline(act1="", act2="", act3=""),
        npcs=[npc],
        timeline=[entry],
        relationships=[rel],
        atmosphere="紧张压抑",
        key_questions=["谁是凶手？", "动机是什么？"],
    )

    assert len(script.npcs) == 1
    assert script.npcs[0].name == "张老三"
    assert len(script.timeline) == 1
    assert script.timeline[0].time == "21:30"
    assert len(script.relationships) == 1
    assert script.relationships[0].tension == 8
    assert script.atmosphere == "紧张压抑"
    assert len(script.key_questions) == 2


def test_script_v2_defaults():
    script = ScriptV2(
        title="X",
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
    assert script.npcs == []
    assert script.timeline == []
    assert script.relationships == []
    assert script.atmosphere == ""
    assert script.key_questions == []


def test_npc_model():
    npc = NPC(
        name="王五",
        age=35,
        occupation="商人",
        description="富有但吝啬",
        relationship_to_victim="合伙人",
        knows=["商业秘密", "债务纠纷"],
    )
    assert npc.knows == ["商业秘密", "债务纠纷"]


def test_timeline_entry():
    entry = TimelineEntry(time="22:00", event="发现尸体", witnesses=["A", "B"])
    assert len(entry.witnesses) == 2


def test_relationship():
    rel = Relationship(from_role="A", to_role="B", relation="仇人", tension=9)
    assert rel.tension == 9
```

- [ ] **Step 4: Run tests**

Run: `pytest tests/test_script_engine.py -v`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add server/script_engine/__init__.py server/script_engine/models.py tests/test_script_engine.py
git commit -m "feat(script_engine): add enhanced ScriptV2 models with NPCs, timeline, relationships"
```

---

### Task 2: Genre Templates

**Files:**
- Create: `server/script_engine/templates.py`
- Modify: `tests/test_script_engine.py`

- [ ] **Step 1: Create templates**

```python
# server/script_engine/templates.py
GENRE_TEMPLATES = {
    "悬疑推理": {
        "atmosphere_hint": "封闭空间，暴风雪山庄模式。浓雾笼罩，断桥断路，所有人都被困其中。",
        "tone": "紧张压抑，步步惊心。每个角色都有秘密，每条线索都可能指向不同的方向。",
        "clue_style": "物证为主（日记、信件、指纹、毒物），辅以人证矛盾。",
        "key_elements": ["密室或半封闭空间", "时间线错位", "不在场证明", "伪造证据"],
    },
    "古风权谋": {
        "atmosphere_hint": "朝堂之上暗流涌动，后宫之中步步惊心。表面歌舞升平，实则危机四伏。",
        "tone": "古风典雅，文言与白话交融。阴谋与权术交织，忠奸难辨。",
        "clue_style": "以书信、密旨、诗词暗语、宫廷器物为主。",
        "key_elements": ["权力斗争", "暗中结盟", "毒计暗杀", "宫闱秘闻"],
    },
    "现代都市": {
        "atmosphere_hint": "繁华都市的阴暗角落，霓虹灯下的秘密交易。表面光鲜的社交圈中暗藏杀机。",
        "tone": "写实风格，贴近生活。人物关系复杂，利益纠葛深沉。",
        "clue_style": "手机记录、监控录像、银行流水、社交媒体痕迹。",
        "key_elements": ["商业阴谋", "情感纠葛", "网络犯罪", "身份伪造"],
    },
    "恐怖惊悚": {
        "atmosphere_hint": "废弃建筑中回荡着诡异的声响，午夜时分，镜中映出不属于你的身影。",
        "tone": "阴森恐怖，悬念迭起。超自然与现实的边界模糊不清。",
        "clue_style": "古老符文、灵异照片、诡异的仪式物品、神秘书信。",
        "key_elements": ["诅咒传说", "灵异事件", "心理恐惧", "禁忌仪式"],
    },
    "欢乐搞笑": {
        "atmosphere_hint": "看似严肃的场合中不断出现荒诞的误会和笑料，每个人都藏着令人啼笑皆非的秘密。",
        "tone": "轻松幽默，反转不断。在欢乐中隐藏着意想不到的真相。",
        "clue_style": "搞笑的物证（表情包截图、荒唐的购物记录、尴尬的照片）。",
        "key_elements": ["乌龙误会", "身份搞错", "搞笑秘密", "意外反转"],
    },
    "科幻未来": {
        "atmosphere_hint": "空间站中警报长鸣，AI系统突然失控。在星际旅途中，没有人能逃脱。",
        "tone": "科技感与悬疑并重。人类与AI的博弈，虚拟与现实的交错。",
        "clue_style": "数据日志、AI行为记录、生物扫描结果、全息影像。",
        "key_elements": ["AI失控", "时空异常", "基因改造", "意识上传"],
    },
}


def get_template(genre: str) -> dict:
    """Get genre template, falling back to 悬疑推理 for unknown genres."""
    return GENRE_TEMPLATES.get(genre, GENRE_TEMPLATES["悬疑推理"])


def get_all_genres() -> list[str]:
    """Return list of all supported genres."""
    return list(GENRE_TEMPLATES.keys())
```

- [ ] **Step 2: Add template tests**

Append to `tests/test_script_engine.py`:

```python
from server.script_engine.templates import get_template, get_all_genres, GENRE_TEMPLATES


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
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_script_engine.py -v`
Expected: 10 passed

- [ ] **Step 4: Commit**

```bash
git add server/script_engine/templates.py tests/test_script_engine.py
git commit -m "feat(script_engine): add genre-specific generation templates"
```

---

### Task 3: Script Generator

**Files:**
- Create: `server/script_engine/generator.py`
- Modify: `tests/test_script_engine.py`

- [ ] **Step 1: Write generator tests**

Append to `tests/test_script_engine.py`:

```python
from unittest.mock import MagicMock, patch
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
    assert "90" in prompt


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
    assert "relationships" in prompt.lower() or "关系" in prompt


def test_generator_generate():
    good_json = json.dumps({
        "title": "迷雾山庄",
        "genre": "悬疑推理",
        "difficulty": "中等",
        "estimated_time": 90,
        "background_story": "暴风雪山庄杀人事件",
        "true_killer": "张三",
        "murder_method": "毒杀",
        "cover_up": "伪装自杀",
        "roles": [{"name": "张三", "age": 30, "occupation": "医生", "description": "沉默寡言", "background": "曾经军医", "secret_task": "隐藏身份", "alibi": "在书房看书", "motive": "复仇", "relationships": []}],
        "clues": [{"title": "毒瓶", "content": "一个装有毒药的小瓶", "target_role": None, "is_red_herring": False, "content_hint": "有毒", "target_player_ids": [], "unlock_phase": "act1", "trigger_condition": None}],
        "plot_outline": {"act1": "背景", "act2": "调查", "act3": "审判"},
        "private_events": [],
        "npcs": [],
        "timeline": [],
        "relationships": [],
        "atmosphere": "紧张",
        "key_questions": ["谁杀了人？"],
    })
    registry = _make_registry(good_json)
    gen = ScriptGenerator(registry)
    script = gen.generate("悬疑推理", "中等", 4, 90)
    assert script.title == "迷雾山庄"
    assert len(script.roles) == 1
    assert isinstance(script, ScriptV2)


def test_generator_normalize_wraps_json_in_code_block():
    raw = '```json\n{"title":"T","genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}\n```'
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    data = gen.normalize_script_json(raw)
    assert data["title"] == "T"


def test_generator_normalize_plain_json():
    raw = '{"title":"T","genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}'
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    data = gen.normalize_script_json(raw)
    assert data["title"] == "T"


def test_generator_normalize_adds_defaults():
    raw = json.dumps({
        "title": "T", "genre": "悬疑推理", "difficulty": "中等", "estimated_time": 90,
        "background_story": "", "true_killer": "", "murder_method": "", "cover_up": "",
        "roles": [{"name": "A", "age": 20, "occupation": "x", "description": "x", "background": "x", "secret_task": "x", "alibi": "x", "motive": "x", "relationships": ["string_target"]}],
        "clues": [{"title": "c", "content": "c", "target_role": None, "is_red_herring": False, "content_hint": "h"}],
        "plot_outline": {"act1": "", "act2": "", "act3": ""},
    })
    registry = _make_registry()
    gen = ScriptGenerator(registry)
    data = gen.normalize_script_json(raw)
    # String relationships should be converted to dict
    assert isinstance(data["roles"][0]["relationships"][0], dict)
    # Clue should have defaults
    assert data["clues"][0]["unlock_phase"] == "act1"
    assert data["clues"][0]["target_player_ids"] == []


def test_generator_generate_stream():
    chunks = ['{"title":', '"测试"', ', "genre":"悬疑推理","difficulty":"中等","estimated_time":90,"background_story":"","true_killer":"","murder_method":"","cover_up":"","roles":[],"clues":[],"plot_outline":{"act1":"","act2":"","act3":""}}']
    registry = _make_registry()
    registry.get_active.return_value.chat_stream.return_value = iter(chunks)
    gen = ScriptGenerator(registry)
    collected = list(gen.generate_stream("悬疑推理", "中等", 4, 90))
    assert len(collected) == 3
```

- [ ] **Step 2: Implement generator**

```python
# server/script_engine/generator.py
import json
import logging
from typing import Generator, Optional
from server.script_engine.models import ScriptV2
from server.script_engine.templates import get_template
from server.models import Script

log = logging.getLogger(__name__)


class ScriptGenerator:
    def __init__(self, llm_registry):
        self._registry = llm_registry

    def build_prompt(self, genre: str, difficulty: str, player_count: int, estimated_time: int) -> str:
        template = get_template(genre)
        return f"""请生成一个完整的剧本杀剧本，以 JSON 格式返回。

类型：{genre}
难度：{difficulty}
预计时长：{estimated_time}分钟
玩家数量：{player_count}人（需要{player_count}个角色）

=== 类型风格指引 ===
氛围：{template['atmosphere_hint']}
基调：{template['tone']}
线索风格：{template['clue_style']}
核心元素：{'、'.join(template['key_elements'])}

=== JSON 格式要求 ===
{{
  "title": "剧本标题",
  "genre": "{genre}",
  "difficulty": "{difficulty}",
  "estimated_time": {estimated_time},
  "background_story": "背景故事（200-500字）",
  "true_killer": "凶手角色名",
  "murder_method": "作案手法描述",
  "cover_up": "掩盖手段描述",
  "atmosphere": "氛围描述（一句话）",
  "roles": [
    {{
      "id": "role_1",
      "name": "角色名",
      "age": 年龄,
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
      "target_player_ids": [],
      "unlock_phase": "act2",
      "trigger_condition": null
    }}
  ],
  "plot_outline": {{
    "act1": "第一幕概述",
    "act2": "第二幕概述",
    "act3": "第三幕概述"
  }},
  "private_events": [
    {{
      "phase": "act2",
      "target_role_name": "角色名",
      "content": "DM私信内容",
      "trigger": null
    }}
  ],
  "npcs": [
    {{
      "name": "NPC名",
      "age": 40,
      "occupation": "职业",
      "description": "描述",
      "relationship_to_victim": "与受害者的关系",
      "knows": ["知道的信息1", "知道的信息2"]
    }}
  ],
  "timeline": [
    {{
      "time": "21:30",
      "event": "发生的事件",
      "witnesses": ["目击者角色名"]
    }}
  ],
  "relationships": [
    {{
      "from_role": "角色A",
      "to_role": "角色B",
      "relation": "关系描述",
      "tension": 5
    }}
  ],
  "key_questions": ["关键问题1", "关键问题2", "关键问题3"]
}}

=== 注意事项 ===
- 确保有{player_count}个角色
- 每个角色的 id 必须唯一（role_1, role_2...）
- 线索数量至少 5 条，分散在 act1（2-3条）和 act2（3-5条）
- 凶手必须是其中一个角色
- target_player_ids 使用角色名
- 生成 2-3 个 NPC（非玩家角色，用于丰富剧情）
- 时间线至少 5 个关键时间点
- 角色间关系至少 {player_count} 对（含 tension 紧张度 0-10）
- 生成 3-5 个关键问题供玩家思考
- 只返回JSON，不要其他内容"""

    def normalize_script_json(self, raw: str) -> dict:
        """Extract and normalize JSON from LLM output."""
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)

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
            clue.setdefault("unlock_phase", "act1")
            clue.setdefault("trigger_condition", None)

        private_events = data.get("private_events", [])
        for event in private_events:
            event.setdefault("trigger", None)

        data.setdefault("npcs", [])
        data.setdefault("timeline", [])
        data.setdefault("relationships", [])
        data.setdefault("atmosphere", "")
        data.setdefault("key_questions", [])

        return data

    def generate(self, genre: str, difficulty: str, player_count: int, estimated_time: int = 90) -> ScriptV2:
        """Generate a complete script via LLM."""
        system_prompt = "你是一名剧本杀设计师，请生成完整的剧本。只返回 JSON，不要其他内容。"
        user_prompt = self.build_prompt(genre, difficulty, player_count, estimated_time)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        raw = self._registry.get_active().chat(messages, temperature=0.7, timeout=300)
        data = self.normalize_script_json(raw)
        return ScriptV2(**data)

    def generate_stream(self, genre: str, difficulty: str, player_count: int, estimated_time: int = 90) -> Generator[str, None, None]:
        """Stream script generation chunks via LLM."""
        system_prompt = "你是一名剧本杀设计师，请生成完整的剧本。只返回 JSON，不要其他内容。"
        user_prompt = self.build_prompt(genre, difficulty, player_count, estimated_time)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        yield from self._registry.get_active().chat_stream(messages, temperature=0.7)
```

- [ ] **Step 3: Run tests**

Run: `pytest tests/test_script_engine.py -v`
Expected: 20 passed

- [ ] **Step 4: Commit**

```bash
git add server/script_engine/generator.py tests/test_script_engine.py
git commit -m "feat(script_engine): add ScriptGenerator with prompt building and JSON normalization"
```

---

### Task 4: Integrate ScriptGenerator into API and DI

**Files:**
- Modify: `server/di/container.py`
- Modify: `server/api/script.py`

- [ ] **Step 1: Register ScriptGenerator in DI**

Add to `register_services()` in `server/di/container.py`, after the existing `script_service` registration:

```python
    container.register("script_generator", lambda: ScriptGenerator(container.resolve("llm_registry")), singleton=True)
```

Add the import at the top of `register_services()`:
```python
    from server.script_engine.generator import ScriptGenerator
```

- [ ] **Step 2: Update `api/script.py` to use ScriptGenerator**

Replace the current `_generate_script_generator` function. The key changes:
- Use `container.resolve("script_generator")` instead of `_get_host_dm().llm.generate_script_stream()`
- Use `ScriptGenerator.generate_stream()` for streaming
- Use `ScriptGenerator.normalize_script_json()` for JSON parsing
- Keep the SSE wrapper logic the same

Replace the generator function:

```python
def _generate_script_generator(game_id: str, req: ScriptGenerationRequest):
    """Generator for SSE streaming of script generation."""
    state = _get_manager().get_state(game_id)
    if not state:
        yield f"data: {{\"type\": \"error\", \"message\": \"Room not found\"}}\n\n"
        return
    if state.phase != "waiting":
        yield f"data: {{\"type\": \"error\", \"message\": \"只能在等待阶段生成剧本\"}}\n\n"

    from server.script_engine.models import ScriptV2
    script_gen = container.resolve("script_generator")

    try:
        yield f"data: {{\"type\": \"start\"}}\n\n"

        full_text = ""
        for chunk in script_gen.generate_stream(req.genre, req.difficulty, req.player_count, req.estimated_time):
            full_text += chunk
            yield f"data: {{\"type\": \"chunk\", \"content\": {json.dumps(chunk, ensure_ascii=False)}}}\n\n"

        script_dict = script_gen.normalize_script_json(full_text)
        script = ScriptV2(**script_dict)
        _get_manager().set_script(game_id, script)
        state.script_generated = True

        yield f"data: {{\"type\": \"done\", \"title\": {json.dumps(script.title, ensure_ascii=False)}, \"roles_count\": {len(script.roles)}, \"clues_count\": {len(script.clues)}}}\n\n"
    except Exception as e:
        yield f"data: {{\"type\": \"error\", \"message\": {json.dumps(str(e), ensure_ascii=False)}}}\n\n"
```

Also update `set_script` to handle ScriptV2:
- In `set_script`, change `Script(**script_data)` to `ScriptV2(**script_data)` and import `ScriptV2`.

- [ ] **Step 3: Run all tests**

Run: `pytest tests/test_script_engine.py tests/test_game_manager.py tests/test_api_rooms.py -v`
Expected: all passed

- [ ] **Step 4: Commit**

```bash
git add server/di/container.py server/api/script.py
git commit -m "feat: integrate ScriptGenerator into API and DI container"
```
