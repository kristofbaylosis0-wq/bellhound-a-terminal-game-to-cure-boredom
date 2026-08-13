"""Gameplay actions exposed by world facilities."""

from __future__ import annotations

from rpg_core.progression import (
    FACILITIES,
    add_gold,
    buy_item,
    heal_player,
    record_action,
    repair_item,
    sell_item,
    train,
)
from rpg_core.models import GameState


def facility_info(facility_id: str) -> dict[str, object]:
    name, actions = FACILITIES[facility_id]
    return {"id": facility_id, "name": name, "actions": list(actions)}


def use_facility(state: GameState, facility_id: str, action: str, **kwargs: object) -> object:
    if facility_id not in FACILITIES:
        raise ValueError(f"Unknown facility: {facility_id}")
    allowed = set(FACILITIES[facility_id][1])
    if action not in allowed:
        raise ValueError(f"{action} is not available at {facility_id}")

    if action.startswith("train_"):
        stat = action.removeprefix("train_")
        return train(state, stat)
    if action == "heal":
        return heal_player(state)
    if action == "buy":
        return buy_item(state, str(kwargs["item_id"]), int(kwargs.get("quantity", 1)), discount=float(kwargs.get("discount", 0.0)))
    if action == "sell":
        return sell_item(state, str(kwargs["item_id"]), int(kwargs.get("quantity", 1)))
    if action == "repair":
        return repair_item(state, str(kwargs["item_id"]))

    # Social/lore facilities register their activity now; their full event
    # content can be layered on later without changing the interface.
    record_action(state, action)
    return True
