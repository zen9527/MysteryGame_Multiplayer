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
        # DM (room creator) does not get a role — they are the host
        if player_id == state.room_creator_id:
            player = Player(id=player_id, name=player_name, role_id="", role=None)
            state.players[player_id] = player
            return player
        # Count playable players (exclude DM) to assign roles correctly
        playable_count = sum(1 for pid, p in state.players.items() if pid != state.room_creator_id)
        if playable_count >= len(state.script.roles):
            return None  # 房间已满
        role = state.script.roles[playable_count] if state.script.roles else None
        player = Player(
            id=player_id,
            name=player_name,
            role_id=role.id if role else "",
            role=role,
        )
        state.players[player_id] = player
        return player

    def set_script(self, game_id: str, script: Script):
        """设置剧本（LLM 生成后）"""
        if game_id in self.games:
            state = self.games[game_id]
            state.script = script
            # Reassign roles to playable players (skip DM)
            role_idx = 0
            for pid, player in state.players.items():
                if pid == state.room_creator_id:
                    player.role_id = ""
                    player.role = None
                    continue
                if role_idx < len(script.roles):
                    new_role = script.roles[role_idx]
                    player.role_id = new_role.id
                    player.role = new_role
                    role_idx += 1

    def start_game(self, game_id: str):
        if game_id in self.games:
            state = self.games[game_id]
            # Count playable players (exclude DM)
            playable_count = sum(1 for pid in state.players if pid != state.room_creator_id)
            state.phase = "playing"
            state.act = 1
            state.timer_start = datetime.now()
            return playable_count

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
        total_players = len(state.players)
        for count in vote_counts.values():
            if count >= total_players * 0.5:
                return True
        return False

    def get_state(self, game_id: str) -> Optional[GameState]:
        return self.games.get(game_id)


manager = GameManager()
