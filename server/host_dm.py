from server.llm_client import LLMClient
from server.models import GameState
from typing import List

class HostDM:
    def __init__(self):
        self.llm = LLMClient()
        self.system_prompt = """你是一名剧本杀主持人（DM）。你的职责：
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
- 保持悬疑感和趣味性"""

    def generate_event(self, game_state: GameState) -> str:
        """生成当前轮次的事件"""
        history = game_state.host_message_history[-10:]  # 最近 10 轮上下文
        user_input = f"当前是第{game_state.current_round}轮，玩家状态：{list(game_state.players.keys())}"
        return self.llm.host_event(self.system_prompt, history + [user_input])

    def generate_script(self, genre: str, player_count: int) -> str:
        """生成剧本"""
        system_prompt = "你是一名剧本杀设计师，请生成完整的剧本。"
        user_prompt = f"类型：{genre}，玩家数：{player_count}"
        return self.llm.generate_script(system_prompt, user_prompt)

host = HostDM()
