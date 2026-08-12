"""Player-facing inventory and equipment operations."""

from __future__ import annotations

from .items import DEFAULT_ITEMS, Inventory, InventoryError, Item
from .models import GameState

EQUIPMENT_SLOTS = {"weapon", "armor", "accessory"}


def inventory_for(state: GameState) -> Inventory:
    counts: dict[str, int] = {}
    for item_id in state.player.inventory:
        counts[item_id] = counts.get(item_id, 0) + 1
    return Inventory([{"item_id": item_id, "quantity": quantity} for item_id, quantity in counts.items()])


def _write_inventory(state: GameState, inventory: Inventory) -> None:
    state.player.inventory = [
        entry.item_id for entry in inventory.entries for _ in range(entry.quantity)
    ]


def add_item(state: GameState, item_id: str, quantity: int = 1) -> None:
    item = DEFAULT_ITEMS.get(item_id)
    if item is None:
        raise InventoryError(f"Unknown item: {item_id}")
    inventory = inventory_for(state)
    inventory.add(item, quantity)
    _write_inventory(state, inventory)


def remove_item(state: GameState, item_id: str, quantity: int = 1) -> None:
    item = DEFAULT_ITEMS.get(item_id)
    if item is None:
        raise InventoryError(f"Unknown item: {item_id}")
    inventory = inventory_for(state)
    inventory.remove(item, quantity)
    _write_inventory(state, inventory)


def equip_item(state: GameState, item_id: str, slot: str | None = None) -> None:
    item = DEFAULT_ITEMS.get(item_id)
    if item is None:
        raise InventoryError(f"Unknown item: {item_id}")
    slot = (slot or item.item_type).strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise InventoryError(f"Unknown equipment slot: {slot}")
    if item_id not in state.player.inventory:
        raise InventoryError(f"Item not in inventory: {item_id}")
    state.player.equipment[slot] = item_id


def unequip_item(state: GameState, slot: str) -> str:
    slot = slot.strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise InventoryError(f"Unknown equipment slot: {slot}")
    item_id = state.player.equipment.get(slot)
    if item_id is None:
        raise InventoryError(f"Nothing equipped in {slot}")
    state.player.equipment[slot] = None
    return item_id


def equipped_items(state: GameState) -> dict[str, Item | None]:
    return {
        slot: DEFAULT_ITEMS.get(item_id) if item_id else None
        for slot, item_id in state.player.equipment.items()
    }
