"""Player progression, divine resonance, backgrounds, and world interactions."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor
from typing import Any

from .items import DEFAULT_ITEMS, Inventory, InventoryError, Item
from .models import GameState

RESONANCE_KEYS = (
    "strength", "shadows", "knowledge", "war", "life", "death",
    "storms", "sea", "fate", "freedom", "creation", "forgotten",
)
STAT_TO_RESONANCE = {
    "strength": {"strength": 1.00, "war": 0.20},
    "agility": {"shadows": 0.75, "storms": 0.20},
    "endurance": {"life": 0.35, "strength": 0.25, "war": 0.15},
    "intelligence": {"knowledge": 0.80, "fate": 0.15},
    "willpower": {"life": 0.25, "death": 0.20, "storms": 0.20},
    "charisma": {"freedom": 0.45, "fate": 0.20, "life": 0.15},
    "luck": {"fate": 0.60, "sea": 0.10, "forgotten": 0.05},
}

GOD_ORDER = (
    "strength", "shadows", "knowledge", "war", "life", "death",
    "storms", "sea", "fate", "freedom", "creation", "forgotten",
)


@dataclass(frozen=True)
class Background:
    id: str
    name: str
    description: str
    starting_items: tuple[str, ...]
    starting_gold: int
    bonus_stats: dict[str, int]
    actions: tuple[str, ...]


BACKGROUNDS: dict[str, Background] = {
    "soldier": Background("soldier", "Soldier", "Trained to survive conflict and command under pressure.", ("rusted-knife", "traveler-coat"), 35, {"strength": 1, "endurance": 1}, ("command", "intimidate", "drill", "formation")),
    "thief": Background("thief", "Thief", "A survivor who learned to go where locks say no.", ("rusted-knife", "traveler-coat"), 45, {"agility": 2}, ("sneak", "pickpocket", "listen", "appraise")),
    "scholar": Background("scholar", "Scholar", "A researcher trained to find meaning in forgotten things.", ("traveler-coat", "old-photograph"), 25, {"intelligence": 2}, ("research", "translate", "identify", "teach")),
    "healer": Background("healer", "Healer", "A practical medic who learned to save lives with little.", ("traveler-coat", "health-potion"), 30, {"willpower": 1, "endurance": 1}, ("treat", "diagnose", "brew")),
    "merchant": Background("merchant", "Merchant", "A trader who knows what something is worth before the buyer does.", ("traveler-coat",), 90, {"charisma": 2}, ("haggle", "appraise", "negotiate", "trade")),
    "craftsperson": Background("craftsperson", "Craftsperson", "A maker comfortable turning raw material into useful things.", ("traveler-coat",), 40, {"intelligence": 1, "strength": 1}, ("forge", "repair", "salvage", "craft")),
    "wanderer": Background("wanderer", "Wanderer", "A traveler with no master and a talent for finding another road.", ("rusted-knife",), 20, {"luck": 1, "agility": 1}, ("scout", "forage", "navigate", "improvise")),
}


PROFESSION_ACTIONS = {
    "soldier": {"command", "intimidate", "drill", "formation"},
    "thief": {"sneak", "pickpocket", "listen", "appraise"},
    "scholar": {"research", "translate", "identify", "teach"},
    "healer": {"treat", "diagnose", "brew"},
    "merchant": {"haggle", "appraise", "negotiate", "trade"},
    "blacksmith": {"forge", "repair", "salvage", "craft"},
    "ranger": {"scout", "forage", "navigate", "track"},
}


FACILITIES = {
    "training_ground": ("Training Grounds", ("train_strength", "train_agility", "spar", "learn_combat")),
    "shop": ("General Shop", ("buy", "sell", "haggle", "appraise")),
    "blacksmith": ("Blacksmith", ("buy", "sell", "repair", "forge", "salvage")),
    "guild": ("Adventurer Guild", ("accept_contract", "collect_bounty", "rank_up")),
    "temple": ("Temple", ("heal", "pray", "learn_lore", "divine_listen")),
    "library": ("Library", ("research", "translate", "record_lore")),
    "tavern": ("Tavern", ("rumor", "rest", "drink", "meet")),
}


def xp_to_next_level(level: int) -> int:
    return max(100, 100 + (level - 1) * 35 + (level - 1) ** 2 * 10)


def derived_stats(state: GameState) -> dict[str, float]:
    p = state.player
    return {
        "attack": p.stats.get("strength", 5) * 2 + p.level,
        "defense": p.stats.get("endurance", 5) * 1.8 + p.level,
        "evasion": p.stats.get("agility", 5) * 1.5,
        "healing_power": p.stats.get("willpower", 5) * 1.5,
        "crit_chance": min(75.0, 5.0 + p.stats.get("luck", 5) * 0.75),
        "carry_capacity": 20.0 + p.stats.get("strength", 5) * 2 + p.stats.get("endurance", 5) * 1.5,
        "dialogue_bonus": p.stats.get("charisma", 5) * 0.8,
    }


def initialize_resonance(state: GameState) -> None:
    if not state.divine_resonance:
        state.divine_resonance = {key: 0.0 for key in RESONANCE_KEYS}


def stat_multiplier(state: GameState, resonance: str) -> float:
    base = 1.0
    p = state.player
    for stat, weights in STAT_TO_RESONANCE.items():
        weight = weights.get(resonance, 0.0)
        if weight:
            base += max(0, p.stats.get(stat, 0) - 5) * weight * 0.04
    return round(base, 3)


def add_resonance(state: GameState, resonance: str, base_amount: float, *, source: str = "action") -> float:
    initialize_resonance(state)
    if resonance not in state.divine_resonance:
        raise ValueError(f"Unknown resonance: {resonance}")
    amount = max(0.0, float(base_amount)) * stat_multiplier(state, resonance)
    state.divine_resonance[resonance] += amount
    if source:
        state.history.append(f"resonance:{resonance}:{amount:.2f}:{source}")
    return amount


def record_action(state: GameState, action: str, *, outcomes: dict[str, float] | None = None) -> dict[str, float]:
    """Record a behavioral action and award weighted divine resonance."""
    action = action.strip().lower()
    weights = outcomes or ACTION_RESONANCE.get(action, {})
    gains: dict[str, float] = {}
    for resonance, amount in weights.items():
        gains[resonance] = add_resonance(state, resonance, amount, source=action)
    state.action_history.append(action)
    return gains


ACTION_RESONANCE: dict[str, dict[str, float]] = {
    "heal": {"life": 3}, "save": {"life": 2, "freedom": 1}, "protect": {"life": 2, "strength": 1},
    "kill": {"death": 1, "war": 1}, "unnecessary_kill": {"death": 2, "forgotten": 3},
    "intimidate": {"war": 2, "strength": 1}, "command": {"war": 2, "freedom": 1},
    "sneak": {"shadows": 3}, "pickpocket": {"shadows": 2, "forgotten": 1}, "listen": {"shadows": 1, "knowledge": 2},
    "research": {"knowledge": 3}, "translate": {"knowledge": 2, "fate": 1}, "identify": {"knowledge": 2},
    "haggle": {"freedom": 1, "fate": 1}, "negotiate": {"freedom": 2}, "trade": {"creation": 1, "freedom": 1},
    "forge": {"creation": 3, "strength": 1}, "repair": {"creation": 2, "life": 1}, "salvage": {"creation": 1, "knowledge": 1},
    "build": {"creation": 3}, "explore": {"sea": 1, "fate": 1}, "scout": {"shadows": 1, "knowledge": 1},
    "pray": {"life": 1, "fate": 2}, "pray_for_power": {"strength": 1, "war": 1},
    "destroy": {"war": 1, "forgotten": 2}, "betray": {"forgotten": 3}, "abandon": {"forgotten": 2},
    "mercy": {"life": 2, "freedom": 1}, "risk": {"fate": 2}, "storm": {"storms": 3},
}


def predicted_god(state: GameState) -> tuple[str, float]:
    initialize_resonance(state)
    values = dict(state.divine_resonance)
    total = sum(values.values()) or 1.0
    winner = max(GOD_ORDER, key=lambda key: values.get(key, 0.0))
    confidence = values.get(winner, 0.0) / total
    return winner, confidence


def refresh_divine_prediction(state: GameState) -> tuple[str, float]:
    god, confidence = predicted_god(state)
    state.divine_prediction = god if confidence >= 0.20 else "undetermined"
    return god, confidence


def grant_xp(state: GameState, amount: int) -> int:
    if amount < 0:
        raise ValueError("XP amount cannot be negative")
    state.xp += amount
    gained = 0
    while state.xp >= xp_to_next_level(state.level):
        state.xp -= xp_to_next_level(state.level)
        state.level += 1
        state.stat_points += 3
        state.skill_points += 1
        state.max_hp += 10
        state.hp = state.max_hp
        gained += 1
    return gained


def spend_stat_point(state: GameState, stat: str) -> None:
    if state.stat_points <= 0:
        raise ValueError("No stat points available")
    stat = stat.strip().lower()
    if stat not in state.stats:
        raise ValueError(f"Unknown stat: {stat}")
    state.stats[stat] += 1
    state.stat_points -= 1


def set_background(state: GameState, background_id: str) -> Background:
    if state.background_id:
        raise ValueError("Background is already set")
    try:
        background = BACKGROUNDS[background_id]
    except KeyError as exc:
        raise ValueError(f"Unknown background: {background_id}") from exc
    state.background_id = background.id
    state.profession = background.id
    state.gold += background.starting_gold
    for stat, amount in background.bonus_stats.items():
        state.stats[stat] = state.stats.get(stat, 5) + amount
    for item_id in background.starting_items:
        if item_id not in state.inventory:
            state.inventory.append(item_id)
    return background


def change_profession(state: GameState, profession: str) -> None:
    profession = profession.strip().lower()
    if profession not in PROFESSION_ACTIONS:
        raise ValueError(f"Unknown profession: {profession}")
    state.profession = profession


def can_use_action(state: GameState, action: str) -> bool:
    action = action.strip().lower()
    background = BACKGROUNDS.get(state.background_id)
    if background and action in background.actions:
        return True
    return action in PROFESSION_ACTIONS.get(state.profession, set())


def spend_gold(state: GameState, amount: int) -> None:
    if amount < 0 or state.gold < amount:
        raise ValueError("Not enough gold")
    state.gold -= amount


def add_gold(state: GameState, amount: int) -> None:
    if amount < 0:
        raise ValueError("Gold amount cannot be negative")
    state.gold += amount


def buy_item(state: GameState, item_id: str, quantity: int = 1, *, discount: float = 0.0) -> int:
    item = DEFAULT_ITEMS[item_id]
    price = max(1, floor(item.value * quantity * max(0.0, 1.0 - discount)))
    spend_gold(state, price)
    inv = Inventory.from_dict([{"item_id": i, "quantity": 1} for i in state.inventory])
    inv.add(item, quantity)
    state.inventory = [entry.item_id for entry in inv.entries for _ in range(entry.quantity)]
    return price


def sell_item(state: GameState, item_id: str, quantity: int = 1, *, multiplier: float = 1.0) -> int:
    item = DEFAULT_ITEMS[item_id]
    if state.inventory.count(item_id) < quantity:
        raise ValueError(f"Not enough {item.name}")
    for _ in range(quantity):
        state.inventory.remove(item_id)
    payout = max(1, floor(item.value * quantity * 0.5 * multiplier))
    add_gold(state, payout)
    return payout


def train(state: GameState, stat: str, *, cost: int = 10, xp: int = 20) -> int:
    if not can_use_action(state, "drill") and not can_use_action(state, "train"):
        raise ValueError("This character has no training technique here")
    spend_gold(state, cost)
    add_resonance(state, stat if stat in RESONANCE_KEYS else "strength", 1.0, source="training")
    return grant_xp(state, xp)


def forge_item(state: GameState, output_id: str, *, material_ids: list[str], gold_cost: int = 10) -> None:
    if not can_use_action(state, "forge"):
        raise ValueError("You don't know how to forge")
    for material_id in material_ids:
        if state.inventory.count(material_id) < 1:
            raise ValueError(f"Missing material: {material_id}")
    for material_id in material_ids:
        state.inventory.remove(material_id)
    spend_gold(state, gold_cost)
    if output_id not in DEFAULT_ITEMS:
        raise ValueError(f"Unknown crafted item: {output_id}")
    state.inventory.append(output_id)
    record_action(state, "forge")


def repair_item(state: GameState, item_id: str, *, gold_cost: int = 8) -> None:
    if not can_use_action(state, "repair"):
        raise ValueError("You don't know how to repair equipment")
    if item_id not in state.inventory and item_id not in state.equipment.values():
        raise ValueError("Item is not owned")
    spend_gold(state, gold_cost)
    record_action(state, "repair")


def interaction_choices(state: GameState, context: str) -> list[str]:
    """Return additional world verbs available to this character."""
    common = ["talk", "inspect", "leave"]
    specialized = []
    for action in sorted(set(PROFESSION_ACTIONS.get(state.profession, set())) | set(BACKGROUNDS.get(state.background_id, Background("", "", "", (), 0, {}, ())).actions)):
        specialized.append(action)
    context_map = {
        "guard": ["intimidate", "command", "negotiate", "sneak"],
        "blacksmith": ["buy", "sell", "repair", "forge", "salvage"],
        "shop": ["buy", "sell", "haggle", "appraise"],
        "library": ["research", "translate", "identify"],
        "wounded": ["treat", "diagnose", "pray"],
    }
    for action in context_map.get(context, []):
        if action in specialized or action in {"negotiate", "pray"}:
            specialized.append(action)
    return list(dict.fromkeys(common + specialized))
