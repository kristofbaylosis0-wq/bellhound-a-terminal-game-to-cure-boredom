"""Offline showcase for terminal RPG systems.

This command deliberately avoids story generation and AI calls. It is safe to
run before an AI provider is configured.
"""

from __future__ import annotations

from pathlib import Path

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
            _show_placeholder(
                "PLAYER / CHARACTER SHEET",
                [
                    "Name:       Preview Hero",
                    "Level:      5",
                    "XP:         320 / 500",
                    "HP:         84 / 100",
                    "MP:         42 / 60",
                    "Gold:       1,250",
                    "Status:     Healthy",
                ],
            )
        elif selected == 3:
            _show_placeholder(
                "INVENTORY",
                [
                    "[1] Iron Sword       x1",
                    "[2] Health Potion    x4",
                    "[3] Torch             x2",
                    "[4] Ancient Coin      x7",
                    "[5] Empty slot",
                ],
            )
        elif selected == 4:
            from .ai_setup import provider_setup

            provider_setup(force=True)
        elif selected == 5:
            _show_placeholder(
                "SAVE SLOTS",
                [
                    "Save1 — Preview Hero, Lv.5",
                    "Save2 — EMPTY",
                    "Save3 — EMPTY",
                ],
            )
        elif selected == 6:
            _show_placeholder(
                "WORLD / AREA BROWSER",
                [
                    "Major Areas:",
                    "  The Ashen Road",
                    "  Blackwood Forest",
                    "  Arkhaven",
                    "  The Sunken Ruins",
                    "  [More areas will appear as the world is built]",
                ],
            )
        else:
            return
