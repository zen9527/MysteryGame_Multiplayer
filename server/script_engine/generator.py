import json
import logging
from typing import Generator
from server.script_engine.models import ScriptV2
from server.script_engine.templates import get_template

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
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        data = json.loads(text)

        for role in data.get("roles", []):
            normalized = []
            for r in role.get("relationships", []):
                if isinstance(r, dict):
                    normalized.append(r)
                elif isinstance(r, str):
                    normalized.append({"target": r, "description": r})
            role["relationships"] = normalized

        for clue in data.get("clues", []):
            clue.setdefault("target_player_ids", [])
            clue.setdefault("unlock_phase", "act1")
            clue.setdefault("trigger_condition", None)

        for event in data.get("private_events", []):
            event.setdefault("trigger", None)

        data.setdefault("npcs", [])
        data.setdefault("timeline", [])
        data.setdefault("relationships", [])
        data.setdefault("atmosphere", "")
        data.setdefault("key_questions", [])

        return data

    def generate(self, genre: str, difficulty: str, player_count: int, estimated_time: int = 90) -> ScriptV2:
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
        system_prompt = "你是一名剧本杀设计师，请生成完整的剧本。只返回 JSON，不要其他内容。"
        user_prompt = self.build_prompt(genre, difficulty, player_count, estimated_time)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        yield from self._registry.get_active().chat_stream(messages, temperature=0.7)
