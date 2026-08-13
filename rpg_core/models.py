"""Authoritative game-state models.

The save format is JSON-friendly and intentionally contains only game state,
not runtime objects or API credentials.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SAVE_VERSION = 4
START_LOCATION = "ashen-capital-gate"
DIVINE_DOMAINS = (
    "strength", "shadows", "knowledge", "war", "life", "death",
    "storms", "sea", "fate", "freedom", "creation", "forgotten",
)
DEFAULT_STATS = {
    "strength": 5, "agility": 5, "endurance": 5,
    "intelligence": 5, "willpower": 5, "charisma": 5, "luck": 5,
}


def default_divine_affinity() -> dict[str, float]:
    return {domain: 0.0 for domain in DIVINE_DOMAINS}


@dataclass
class Player:
    name: str
    level: int = 1
    xp: int = 0
    hp: int = 100
    max_hp: int = 100
    stat_points: int = 0
    skill_points: int = 0
    gold: int = 25
    stats: dict[str, int] = field(default_factory=lambda: dict(DEFAULT_STATS))
    skills: dict[str, int] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    equipment: dict[str, str | None] = field(default_factory=lambda: {
        "weapon": None, "armor": None, "accessory": None,
    })
    background_id: str = ""
    profession: str = "wanderer"
    divine_prediction: str = "undetermined"
    action_history: list[str] = field(default_factory=list)
    discovered_abilities: list[str] = field(default_factory=list)

    def xp_to_next_level(self) -> int:
        return max(100, 100 + (self.level - 1) * 35 + (self.level - 1) ** 2 * 10)

    def add_xp(self, amount: int) -> int:
        if amount < 0:
            raise ValueError("XP amount cannot be negative")
        self.xp += amount
        gained = 0
        while self.xp >= self.xp_to_next_level():
            self.xp -= self.xp_to_next_level()
            self.level += 1
            self.stat_points += 3
            self.skill_points += 1
            self.max_hp += 10
            self.hp = self.max_hp
            gained += 1
        return gained

    def spend_stat_point(self, stat: str) -> None:
        if self.stat_points <= 0:
            raise ValueError("No stat points available")
        stat = stat.strip().lower()
        if stat not in self.stats:
            raise ValueError(f"Unknown stat: {stat}")
        self.stats[stat] += 1
        self.stat_points -= 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        normalized = dict(data)
        normalized.setdefault("gold", 25)
        normalized.setdefault("stats", dict(DEFAULT_STATS))
        normalized.setdefault("skills", {})
        normalized.setdefault("inventory", [])
        normalized.setdefault("equipment", {"weapon": None, "armor": None, "accessory": None})
        normalized.setdefault("background_id", "")
        normalized.setdefault("profession", "wanderer")
        normalized.setdefault("divine_prediction", "undetermined")
        normalized.setdefault("action_history", [])
        normalized.setdefault("discovered_abilities", [])
        return cls(**normalized)


@dataclass
class GameState:
    player: Player
    location: str = START_LOCATION
    chapter: int = 1
    current_story_node: str = "ch1_arrival"
    checkpoint_node: str = "ch1_arrival"
    world_flags: dict[str, Any] = field(default_factory=dict)
    quest_states: dict[str, str] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    faction_reputation: dict[str, int] = field(default_factory=dict)
    divine_affinity: dict[str, float] = field(default_factory=default_divine_affinity)
    discovered_lore: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    random_seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "save_version": SAVE_VERSION,
            "player": self.player.to_dict(),
            "location": self.location,
            "chapter": self.chapter,
            "current_story_node": self.current_story_node,
            "checkpoint_node": self.checkpoint_node,
            "world_flags": self.world_flags,
            "quest_states": self.quest_states,
            "relationships": self.relationships,
            "faction_reputation": self.faction_reputation,
            "divine_affinity": self.divine_affinity,
            "discovered_lore": self.discovered_lore,
            "history": self.history,
            "achievements": self.achievements,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        version = int(data.get("save_version", 0))
        if version not in {1, 2, 3, SAVE_VERSION}:
            raise ValueError(f"Unsupported save version: {version}")
        divine = default_divine_affinity()
        for key, value in data.get("divine_affinity", {}).items():
            if key in divine:
                divine[key] = float(value)
        return cls(
            player=Player.from_dict(data["player"]),
            location=data.get("location", START_LOCATION),
            chapter=int(data.get("chapter", 1)),
            current_story_node=str(data.get("current_story_node", "ch1_arrival")),
            checkpoint_node=str(data.get("checkpoint_node", data.get("current_story_node", "ch1_arrival"))),
            world_flags=dict(data.get("world_flags", {})),
            quest_states=dict(data.get("quest_states", {})),
            relationships={k: int(v) for k, v in data.get("relationships", {}).items()},
            faction_reputation={k: int(v) for k, v in data.get("faction_reputation", {}).items()},
            divine_affinity=divine,
            discovered_lore=list(data.get("discovered_lore", [])),
            history=list(data.get("history", [])),
            achievements=list(data.get("achievements", [])),
            random_seed=data.get("random_seed"),
        )
