from server.models import GameState, Player, Script, Message, Accusation, Vote, Clue, PlotOutline
from datetime import datetime, timedelta
from typing import Optional


class GameManager:
    def __init__(self):
        self.games: dict[str, GameState] = {}

    def create_game(self, game_id: str, creator_id: str) -> GameState:
        """创建房间，使用空剧本（等待LLM生成）"""
        placeholder_script = Script(
            title="待生成",
            genre="悬疑推理",
            difficulty="中等",
            estimated_time=90,
            background_story="",
            true_killer="",
            murder_method="",
            cover_up="",
            roles=[],  # LLM生成后填充
            clues=[],
            plot_outline=PlotOutline(act1="", act2="", act3=""),
        )
        state = GameState(
            game_id=game_id,
            phase="waiting",
            act=1,
            room_creator_id=creator_id,
            players={},
            script=placeholder_script,
            timer_start=datetime.now(),
        )
        self.games[game_id] = state
        return state

    def add_player(self, game_id: str, player_id: str, player_name: str) -> Optional[Player]:
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        # If script not yet generated (placeholder has no roles), allow joining without role
        if not state.script.roles:
            player = Player(id=player_id, name=player_name, role_id="", role=None)
            state.players[player_id] = player
            return player
        # Count all players to assign roles correctly
        if len(state.players) >= len(state.script.roles):
            return None  # 房间已满
        role = state.script.roles[len(state.players)]
        player = Player(
            id=player_id,
            name=player_name,
            role_id=role.id,
            role=role,
        )
        state.players[player_id] = player
        return player

    def set_script(self, game_id: str, script: Script):
        """设置剧本（LLM 生成后），重新分配角色给所有玩家"""
        if game_id in self.games:
            state = self.games[game_id]
            state.script = script
            role_idx = 0
            for pid, player in state.players.items():
                if role_idx < len(script.roles):
                    new_role = script.roles[role_idx]
                    player.role_id = new_role.id
                    player.role = new_role
                    role_idx += 1

    def start_game(self, game_id: str):
        if game_id in self.games:
            state = self.games[game_id]
            state.phase = "playing"
            state.act = 1
            state.timer_start = datetime.now()
            return len(state.players)

    def is_admin(self, game_id: str, player_id: str) -> bool:
        """检查是否为管理员"""
        if game_id not in self.games:
            return False
        return self.games[game_id].room_creator_id == player_id

    def kick_player(self, game_id: str, player_id_to_kick: str):
        """踢出玩家（仅管理员）"""
        if game_id in self.games:
            state = self.games[game_id]
            if player_id_to_kick in state.players:
                del state.players[player_id_to_kick]

    def force_trial(self, game_id: str):
        """强制进入审判阶段（仅管理员）"""
        if game_id in self.games:
            state = self.games[game_id]
            state.phase = "trial"
            state.act = 3

    def end_game(self, game_id: str):
        """提前结束游戏，揭晓真相（仅管理员）"""
        if game_id in self.games:
            state = self.games[game_id]
            state.phase = "revealed"
            state.act = 3

    def push_event(self, game_id: str, event_content: str):
        """DM推送事件到游戏（手动或自动）"""
        if game_id not in self.games:
            return
        state = self.games[game_id]
        msg = Message(
            from_player_id="__dm__",
            content=event_content,
            type="event",
        )
        state.public_messages.append(msg)
        state.host_message_history.append(event_content)

    def add_clue(self, game_id: str, clue_title: str, clue_content: str):
        """管理员追加自定义线索"""
        if game_id not in self.games:
            return
        clue = Clue(title=clue_title, content=clue_content, content_hint="")
        self.games[game_id].script.clues.append(clue)

    def add_dm_log(self, game_id: str, log_entry: str):
        """记录LLM推理日志"""
        if game_id in self.games:
            self.games[game_id].dm_log.append(log_entry)

    # --- Existing methods (unchanged) ---

    def add_message(self, game_id: str, message: Message):
        if game_id in self.games:
            state = self.games[game_id]
            if message.type in ("public", "system", "event"):
                state.public_messages.append(message)
            elif message.type == "private":
                state.private_messages.append(message)

    def add_chat_message(self, game_id: str, player_id: str, content: str, is_private: bool = False, target_player_id: Optional[str] = None):
        """快捷发送聊天消息（从 API 调用）"""
        if game_id not in self.games:
            return
        state = self.games[game_id]
        msg = Message(
            from_player_id=player_id,
            content=content,
            type="private" if is_private else "public",
            to_player_id=target_player_id,
        )
        self.add_message(game_id, msg)

    def add_accusation(self, game_id: str, accusation: Accusation):
        if game_id in self.games:
            self.games[game_id].accusations.append(accusation)

    def add_vote(self, game_id: str, vote: Vote):
        if game_id in self.games:
            self.games[game_id].votes.append(vote)

    def check_consensus(self, game_id: str) -> bool:
        """检查是否达成共识（≥50% 玩家指控同一人）"""
        if game_id not in self.games:
            return False
        state = self.games[game_id]
        if not state.votes:
            return False
        vote_counts: dict[str, int] = {}
        for vote in state.votes:
            vote_counts[vote.target_role_name] = vote_counts.get(vote.target_role_name, 0) + 1
        total_players = len(state.players)  # All players count (including admin)
        for count in vote_counts.values():
            if count >= total_players * 0.5:
                return True
        return False

    def get_state(self, game_id: str) -> Optional[GameState]:
        return self.games.get(game_id)

    def distribute_role_card(self, game_id: str, player_id: str, layer: str):
        """分发角色卡指定层级给玩家。
        layer: '1' = 角色名+简介, '2' = 背景/秘密任务/不在场证明, '3' = 人际关系/动机/个人线索
        """
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        player = state.players.get(player_id)
        if not player or not player.role:
            return None

        card_data = {}
        if layer == "1":
            card_data = {
                "name": player.role.name,
                "description": player.role.description,
            }
        elif layer == "2":
            card_data = {
                "name": player.role.name,
                "background": player.role.background,
                "secret_task": player.role.secret_task,
                "alibi": player.role.alibi,
            }
        elif layer == "3":
            card_data = {
                "relationships": player.role.relationships,
                "motive": player.role.motive,
            }
        return card_data

    def distribute_clue(self, game_id: str, clue_id: str, player_id: str):
        """分发线索给特定玩家。target_player_ids 使用角色名匹配。返回线索数据或 None。"""
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        clue = next((c for c in state.script.clues if c.id == clue_id), None)
        if not clue:
            return None
        # Match by role name (LLM outputs role names, not UUIDs)
        player = state.players.get(player_id)
        if player and player.role:
            if clue.target_player_ids and player.role.name not in clue.target_player_ids:
                return None
        return {
            "id": clue.id,
            "title": clue.title,
            "content": clue.content,
            "content_hint": clue.content_hint,
            "is_red_herring": clue.is_red_herring,
        }

    def execute_private_events(self, game_id: str, phase: str):
        """执行当前阶段的所有 DM 私信触发点。返回 [(player_id, content), ...]。"""
        if game_id not in self.games:
            return []
        state = self.games[game_id]
        events = [e for e in state.script.private_events if e.phase == phase]
        results = []
        for event in events:
            player_id = None
            for pid, player in state.players.items():
                if player.role and player.role.name == event.target_role_name:
                    player_id = pid
                    break
            if player_id:
                results.append((player_id, event.content))
        return results

    def cache_distribution(self, game_id: str, role_cards: dict, clues: dict, private_events: list):
        """Cache distributed data in GameState so it can be resent on WS (re)connect."""
        if game_id not in self.games:
            return
        state = self.games[game_id]

        # Cache role cards per player
        for pid, card_data in role_cards.items():
            if pid not in state.distributed_role_cards:
                state.distributed_role_cards[pid] = []
            # Determine layer from the data content
            layer = "2" if "background" in card_data else "3"
            state.distributed_role_cards[pid].append({
                "type": "role_card",
                "layer": layer,
                "player_id": pid,
                "data": card_data,
            })

        # Cache clues per player
        for pid, clue_list in clues.items():
            if pid not in state.distributed_clues:
                state.distributed_clues[pid] = []
            for clue_data in clue_list:
                state.distributed_clues[pid].append({
                    "type": "clue_unlock",
                    "player_id": pid,
                    "clue": clue_data,
                })

        # Cache DM private messages
        for pid, content in private_events:
            if pid not in state.distributed_dm_private:
                state.distributed_dm_private[pid] = []
            state.distributed_dm_private[pid].append({
                "type": "dm_private",
                "from": "__dm__",
                "to": pid,
                "content": content,
            })

    def get_pending_distributions(self, game_id: str, player_id: str) -> list:
        """Get all cached distribution messages for a player (for WS connect/resend)."""
        if game_id not in self.games:
            return []
        state = self.games[game_id]
        messages = []
        messages.extend(state.distributed_role_cards.get(player_id, []))
        messages.extend(state.distributed_clues.get(player_id, []))
        messages.extend(state.distributed_dm_private.get(player_id, []))
        return messages

    def unlock_phase(self, game_id: str, new_phase: str, new_act: int):
        """阶段解锁：切换阶段并执行该阶段的所有自动分发。
        new_phase is the act phase: "act1", "act2", "act3", etc.
        Returns {role_cards: {pid: layer_data}, clues: {pid: [clue_data]}, private_events: [(pid, content)]}
        """
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        # Phase stays "playing" — act1/act2 are acts within playing phase
        state.phase = "playing"
        state.act = new_act

        role_cards = {}
        clues = {}
        private_events = []

        # Layer map: act1 → layer 2, act2 → layer 3
        layer_map = {
            "act1": "2",
            "act2": "3",
        }
        # Build the act key from the act number
        act_key = f"act{new_act}"
        layer_to_unlock = layer_map.get(act_key)

        if layer_to_unlock:
            for pid, player in state.players.items():
                card_data = self.distribute_role_card(game_id, pid, layer_to_unlock)
                if card_data:
                    role_cards[pid] = card_data

        for clue in state.script.clues:
            if clue.unlock_phase == act_key:
                # Determine targets: if empty, distribute to all players (public clue)
                if clue.target_player_ids:
                    for pid, player in state.players.items():
                        if player.role and player.role.name in clue.target_player_ids:
                            clue_data = self.distribute_clue(game_id, clue.id, pid)
                            if clue_data:
                                clues.setdefault(pid, []).append(clue_data)
                else:
                    # Public clue — distribute to all players
                    for pid, player in state.players.items():
                        clue_data = self.distribute_clue(game_id, clue.id, pid)
                        if clue_data:
                            clues.setdefault(pid, []).append(clue_data)

        private_events = self.execute_private_events(game_id, act_key)

        # Cache the distributions for WS reconnect
        self.cache_distribution(game_id, role_cards, clues, private_events)

        return {
            "role_cards": role_cards,
            "clues": clues,
            "private_events": private_events,
        }


manager = GameManager()
