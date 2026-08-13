"""Player progression, divine resonance, backgrounds, professions, and interactions."""

from __future__ import annotations

from dataclasses import dataclass
from math import floor

from .items import DEFAULT_ITEMS, Inventory
from .models import DIVINE_DOMAINS, GameState

STAT_TO_RESONANCE = {
    "strength": {"strength": 1.0, "war": 0.20},
    "agility": {"shadows": 0.75, "storms": 0.20},
    "endurance": {"life": 0.35, "strength": 0.25, "war": 0.15},
    "intelligence": {"knowledge": 0.80, "fate": 0.15},
    "willpower": {"life": 0.25, "death": 0.20, "storms": 0.20},
    "charisma": {"freedom": 0.45, "fate": 0.20, "life": 0.15},
    "luck": {"fate": 0.60, "sea": 0.10, "forgotten": 0.05},
}


@dataclass(frozen=True)
class Background:
    id: str
    name: str
    description: str
    starting_items: tuple[str, ...]
    starting_gold: int
    bonus_stats: dict[str, int]
    actions: tuple[str, ...]


BACKGROUNDS = {
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

ACTION_RESONANCE = {
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


def xp_to_next_level(level: int) -> int:
    return max(100, 100 + (level - 1) * 35 + (level - 1) ** 2 * 10)


def derived_stats(state: GameState) -> dict[str, float]:
    p = state.player
    return {
        "attack": p.stats["strength"] * 2 + p.level,
        "defense": p.stats["endurance"] * 1.8 + p.level,
        "evasion": p.stats["agility"] * 1.5,
        "healing_power": p.stats["willpower"] * 1.5,
        "crit_chance": min(75.0, 5.0 + p.stats["luck"] * 0.75),
        "carry_capacity": 20.0 + p.stats["strength"] * 2 + p.stats["endurance"] * 1.5,
        "dialogue_bonus": p.stats["charisma"] * 0.8,
    }


def stat_multiplier(state: GameState, resonance: str) -> float:
    multiplier = 1.0
    for stat, weights in STAT_TO_RESONANCE.items():
        multiplier += max(0, state.player.stats.get(stat, 5) - 5) * weights.get(resonance, 0.0) * 0.04
    return round(multiplier, 3)


def add_resonance(state: GameState, resonance: str, base_amount: float, *, source: str = "action") -> float:
    if resonance not in DIVINE_DOMAINS:
        raise ValueError(f"Unknown divine resonance: {resonance}")
    amount = max(0.0, float(base_amount)) * stat_multiplier(state, resonance)
    state.divine_affinity[resonance] = state.divine_affinity.get(resonance, 0.0) + amount
    if source:
        state.history.append(f"resonance:{resonance}:{amount:.2f}:{source}")
    return amount


def refresh_prediction(state: GameState) -> tuple[str, float]:
    total = sum(state.divine_affinity.values()) or 1.0
    winner = max(DIVINE_DOMAINS, key=lambda key: state.divine_affinity.get(key, 0.0))
    confidence = state.divine_affinity.get(winner, 0.0) / total
    state.player.divine_prediction = winner if confidence >= 0.20 else "undetermined"
    return winner, confidence


def record_action(state: GameState, action: str, *, outcomes: dict[str, float] | None = None) -> dict[str, float]:
    action = action.strip().lower()
    gains = {domain: add_resonance(state, domain, amount, source=action) for domain, amount in (outcomes or ACTION_RESONANCE.get(action, {})).items()}
    state.player.action_history.append(action)
    refresh_prediction(state)
    return gains


def grant_xp(state: GameState, amount: int) -> int:
    if amount < 0:
        raise ValueError("XP amount cannot be negative")
    return state.player.add_xp(amount)


def spend_stat_point(state: GameState, stat: str) -> None:
    state.player.spend_stat_point(stat)


def set_background(state: GameState, background_id: str) -> Background:
    if state.player.background_id:
        raise ValueError("Background is already set")
    background = BACKGROUNDS[background_id]
    state.player.background_id = background.id
    state.player.profession = background.id
    state.player.gold += background.starting_gold
    for stat, amount in background.bonus_stats.items():
        state.player.stats[stat] += amount
    for item_id in background.starting_items:
        state.player.inventory.append(item_id)
    return background


def change_profession(state: GameState, profession: str) -> None:
    profession = profession.strip().lower()
    if profession not in PROFESSION_ACTIONS:
        raise ValueError(f"Unknown profession: {profession}")
    state.player.profession = profession


def can_use_action(state: GameState, action: str) -> bool:
    action = action.strip().lower()
    background = BACKGROUNDS.get(state.player.background_id)
    return bool((background and action in background.actions) or action in PROFESSION_ACTIONS.get(state.player.profession, set()))


def add_gold(state: GameState, amount: int) -> None:
    if amount < 0:
        raise ValueError("Gold amount cannot be negative")
    state.player.gold += amount


def spend_gold(state: GameState, amount: int) -> None:
    if amount < 0 or state.player.gold < amount:
        raise ValueError("Not enough gold")
    state.player.gold -= amount


def _inventory(state: GameState) -> Inventory:
    return Inventory.from_dict([{"item_id": item_id, "quantity": state.player.inventory.count(item_id)} for item_id in dict.fromkeys(state.player.inventory)])


def _sync_inventory(state: GameState, inventory: Inventory) -> None:
    state.player.inventory = [entry.item_id for entry in inventory.entries for _ in range(entry.quantity)]


def buy_item(state: GameState, item_id: str, quantity: int = 1, *, discount: float = 0.0) -> int:
    item = DEFAULT_ITEMS[item_id]
    merchant_bonus = 0.10 if state.player.profession == "merchant" else 0.0
    effective_discount = min(0.80, max(0.0, discount + merchant_bonus))
    price = max(1, floor(item.value * quantity * (1.0 - effective_discount)))
    spend_gold(state, price)
    inv = _inventory(state)
    inv.add(item, quantity)
    _sync_inventory(state, inv)
    record_action(state, "trade")
    return price


def sell_item(state: GameState, item_id: str, quantity: int = 1, *, multiplier: float = 1.0) -> int:
    item = DEFAULT_ITEMS[item_id]
    if state.player.inventory.count(item_id) < quantity:
        raise ValueError(f"Not enough {item.name}")
    for _ in range(quantity):
        state.player.inventory.remove(item_id)
    merchant_bonus = 0.10 if state.player.profession == "merchant" else 0.0
    payout = max(1, floor(item.value * quantity * (0.50 + merchant_bonus) * multiplier))
    add_gold(state, payout)
    record_action(state, "trade")
    return payout


def train(state: GameState, stat: str, *, cost: int = 10, xp: int = 20) -> int:
    if state.player.profession not in {"soldier", "ranger"} and not can_use_action(state, "drill"):
        raise ValueError("This character has no training technique")
    stat = stat.strip().lower()
    if stat not in state.player.stats:
        raise ValueError(f"Unknown stat: {stat}")
    spend_gold(state, cost)
    resonance = stat if stat in DIVINE_DOMAINS else "strength"
    add_resonance(state, resonance, 1.0, source="training")
    return grant_xp(state, xp)


def forge_item(state: GameState, output_id: str, *, material_ids: list[str], gold_cost: int = 10) -> None:
    if not can_use_action(state, "forge"):
        raise ValueError("You don't know how to forge")
    if output_id not in DEFAULT_ITEMS:
        raise ValueError(f"Unknown crafted item: {output_id}")
    for material_id in material_ids:
        if state.player.inventory.count(material_id) < 1:
            raise ValueError(f"Missing material: {material_id}")
    for material_id in material_ids:
        state.player.inventory.remove(material_id)
    spend_gold(state, gold_cost)
    state.player.inventory.append(output_id)
    record_action(state, "forge")


def repair_item(state: GameState, item_id: str, *, gold_cost: int = 8) -> None:
    if not can_use_action(state, "repair"):
        raise ValueError("You don't know how to repair equipment")
    if item_id not in state.player.inventory and item_id not in state.player.equipment.values():
        raise ValueError("Item is not owned")
    spend_gold(state, gold_cost)
    record_action(state, "repair")


def heal_player(state: GameState, amount: int | None = None) -> int:
    amount = amount or int(10 + derived_stats(state)["healing_power"])
    before = state.player.hp
    state.player.hp = min(state.player.max_hp, state.player.hp + max(0, amount))
    restored = state.player.hp - before
    record_action(state, "heal")
    return restored


def interaction_choices(state: GameState, context: str) -> list[str]:
    context_actions = {
        "guard": ["intimidate", "command", "negotiate", "sneak"],
        "blacksmith": ["buy", "sell", "repair", "forge", "salvage"],
        "shop": ["buy", "sell", "haggle", "appraise"],
        "library": ["research", "translate", "identify"],
        "wounded": ["treat", "diagnose", "pray"],
    }
    available = set(PROFESSION_ACTIONS.get(state.player.profession, set()))
    background = BACKGROUNDS.get(state.player.background_id)
    if background:
        available.update(background.actions)
    return list(dict.fromkeys(["talk", "inspect", "leave"] + [a for a in context_actions.get(context, []) if a in available or a in {"negotiate", "pray"}]))
