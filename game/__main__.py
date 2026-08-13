"""Command-line entry point for the terminal RPG."""

from __future__ import annotations

import argparse

from rpg_core.save_manager import SaveManager

from .launcher import launcher, new_game, preview
from .ui import clear, pause, title
from story.engine import StoryEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="RPG",
        description="A text RPG game made by ChatGPT",
    )
    parser.add_argument(
        "target",
        nargs="*",
        help="game, preview, new game, or a save slot name such as Save1",
    )
    return parser


def _start_saved_story(manager: SaveManager, slot: int) -> int:
    state = manager.load(slot)
    clear()
    title()
    print(f"\nLoaded Save{slot}.\n")
    print(f"Welcome back, {state.player.name}.")
    print(f"Level {state.player.level} | HP {state.player.hp}/{state.player.max_hp}")
    print(f"Story: Chapter {state.chapter} — {state.current_story_node}")
    pause()
    StoryEngine(state, manager, save_slot=slot).run()
    return 0


def load_save(manager: SaveManager, name: str) -> int:
    normalized = name.lower().replace(".json", "")
    if normalized.startswith("save") and normalized[4:].isdigit():
        slot = int(normalized[4:])
    else:
        print(f"Save '{name}' was not found. Use Save1, Save2, or Save3.")
        return 1

    if slot not in {1, 2, 3} or not manager.exists(slot):
        print(f"Save '{name}' was not found.")
        return 1

    try:
        return _start_saved_story(manager, slot)
    except Exception as exc:
        clear()
        title()
        print("\nUnable to resume that save.\n")
        print(f"{type(exc).__name__}: {exc}")
        print(f"\nSave{slot} was not deleted or modified.")
        pause()
        return 1


def main() -> int:
    args = build_parser().parse_args()
    target = [part.lower() for part in args.target]
    manager = SaveManager()

    # Preview and the handcrafted campaign are intentionally usable without
    # an AI provider. AI is an optional gameplay layer, not a boot dependency.
    if target == ["preview"]:
        preview()
        return 0

    if not target or target == ["game"]:
        launcher(manager)
        return 0

    if target in (["new", "game"], ["newgame"]):
        new_game(manager)
        return 0

    if len(target) == 1:
        return load_save(manager, target[0])

    print("Usage: RPG game | RPG preview | RPG new game | RPG <save-name>")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
