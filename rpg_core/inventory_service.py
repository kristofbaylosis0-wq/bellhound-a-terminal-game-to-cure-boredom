"""Inventory and equipment operations."""

from __future__ import annotations

from .models import GameState

EQUIPMENT_SLOTS = {"weapon", "armor", "accessory"}


def add_item(state: GameState, item_id: str, quantity: int = 1) -> None:
    if not item_id.strip():
        raise ValueError("Item ID cannot be empty")
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    state.player.inventory.extend([item_id] * quantity)


def remove_item(state: GameState, item_id: str, quantity: int = 1) -> None:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    for _ in range(quantity):
        try:
            state.player.inventory.remove(item_id)
        except ValueError as exc:
            raise ValueError(f"Item not found: {item_id}") from exc


def equip_item(state: GameState, item_id: str, slot: str) -> None:
    slot = slot.strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise ValueError(f"Unknown equipment slot: {slot}")
    if item_id not in state.player.inventory:
        raise ValueError(f"Item not in inventory: {item_id}")
    state.player.equipment[slot] = item_id


def unequip_item(state: GameState, slot: str) -> str:
    slot = slot.strip().lower()
    if slot not in EQUIPMENT_SLOTS:
        raise ValueError(f"Unknown equipment slot: {slot}")
    item_id = state.player.equipment.get(slot)
    if item_id is None:
        raise ValueError(f"Nothing equipped in {slot}")
    state.player.equipment[slot] = None
    return item_id
