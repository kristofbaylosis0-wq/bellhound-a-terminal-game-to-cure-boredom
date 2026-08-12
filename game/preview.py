"""Offline showcase for terminal RPG systems.

This command deliberately avoids story generation and AI calls except when the
user explicitly opens the AI Provider Setup preview.
"""

from __future__ import annotations

from pathlib import Path

from rpg_core.inventory_service import equipped_items, inventory_for
from rpg_core.items import DEFAULT_ITEMS
from rpg_core.player_service import create_new_game

from .ui import clear, menu, pause, title


ROOT = Path(__file__).resolve().parent


def _show_skull() -> None:
    skull_path = ROOT / "assets" / "death_skull.txt"
    try:
        skull = skull_path.read_text(encoding="utf-8")
    except OSError:
        skull = "[death skull asset missing]"

    clear()
    title()
    print("\n")
    print(skull)
    print("\n       YOU DIED\n")
    print("      Credit for skull on Instagram")
    print("              @vagonparovoz\n")
    print("        [R] Retry")
    print("        [L] Load Save")
    print("        [M] Main Menu")
    pause()


def _show_main_menu() -> None:
    clear()
    title()
    menu("MAIN MENU PREVIEW", ["New Game", "Boot From Saves", "Edit AI Provider", "Exit"])


def _show_character() -> None:
    state = create_new_game("Preview Hero")
    clear()
    title()
    print("\nPLAYER / CHARACTER SHEET\n")
    print(f"Name:         {state.player.name}")
    print(f"Level:        {state.player.level}")
    print(f"XP:            {state.player.xp} / {state.player.xp_to_next_level()}")
    print(f"HP:           {state.player.hp} / {state.player.max_hp}")
    print(f"Gold:         {state.player.gold}")
    print(f"Stat points:  {state.player.stat_points}")
    print(f"Skill points: {state.player.skill_points}\n")
    for stat, value in state.player.stats.items():
        print(f"  {stat.title():<13} {value}")
    print("\nEquipment:")
    for slot, item in equipped_items(state).items():
        print(f"  {slot.title():<10} {item.name if item else 'Empty'}")
    pause()


def _show_inventory() -> None:
    state = create_new_game("Preview Hero")
    inventory = inventory_for(state)
    clear()
    title()
    print("\nINVENTORY\n")
    for index, entry in enumerate(inventory.entries, 1):
        item = DEFAULT_ITEMS.get(entry.item_id)
        if item:
            print(f"  {index:>2}. {item.name:<24} x{entry.quantity}")
    print(f"\nWeight: {inventory.total_weight(DEFAULT_ITEMS):.1f}")
    print("\nEquipped:")
    for slot, item in equipped_items(state).items():
        stats = ", ".join(f"{k} +{v}" for k, v in item.stats.items()) if item else ""
        print(f"  {slot.title():<10} {item.name if item else 'Empty'} {stats}")
    print("\nExample item effects:")
    print("  Health Potion → heals 30 HP")
    pause()


def _show_placeholder(name: str, lines: list[str]) -> None:
    clear()
    title()
    print(f"\n{name}\n")
    for line in lines:
        print(line)
    pause()


def preview() -> None:
    """Preview implemented/non-story-facing UI and systems."""
    while True:
        selected = menu(
            "DEVELOPER PREVIEW",
            [
                "Main Menu",
                "Death Screen",
                "Player / Character Sheet",
                "Inventory UI",
                "AI Provider Setup",
                "Save Slots",
                "World / Area Browser",
                "Exit Preview",
            ],
        )

        if selected == 0:
            _show_main_menu()
        elif selected == 1:
            _show_skull()
        elif selected == 2:
            _show_character()
        elif selected == 3:
            _show_inventory()
        elif selected == 4:
            from .ai_setup import provider_setup

            provider_setup(force=True)
        elif selected == 5:
            _show_placeholder(
                "SAVE SLOTS",
                [
                    "Save1 — Preview Hero, Lv.1",
                    "Save2 — EMPTY",
                    "Save3 — EMPTY",
                ],
            )
        elif selected == 6:
            _show_placeholder(
                "WORLD / AREA BROWSER",
                [
                    "Major Areas:",
                    "  The Ashen Capital",
                    "  The Greywater Coast",
                    "  The Verdant March",
                    "  The Hollow Under",
                    "  The Sunken Archive",
                    "  The Ironbound Frontier",
                    "  The Blackglass Desert",
                    "  The Skygrave",
                ],
            )
        else:
            return
