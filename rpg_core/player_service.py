"""Player creation and progression operations."""

from __future__ import annotations

from .models import GameState, Player

DEFAULT_SEED_STATS = {
    "strength": 5,
    "agility": 5,
    "endurance": 5,
    "intelligence": 5,
    "willpower": 5,
    "charisma": 5,
    "luck": 5,
}


def create_new_game(player_name: str, *, random_seed: int | None = None) -> GameState:
    """Create a fresh game with a validated player name."""
    name = player_name.strip()
    if not name:
        raise ValueError("Player name cannot be empty")
    if len(name) > 32:
        raise ValueError("Player name cannot exceed 32 characters")

    player = Player(name=name, stats=dict(DEFAULT_SEED_STATS))
    return GameState(player=player, random_seed=random_seed)


def grant_xp(state: GameState, amount: int) -> int:
    """Award XP and return the number of levels gained."""
    return state.player.add_xp(amount)


def spend_stat_point(state: GameState, stat: str) -> None:
    """Spend one available stat point on the requested stat."""
    state.player.spend_stat_point(stat.lower().strip())
