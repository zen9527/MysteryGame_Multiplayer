from server.llm_client import LLMClient
from server.models import GameState


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
- 给不同角色投放个性化线索（利用 target_role）
- 保持悬疑感和趣味性
- 返回内容简洁明了，使用中文，适合直接展示给玩家"""

    def generate_event(self, game_state: GameState) -> str:
        """生成当前轮次的事件"""
        history = game_state.host_message_history[-10:]
        player_info = []
        for pid, p in game_state.players.items():
            role_name = p.role.name if p.role else "未分配"
            player_info.append(f"{p.name}({role_name})")

        chat_summary = []
        for msg in game_state.public_messages[-20:]:
            sender = next(
                (p.name for pid, p in game_state.players.items() if pid == msg.from_player_id),
                msg.from_player_id,
            )
            chat_summary.append(f"{sender}: {msg.content}")

        user_input = f"""当前是第{game_state.current_round}轮，阶段: 第{game_state.act}幕
玩家状态：{', '.join(player_info)}
最近聊天：
{''.join(chat_summary) if chat_summary else '暂无聊天记录'}

请根据以上信息生成下一个游戏事件。如果是第一幕，发布开场背景介绍；
如果是第二幕，根据讨论情况投放线索或推进剧情；
如果是第三幕，引导审判和真相揭晓。"""

        return self.llm.host_event(self.system_prompt, history + [user_input])

    def generate_script(self, system_prompt: str, user_prompt: str) -> str:
        """生成剧本"""
        return self.llm.generate_script(system_prompt, user_prompt)


host = HostDM()
