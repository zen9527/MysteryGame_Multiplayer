import json
import logging
from server.llm_client import LLMClient
from server.models import GameState

log = logging.getLogger(__name__)


class HostDM:
    def __init__(self):
        self.llm = LLMClient()
        self.system_prompt = """你是一名专业的剧本杀主持人（DM）。你的职责：
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
  "public_event": "面向所有玩家公开的叙事/事件/线索。可以包含环境描写、公共线索、动态事件等。使用emoji和markdown增强可读性。如果没有公共内容，填空字符串。",
  "private_clues": [
    {"role": "角色名", "content": "该角色专属的线索内容"},
    ...
  ],
  "dm_instruction": "仅DM可见的行动指引。告诉玩家本轮该做什么（如：自由讨论、申请搜查、准备下一轮等）。不要暴露给玩家。"
}

注意事项：
- private_clues 的 role 字段必须是当前在场玩家的**角色名**（如"林默"、"苏婉"）
- 不要给所有玩家相同的专属线索——专属线索应该有差异性
- dm_instruction 是给你的内部操作指引，玩家看不到
- 只返回JSON，不要添加任何解释文字"""

    @staticmethod
    def parse_event_response(raw: str) -> dict:
        """Parse LLM response into structured event dict.

        Returns:
            {
                "public_event": str,
                "private_clues": [{"role": str, "content": str}, ...],
                "dm_instruction": str,
            }
        """
        text = raw.strip()
        # Try to extract JSON from markdown code block
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            log.warning(f"[DM] JSON parse failed, using raw text as public_event: {e}")
            return {
                "public_event": raw,
                "private_clues": [],
                "dm_instruction": "",
            }

        return {
            "public_event": data.get("public_event", ""),
            "private_clues": data.get("private_clues", []),
            "dm_instruction": data.get("dm_instruction", ""),
        }

    def generate_event(self, game_state: GameState) -> dict:
        """生成当前轮次的事件，返回结构化数据。

        Returns:
            {
                "public_event": str,        # 公屏消息
                "private_clues": list[dict], # [{role, content}, ...]
                "dm_instruction": str,       # DM内部指引
            }
        """
        history = game_state.host_message_history[-10:]
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

        user_input = f"""当前是第{game_state.current_round}轮，阶段: 第{game_state.act}幕
玩家状态：{', '.join(player_info)}
在场角色名：{', '.join(role_names)}
最近聊天：
{''.join(chat_summary) if chat_summary else '暂无聊天记录'}

请根据以上信息生成下一个游戏事件。如果是第一幕，发布开场背景介绍；
如果是第二幕，根据讨论情况投放线索或推进剧情；
如果是第三幕，引导审判和真相揭晓。

严格按JSON格式返回，包含 public_event、private_clues、dm_instruction 三个字段。"""

        raw = self.llm.host_event(self.system_prompt, history + [user_input])
        return self.parse_event_response(raw)

    def generate_script(self, system_prompt: str, user_prompt: str) -> str:
        """生成剧本"""
        return self.llm.generate_script(system_prompt, user_prompt)


host = HostDM()
