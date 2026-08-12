"""Authoritative game-state models.

The save format is JSON-friendly and intentionally contains only game state,
not runtime objects or API credentials.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

SAVE_VERSION = 1
BASE_XP_TO_LEVEL = 100
START_LOCATION = "ashen-capital-gate"


@dataclass
class Player:
    name: str
    level: int = 1
    xp: int = 0
    hp: int = 100
    max_hp: int = 100
    stat_points: int = 0
    skill_points: int = 0
    stats: dict[str, int] = field(
        default_factory=lambda: {
            "strength": 5,
            "agility": 5,
            "endurance": 5,
            "intelligence": 5,
            "willpower": 5,
            "charisma": 5,
            "luck": 5,
        }
    )
    skills: dict[str, int] = field(default_factory=dict)
    inventory: list[str] = field(default_factory=list)
    equipment: dict[str, str | None] = field(
        default_factory=lambda: {
            "weapon": None,
            "armor": None,
            "accessory": None,
        }
    )

    def xp_to_next_level(self) -> int:
        """Return XP required from the current level to the next level."""
        return BASE_XP_TO_LEVEL * self.level

    def add_xp(self, amount: int) -> int:
        """Add XP, process every earned level, and return levels gained."""
        if amount < 0:
            raise ValueError("XP amount cannot be negative")

        self.xp += amount
        gained = 0
        while self.xp >= self.xp_to_next_level():
            self.xp -= self.xp_to_next_level()
            self.level += 1
            self.stat_points += 2
            self.skill_points += 1
            self.max_hp += 10
            self.hp = self.max_hp
            gained += 1
        return gained

    def spend_stat_point(self, stat: str) -> None:
        """Increase one known stat by one point."""
        if self.stat_points <= 0:
            raise ValueError("No stat points available")
        if stat not in self.stats:
            raise ValueError(f"Unknown stat: {stat}")
        self.stats[stat] += 1
        self.stat_points -= 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Player":
        return cls(**data)


@dataclass
class GameState:
    player: Player
    location: str = START_LOCATION
    chapter: int = 1
    world_flags: dict[str, Any] = field(default_factory=dict)
    quest_states: dict[str, str] = field(default_factory=dict)
    relationships: dict[str, int] = field(default_factory=dict)
    faction_reputation: dict[str, int] = field(default_factory=dict)
    discovered_lore: list[str] = field(default_factory=list)
    history: list[str] = field(default_factory=list)
    random_seed: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "save_version": SAVE_VERSION,
            "player": self.player.to_dict(),
            "location": self.location,
            "chapter": self.chapter,
            "world_flags": self.world_flags,
            "quest_states": self.quest_states,
            "relationships": self.relationships,
            "faction_reputation": self.faction_reputation,
            "discovered_lore": self.discovered_lore,
            "history": self.history,
            "random_seed": self.random_seed,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        version = int(data.get("save_version", 0))
        if version != SAVE_VERSION:
            raise ValueError(f"Unsupported save version: {version}")
        return cls(
            player=Player.from_dict(data["player"]),
            location=data.get("location", START_LOCATION),
            chapter=int(data.get("chapter", 1)),
            world_flags=dict(data.get("world_flags", {})),
            quest_states=dict(data.get("quest_states", {})),
            relationships={k: int(v) for k, v in data.get("relationships", {}).items()},
            faction_reputation={k: int(v) for k, v in data.get("faction_reputation", {}).items()},
            discovered_lore=list(data.get("discovered_lore", [])),
            history=list(data.get("history", [])),
            random_seed=data.get("random_seed"),
        )
