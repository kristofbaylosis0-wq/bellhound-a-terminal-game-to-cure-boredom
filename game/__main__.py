"""Command-line entry point for the terminal RPG."""

from __future__ import annotations

import argparse
from pathlib import Path

from rpg_core.player_service import create_new_game
from rpg_core.save_manager import SaveManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RPG",
        description="A text RPG game made by ChatGPT",
    )
    parser.add_argument(
        "target",
        nargs="*",
        help="game, new game, or a save slot name such as Save1",
    )
    return parser


def boot_launcher(manager: SaveManager) -> None:
    print("\n╔══════════════════════════════════════════════╗")
    print("║       A TEXT RPG GAME MADE BY CHATGPT      ║")
    print("╠══════════════════════════════════════════════╣")
    print("║                                              ║")
    print("║  1. NEW GAME                                ║")
    print("║  2. BOOT FROM SAVES                         ║")
    print("║  3. EXIT                                    ║")
    print("║                                              ║")
    print("╚══════════════════════════════════════════════╝")

    while True:
        choice = input("\n> ").strip().lower()
        if choice in {"1", "new", "new game"}:
            start_new_game(manager)
            return
        if choice in {"2", "load", "saves", "boot from saves"}:
            boot_from_saves(manager)
            return
        if choice in {"3", "exit", "quit", "q"}:
            return
        print("Choose 1, 2, or 3.")


def boot_from_saves(manager: SaveManager) -> None:
    while True:
        print("\nSAVE FILES")
        for info in manager.list_slots():
            if not info.exists:
                print(f"  Save{info.slot}: EMPTY")
                continue
            level = info.level if info.level is not None else "?"
            player = info.player_name or "Unknown"
            location = info.location or "Unknown"
            print(f"  Save{info.slot}: {player} | Level {level} | {location}")

        choice = input("\nEnter Save1/Save2/Save3, or B to go back:\n> ").strip()
        if choice.lower() in {"b", "back"}:
            return
        normalized = choice.lower().replace(".json", "")
        if normalized in {"save1", "save2", "save3"}:
            slot = int(normalized[-1])
            if not manager.exists(slot):
                print("That save slot is empty.")
                continue
            load_save(manager, f"Save{slot}")
            return
        print("Enter Save1, Save2, Save3, or B.")


def start_new_game(manager: SaveManager) -> None:
    print("\nNEW GAME")
    while True:
        name = input("What is your name?\n> ").strip()
        try:
            state = create_new_game(name)
        except ValueError as exc:
            print(f"Invalid name: {exc}")
            continue
        break

    manager.save(1, state)
    print(f"\nWelcome, {state.player.name}.")
    print("Your first game has been saved to Save1.")
    print(f"Level {state.player.level} | HP {state.player.hp}/{state.player.max_hp}")


def load_save(manager: SaveManager, name: str) -> None:
    normalized = name.lower().replace(".json", "")
    if normalized.startswith("save") and normalized[4:].isdigit():
        slot = int(normalized[4:])
    else:
        print(f"Save '{name}' was not found. Use Save1, Save2, or Save3.")
        return

    if slot not in {1, 2, 3} or not manager.exists(slot):
        print(f"Save '{name}' was not found.")
        return

    state = manager.load(slot)
    print(f"\nLoaded {name}.")
    print(f"Welcome back, {state.player.name}.")
    print(f"Level {state.player.level} | HP {state.player.hp}/{state.player.max_hp}")
    print(f"Location: {state.location}")


def main() -> None:
    args = build_parser().parse_args()
    target = [part.lower() for part in args.target]
    manager = SaveManager()

    if not target or target == ["game"]:
        boot_launcher(manager)
        return

    if target in (["new", "game"], ["newgame"]):
        start_new_game(manager)
        return

    if len(target) == 1:
        load_save(manager, target[0])
        return

    print("Usage: RPG game | RPG new game | RPG <save-name>")


if __name__ == "__main__":
    main()
