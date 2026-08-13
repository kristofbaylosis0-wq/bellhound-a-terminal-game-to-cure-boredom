"""Player creation and progression operations."""

from __future__ import annotations

from .inventory_service import add_item, equip_item
from .items import DEFAULT_ITEMS
from .models import GameState, Player, STORY_MODES
from .progression import BACKGROUNDS, refresh_prediction

DEFAULT_SEED_STATS = {
    "strength": 5,
    "agility": 5,
    "endurance": 5,
    "intelligence": 5,
    "willpower": 5,
    "charisma": 5,
    "luck": 5,
}


def create_new_game(
    player_name: str,
    *,
    random_seed: int | None = None,
    background_id: str | None = None,
    story_mode: str = "handcrafted",
) -> GameState:
    """Create a fresh game with starter gear, background, and story mode."""
    name = player_name.strip()
    if not name:
        raise ValueError("Player name cannot be empty")
    if len(name) > 32:
        raise ValueError("Player name cannot exceed 32 characters")
    if story_mode not in STORY_MODES:
        raise ValueError(f"Unknown story mode: {story_mode}")

    player = Player(name=name, stats=dict(DEFAULT_SEED_STATS))
    state = GameState(player=player, random_seed=random_seed, story_mode=story_mode)
    add_item(state, "rusted-knife")
    add_item(state, "traveler-coat")
    add_item(state, "health-potion", 3)
    equip_item(state, "rusted-knife", "weapon")
    equip_item(state, "traveler-coat", "armor")

    if background_id:
        if background_id not in BACKGROUNDS:
            raise ValueError(f"Unknown background: {background_id}")
        background = BACKGROUNDS[background_id]
        player.background_id = background.id
        player.profession = background.id
        player.gold += background.starting_gold
        for stat, amount in background.bonus_stats.items():
            player.stats[stat] += amount
        for item_id in background.starting_items:
            item = DEFAULT_ITEMS[item_id]
            if not item.stackable and item_id in player.inventory:
                continue
            add_item(state, item_id)

    refresh_prediction(state)
    return state


def grant_xp(state: GameState, amount: int) -> int:
    gained = state.player.add_xp(amount)
    refresh_prediction(state)
    return gained


def spend_stat_point(state: GameState, stat: str) -> None:
    state.player.spend_stat_point(stat.lower().strip())
