from server.models import GameState, Player, Script, Message, Accusation, Vote
from datetime import datetime, timedelta
from typing import Optional

class GameManager:
    def __init__(self):
        self.games: dict[str, GameState] = {}

    def create_game(self, game_id: str, script: Script) -> GameState:
        state = GameState(
            game_id=game_id,
            phase="waiting",
            players={},
            script=script,
            timer_start=datetime.now(),
        )
        self.games[game_id] = state
        return state

    def add_player(self, game_id: str, player_id: str, player_name: str) -> Optional[Player]:
        if game_id not in self.games:
            return None
        state = self.games[game_id]
        if len(state.players) >= len(state.script.roles):
            return None  # 房间已满
        role = state.script.roles[len(state.players)]
        player = Player(id=player_id, name=player_name, role_id=role.id)
        state.players[player_id] = player
        return player

    def start_game(self, game_id: str):
        if game_id in self.games:
            self.games[game_id].phase = "playing"

    def add_message(self, game_id: str, message: Message):
        if game_id in self.games:
            state = self.games[game_id]
            if message.type in ("public", "system", "event"):
                state.public_messages.append(message)
            elif message.type == "private":
                state.private_messages.append(message)

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
