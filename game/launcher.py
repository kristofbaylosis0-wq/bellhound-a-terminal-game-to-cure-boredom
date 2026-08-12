"""Main launcher flows for the terminal RPG."""

from __future__ import annotations

from rpg_core.player_service import create_new_game
from rpg_core.save_manager import SaveManager

from .ui import clear, menu, pause, prompt_name, title


def new_game(manager: SaveManager) -> None:
    clear()
    title()
    print("\nStarting a new game...\n")

    name = prompt_name(create_new_game)
    state = create_new_game(name)
    manager.save(1, state)

    clear()
    title()
    print(f"\nWelcome, {state.player.name}.\n")
    print("Your journey begins with a clean slate.")
    print("A starting save has been created in Save1.")
    pause()


def load_saves(manager: SaveManager) -> None:
    while True:
        infos = manager.list_slots()
        options = []
        for info in infos:
            if info.exists:
                player = info.player_name or "Unknown"
                level = info.level if info.level is not None else "?"
                location = info.location or "Unknown"
                options.append(f"Save{info.slot} — {player}, Lv.{level}, {location}")
            else:
                options.append(f"Save{info.slot} — EMPTY")
        options.append("Back")

        selected = menu("BOOT FROM SAVES", options)
        if selected == 3:
            return
        slot = selected + 1
        if not manager.exists(slot):
            clear()
            title()
            print(f"\nSave{slot} is empty.")
            pause()
            continue

        state = manager.load(slot)
        clear()
        title()
        print(f"\nLoaded Save{slot}.\n")
        print(f"Welcome back, {state.player.name}.")
        print(f"Level {state.player.level} | HP {state.player.hp}/{state.player.max_hp}")
        print(f"Location: {state.location}")
        pause()
        return


def launcher(manager: SaveManager) -> None:
    while True:
        selected = menu("MAIN MENU", ["New Game", "Boot From Saves", "Exit"])
        if selected == 0:
            new_game(manager)
        elif selected == 1:
            load_saves(manager)
        else:
            return
