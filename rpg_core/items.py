"""Authoritative item and inventory models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class Item:
    id: str
    name: str
    item_type: str
    description: str = ""
    rarity: str = "common"
    stackable: bool = True
    max_stack: int = 99
    weight: float = 0.0
    value: int = 0
    stats: dict[str, int] = field(default_factory=dict)
    effects: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class InventoryEntry:
    item_id: str
    quantity: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_ITEMS: dict[str, Item] = {
    "rusted-knife": Item(
        id="rusted-knife", name="Rusted Knife", item_type="weapon",
        description="A badly worn knife that has seen better days.", rarity="common",
        stackable=False, weight=0.8, value=4, stats={"attack": 3}, tags=["weapon", "starter"],
    ),
    "traveler-coat": Item(
        id="traveler-coat", name="Traveler's Coat", item_type="armor",
        description="A practical coat made for long roads and bad weather.", rarity="common",
        stackable=False, weight=2.0, value=12, stats={"defense": 4, "max_hp": 5}, tags=["armor", "starter"],
    ),
    "health-potion": Item(
        id="health-potion", name="Health Potion", item_type="consumable",
        description="Restores 30 HP.", rarity="common", stackable=True, max_stack=20,
        weight=0.2, value=10, effects=[{"type": "heal", "amount": 30}], tags=["consumable", "healing"],
    ),
    "old-photograph": Item(
        id="old-photograph", name="Old Photograph", item_type="quest",
        description="A faded photograph with a person carefully scratched out.", rarity="uncommon",
        stackable=False, weight=0.0, value=0, tags=["quest", "lore"],
    ),
    "black-iron-key": Item(
        id="black-iron-key", name="Black Iron Key", item_type="quest",
        description="A cold iron key stamped with a bell surrounded by twelve circles.", rarity="rare",
        stackable=False, weight=0.3, value=0, tags=["quest", "bellkeeper", "lore"],
    ),
    "bellkeeper-page": Item(
        id="bellkeeper-page", name="Bellkeeper Record Page", item_type="quest",
        description="A torn record describing a bell that must never be allowed to fail.", rarity="uncommon",
        stackable=True, max_stack=5, weight=0.0, value=0, tags=["quest", "lore", "bellkeeper"],
    ),
    "echo-shard": Item(
        id="echo-shard", name="Echo Shard", item_type="quest",
        description="A splinter of memory-glass left behind by the creature beneath the bell.", rarity="rare",
        stackable=False, weight=0.1, value=0, tags=["quest", "lore", "resonance"],
    ),
    "bellkeeper-seal": Item(
        id="bellkeeper-seal", name="Bellkeeper Seal", item_type="quest",
        description="A brass seal that grants limited passage through Bellkeeper territory.", rarity="uncommon",
        stackable=False, weight=0.1, value=0, tags=["quest", "faction", "bellkeeper"],
    ),
    "crown-writ": Item(
        id="crown-writ", name="Crown Writ", item_type="quest",
        description="An official order stating that your investigation is now under Crown authority.", rarity="uncommon",
        stackable=False, weight=0.0, value=0, tags=["quest", "faction", "crown"],
    ),
    "hollow-mark": Item(
        id="hollow-mark", name="Hollow Mark", item_type="quest",
        description="A dark mark left by the underground when it decides you have been noticed.", rarity="rare",
        stackable=False, weight=0.0, value=0, tags=["quest", "faction", "hollow"],
    ),
}


class InventoryError(ValueError):
    pass


class Inventory:
    """Inventory operations kept separate from terminal presentation."""

    def __init__(self, entries: list[InventoryEntry] | None = None) -> None:
        self.entries = entries or []

    def _find(self, item_id: str) -> InventoryEntry | None:
        return next((entry for entry in self.entries if entry.item_id == item_id), None)

    def quantity(self, item_id: str) -> int:
        entry = self._find(item_id)
        return entry.quantity if entry else 0

    def add(self, item: Item, quantity: int = 1) -> None:
        if quantity <= 0:
            raise InventoryError("Quantity must be positive")
        entry = self._find(item.id)
        if entry is None:
            self.entries.append(InventoryEntry(item.id, min(quantity, item.max_stack)))
            remaining = quantity - min(quantity, item.max_stack)
            if remaining and item.stackable:
                self.add(item, remaining)
            elif remaining:
                raise InventoryError(f"{item.name} cannot be stacked")
            return
        if not item.stackable:
            raise InventoryError(f"{item.name} cannot be stacked")
        if entry.quantity + quantity > item.max_stack:
            raise InventoryError(f"Cannot carry more than {item.max_stack} of {item.name}")
        entry.quantity += quantity

    def remove(self, item: Item, quantity: int = 1) -> None:
        if quantity <= 0:
            raise InventoryError("Quantity must be positive")
        entry = self._find(item.id)
        if entry is None or entry.quantity < quantity:
            raise InventoryError(f"Not enough {item.name}")
        entry.quantity -= quantity
        if entry.quantity == 0:
            self.entries.remove(entry)

    def has(self, item_id: str, quantity: int = 1) -> bool:
        return self.quantity(item_id) >= quantity

    def total_weight(self, catalog: dict[str, Item] | None = None) -> float:
        catalog = catalog or DEFAULT_ITEMS
        return sum(catalog[e.item_id].weight * e.quantity for e in self.entries if e.item_id in catalog)

    def to_dict(self) -> list[dict[str, Any]]:
        return [entry.to_dict() for entry in self.entries]

    @classmethod
    def from_dict(cls, data: list[dict[str, Any]]) -> "Inventory":
        return cls([InventoryEntry(**entry) for entry in data])
