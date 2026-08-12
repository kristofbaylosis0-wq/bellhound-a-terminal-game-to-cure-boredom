"""Player creation and progression operations."""

from __future__ import annotations

from .inventory_service import add_item, equip_item
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
    """Create a fresh game with a validated player name and starter gear."""
    name = player_name.strip()
    if not name:
        raise ValueError("Player name cannot be empty")
    if len(name) > 32:
        raise ValueError("Player name cannot exceed 32 characters")

    player = Player(name=name, stats=dict(DEFAULT_SEED_STATS))
    state = GameState(player=player, random_seed=random_seed)
    add_item(state, "rusted-knife")
    add_item(state, "traveler-coat")
    add_item(state, "health-potion", 3)
    equip_item(state, "rusted-knife", "weapon")
    equip_item(state, "traveler-coat", "armor")
    return state


def grant_xp(state: GameState, amount: int) -> int:
    return state.player.add_xp(amount)


def spend_stat_point(state: GameState, stat: str) -> None:
    state.player.spend_stat_point(stat.lower().strip())
