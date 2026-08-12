"""Command-line entry point for the terminal RPG."""

from __future__ import annotations

import argparse
from pathlib import Path


SAVE_DIR = Path.home() / ".text-rpg" / "saves"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="RPG", description="A text RPG game made by ChatGPT")
    parser.add_argument(
        "target",
        nargs="*",
        help="'game' to open the launcher, 'new game' to start a new game, or a save name to load",
    )
    return parser


def boot_launcher() -> None:
    print("A text RPG game made by ChatGPT")
    print("\n[ GAME ]")
    print("1. New Game")
    print("2. Boot From Saves")
    print("3. Exit")
    # Full interactive launcher will be connected to the game UI subsystem next.


def start_new_game() -> None:
    print("Starting a new game...")
    # Character creation will be connected to the player subsystem next.


def load_save(name: str) -> None:
    path = SAVE_DIR / f"{name}.json"
    if not path.is_file():
        print(f"Save '{name}' was not found.")
        print(f"Checked: {path}")
        return
    print(f"Loading save: {name}")
    # Save loading will be connected to SaveManager next.


def main() -> None:
    args = build_parser().parse_args()
    target = [part.lower() for part in args.target]

    if not target or target == ["game"]:
        boot_launcher()
        return

    if target == ["new", "game"] or target == ["newgame"]:
        start_new_game()
        return

    if len(target) == 1:
        load_save(target[0])
        return

    print("Usage: RPG game | RPG new game | RPG <save-name>")


if __name__ == "__main__":
    main()
