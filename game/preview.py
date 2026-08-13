"""Offline showcase for terminal RPG systems.

This command deliberately avoids story generation and AI calls except when the
user explicitly opens the AI Provider Setup preview.
"""

from __future__ import annotations

from pathlib import Path

from rpg_core.inventory_service import equipped_items, inventory_for
from rpg_core.items import DEFAULT_ITEMS
from rpg_core.player_service import create_new_game
from rpg_core.progression import (
    BACKGROUNDS,
    FACILITIES,
    derived_stats,
    record_action,
    refresh_prediction,
    stat_multiplier,
)
from rpg_world.facility_service import facility_info

from .ui import clear, menu, pause, title

ROOT = Path(__file__).resolve().parent


def _show_skull() -> None:
    try:
        skull = (ROOT / "assets" / "death_skull.txt").read_text(encoding="utf-8")
    except OSError:
        skull = "[death skull asset missing]"
    clear(); title(); print("\n"); print(skull)
    print("\n       YOU DIED\n")
    print("      Credit for skull on Instagram")
    print("              @vagonparovoz\n")
    print("        [R] Retry\n        [L] Load Save\n        [M] Main Menu")
    pause()


def _show_main_menu() -> None:
    clear(); title()
    menu("MAIN MENU PREVIEW", ["New Game", "Boot From Saves", "Edit AI Provider", "Exit"])


def _show_character() -> None:
    state = create_new_game("Preview Hero", background_id="soldier")
    clear(); title(); print("\nPLAYER / CHARACTER SHEET\n")
    p = state.player
    print(f"Name:         {p.name}\nBackground:   {p.background_id.title()}\nProfession:   {p.profession.title()}")
    print(f"Level:        {p.level}\nXP:           {p.xp} / {p.xp_to_next_level()}\nHP:            {p.hp} / {p.max_hp}\nGold:          {p.gold}")
    print(f"Stat points:  {p.stat_points}\nSkill points: {p.skill_points}\n")
    for stat, value in p.stats.items(): print(f"  {stat.title():<13} {value}")
    print("\nDerived:")
    for key, value in derived_stats(state).items(): print(f"  {key.replace('_', ' ').title():<18} {value:.1f}")
    print("\nEquipment:")
    for slot, item in equipped_items(state).items(): print(f"  {slot.title():<10} {item.name if item else 'Empty'}")
    pause()


def _show_inventory() -> None:
    state = create_new_game("Preview Hero")
    inventory = inventory_for(state)
    clear(); title(); print("\nINVENTORY\n")
    for index, entry in enumerate(inventory.entries, 1):
        item = DEFAULT_ITEMS.get(entry.item_id)
        if item: print(f"  {index:>2}. {item.name:<24} x{entry.quantity}")
    print(f"\nWeight: {inventory.total_weight(DEFAULT_ITEMS):.1f}")
    pause()


def _show_progression() -> None:
    state = create_new_game("Preview Hero", background_id="healer")
    for action in ("heal", "save", "protect", "research", "mercy"):
        record_action(state, action)
    god, confidence = refresh_prediction(state)
    clear(); title(); print("\nPROGRESSION / DIVINE RESONANCE SANDBOX\n")
    print(f"Level: {state.player.level}    XP: {state.player.xp}/{state.player.xp_to_next_level()}")
    print(f"Stat points: {state.player.stat_points}    Skill points: {state.player.skill_points}")
    print("\nDivine resonance:")
    total = sum(state.divine_affinity.values()) or 1
    for domain, value in state.divine_affinity.items():
        bar = "█" * min(20, int(value / max(1, total) * 20))
        print(f"  {domain:<10} {value:6.2f} {bar}")
    print(f"\nCurrent prediction: {god.title()} ({confidence:.1%})")
    print("\nStat multipliers:")
    for domain in ("life", "strength", "shadows", "knowledge", "forgotten"):
        print(f"  {domain:<10} ×{stat_multiplier(state, domain):.3f}")
    pause()


def _show_backgrounds() -> None:
    clear(); title(); print("\nBACKGROUNDS / SPECIAL ACTIONS\n")
    for background in BACKGROUNDS.values():
        print(f"{background.name:<14} — {background.description}")
        print(f"  actions: {', '.join(background.actions)}\n")
    pause()


def _show_facilities() -> None:
    clear(); title(); print("\nWORLD FACILITIES\n")
    for facility_id in FACILITIES:
        info = facility_info(facility_id)
        print(f"{info['name']:<20} {', '.join(info['actions'])}")
    pause()


def _show_placeholder(name: str, lines: list[str]) -> None:
    clear(); title(); print(f"\n{name}\n")
    for line in lines: print(line)
    pause()


def preview() -> None:
    while True:
        selected = menu("DEVELOPER PREVIEW", [
            "Main Menu", "Death Screen", "Player / Character Sheet", "Inventory UI",
            "Progression + Divine Resonance", "Backgrounds / Professions", "Facilities",
            "AI Provider Setup", "Save Slots", "World / Area Browser", "Exit Preview",
        ])
        if selected == 0: _show_main_menu()
        elif selected == 1: _show_skull()
        elif selected == 2: _show_character()
        elif selected == 3: _show_inventory()
        elif selected == 4: _show_progression()
        elif selected == 5: _show_backgrounds()
        elif selected == 6: _show_facilities()
        elif selected == 7:
            from .ai_setup import provider_setup
            provider_setup(force=True)
        elif selected == 8:
            _show_placeholder("SAVE SLOTS", ["Save1 — Preview Hero, Lv.1", "Save2 — EMPTY", "Save3 — EMPTY"])
        elif selected == 9:
            _show_placeholder("WORLD / AREA BROWSER", [
                "The Ashen Capital", "The Greywater Coast", "The Verdant March", "The Hollow Under",
                "The Sunken Archive", "The Ironbound Frontier", "The Blackglass Desert", "The Skygrave",
            ])
        else:
            return
