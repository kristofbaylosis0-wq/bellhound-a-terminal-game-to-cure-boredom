"""Reusable spoiler-safe terminal screens for the RPG UI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .ui import clear, menu, pause, terminal_input, title


@dataclass(frozen=True)
class ScreenDemo:
    name: str
    description: str


HUD_DEMO = ScreenDemo("In-Game HUD", "Compact gameplay status without story spoilers.")


def _bar(current: float, maximum: float, width: int = 20) -> str:
    maximum = max(1.0, maximum)
    filled = max(0, min(width, int(current / maximum * width)))
    return "█" * filled + "░" * (width - filled)


def gameplay_hud(*, name: str = "Preview Hero", level: int = 7, hp: int = 73, max_hp: int = 100,
                 xp: int = 240, xp_next: int = 420, gold: int = 185, location: str = "Example Town",
                 objective: str = "Explore the town") -> None:
    clear(); title()
    print("\nGAMEPLAY HUD\n")
    print(f"{name}  Lv.{level}   {location}")
    print(f"HP  [{_bar(hp, max_hp)}] {hp}/{max_hp}")
    print(f"XP  [{_bar(xp, xp_next)}] {xp}/{xp_next}")
    print(f"Gold: {gold}")
    print(f"Objective: {objective}")
    pause()


def pause_menu() -> int:
    return menu("GAME MENU", [
        "Resume", "Character", "Inventory", "Quests", "Map", "Save", "Settings", "Main Menu",
    ])


def dialogue_screen(*, speaker: str = "Mira", lines: Iterable[str] = ("The road is quiet tonight.", "Something feels wrong."),
                    choices: list[str] | None = None) -> int | None:
    clear(); title()
    print(f"\n{speaker}\n")
    for line in lines:
        print(line); print()
    if choices:
        return menu("RESPONSE", choices)
    pause()
    return None


def confirmation_screen(prompt: str = "Leave the area?") -> bool:
    clear(); title()
    print(f"\n{prompt}\n")
    selected = menu("CONFIRM", ["Yes", "No"])
    return selected == 0


def quest_journal() -> int:
    return menu("QUEST JOURNAL", ["Active", "Completed", "Failed", "Back"])


def map_screen() -> int:
    return menu("WORLD MAP", ["Current Area", "Discovered Areas", "Fast Travel", "Back"])


def combat_screen(*, player_name: str = "Hero", player_hp: int = 82, player_max_hp: int = 100,
                  enemy_name: str = "Ash Hound", enemy_hp: int = 54, enemy_max_hp: int = 75) -> int:
    clear(); title()
    print("\nCOMBAT\n")
    print(f"{enemy_name}")
    print(f"HP [{_bar(enemy_hp, enemy_max_hp)}] {enemy_hp}/{enemy_max_hp}\n")
    print(f"{player_name}")
    print(f"HP [{_bar(player_hp, player_max_hp)}] {player_hp}/{player_max_hp}\n")
    return menu("COMBAT ACTION", ["Attack", "Skill", "Item", "Defend", "Flee"])


def shop_screen() -> int:
    return menu("GENERAL SHOP", [
        "Buy", "Sell", "Inspect Item", "Haggle", "Leave",
    ])


def blacksmith_screen() -> int:
    return menu("BLACKSMITH", [
        "Forge", "Repair", "Salvage", "Upgrade", "Buy Equipment", "Leave",
    ])


def training_screen() -> int:
    return menu("TRAINING GROUNDS", [
        "Train Strength", "Train Agility", "Train Endurance", "Spar", "Learn Combat Skill", "Leave",
    ])


def equipment_screen() -> int:
    return menu("EQUIPMENT", ["Weapon", "Armor", "Accessory", "Compare", "Unequip", "Back"])


def skills_screen() -> int:
    return menu("SKILLS", ["Combat Skills", "Passive Skills", "Utility Skills", "Upgrade Skill", "Back"])


def codex_screen() -> int:
    return menu("CODEX", ["Lore", "Creatures", "Materials", "Locations", "People", "Back"])


def settings_screen() -> int:
    return menu("SETTINGS", ["Text Speed", "Animation Effects", "Color", "Input Style", "Accessibility", "Back"])


def save_confirmation(slot: int = 1) -> None:
    clear(); title()
    print(f"\nSave{slot} saved successfully.\n")
    pause()


def transition_screen(chapter: int, destination: str) -> None:
    clear(); title()
    print(f"\nCHAPTER {chapter}\n")
    print(f"Traveling to {destination}...\n")
    print("The road continues.")
    pause()


def notification_screen(message: str = "New quest added.", *, kind: str = "NOTICE") -> None:
    clear(); title()
    print(f"\n[{kind}]\n")
    print(message)
    pause()


def divine_resonance_screen() -> None:
    clear(); title()
    print("\nINNER RESONANCE\n")
    print("Something within you is beginning to awaken.")
    print()
    print("██████████░░░░░░░░░░")
    print()
    print("The feeling is unfamiliar.")
    print("You cannot yet name it.")
    pause()


def systems_showcase() -> None:
    """Open every spoiler-safe UI screen from one menu."""
    actions = [
        ("In-Game HUD", gameplay_hud),
        ("Game Menu", pause_menu),
        ("Dialogue", lambda: dialogue_screen()),
        ("Choice Confirmation", confirmation_screen),
        ("Quest Journal", quest_journal),
        ("Map", map_screen),
        ("Combat", combat_screen),
        ("Shop", shop_screen),
        ("Blacksmith", blacksmith_screen),
        ("Training", training_screen),
        ("Equipment", equipment_screen),
        ("Skills", skills_screen),
        ("Codex / Lore", codex_screen),
        ("Settings", settings_screen),
        ("Save Confirmation", save_confirmation),
        ("Chapter Transition", lambda: transition_screen(1, "Example Region")),
        ("Notification", notification_screen),
        ("Divine Resonance", divine_resonance_screen),
        ("Back", None),
    ]
    while True:
        selected = menu("UI SHOWCASE", [name for name, _ in actions])
        func = actions[selected][1]
        if func is None:
            return
        func()
