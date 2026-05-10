from server.models import Player


def resolve_display_name(player: Player, include_player_name: bool = True) -> str:
    """Resolve player's display name as '角色名 (玩家名)' format.

    Args:
        player: The Player object to resolve
        include_player_name: Whether to append player name in parentheses

    Returns:
        Display name in format '角色名 (玩家名)' or just '角色名' if include_player_name is False.
        Returns player name only if role is not set.
    """
    if player.role and player.role.name:
        if include_player_name and player.name:
            return f"{player.role.name}({player.name})"
        return player.role.name
    return player.name


def resolve_display_name_for_message(state, player_id: str) -> str:
    """Resolve display name for message sender: '角色名 (玩家名)' or '🎭 DM' for DM messages.

    This is the function used by WebSocketHub and API routes for resolving message sender names.

    Args:
        state: The GameState object containing players
        player_id: The player ID to resolve (can be "__dm__" for DM messages)

    Returns:
        Display name in format '角色名 (玩家名)' or '🎭 DM' for DM messages.
    """
    if player_id == "__dm__":
        return "🎭 DM"
    if state and player_id in state.players:
        player = state.players[player_id]
        return resolve_display_name(player, include_player_name=True)
    return player_id
