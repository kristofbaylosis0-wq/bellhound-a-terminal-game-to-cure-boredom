"""Entry point for the terminal RPG foundation."""

from __future__ import annotations

from rpg_core.player_service import create_new_game
from rpg_core.save_manager import SaveManager
from rpg_core.ui import character_sheet, inventory, main_menu, notify, prompt_name, save_selection


def choose(prompt: str, options: dict[str, str]) -> str:
    while True:
        value = input(prompt).strip().lower()
        if value in options:
            return options[value]
        print(f"Choose one of: {', '.join(options)}")


def new_game(save_manager: SaveManager) -> None:
    name = prompt_name()
    state = create_new_game(name)
    save_manager.autosave(state)
    save_manager.save(1, state)
    notify(f"Welcome, {name}. Your new game was created in Save 1.")
    game_loop(save_manager, state)


def load_game(save_manager: SaveManager) -> None:
    infos = save_manager.list_slots()
    save_selection(infos)
    options = {str(info.slot): str(info.slot) for info in infos if info.exists}
    options["b"] = "b"
    choice = choose("Select a save slot or B to go back.\n> ", options)
    if choice == "b":
        return
    state = save_manager.load(int(choice))
    notify(f"Booted {state.player.name}'s game from Save {choice}.")
    game_loop(save_manager, state, int(choice))


def game_loop(save_manager: SaveManager, state, slot: int = 1) -> None:
    while True:
        print("\nCommands: character | inventory | save | menu")
        command = input("> ").strip().lower()
        if command in {"character", "char", "status"}:
            character_sheet(state.player)
        elif command in {"inventory", "inv"}:
            inventory(state)
        elif command == "save":
            save_manager.save(slot, state)
            save_manager.autosave(state)
            notify(f"Saved to Save {slot}.")
        elif command == "menu":
            return
        else:
            notify("That command is not available yet.")


def run() -> None:
    save_manager = SaveManager()
    while True:
        main_menu()
        choice = choose("\n> ", {"1": "new", "new": "new", "2": "load", "load": "load", "3": "settings", "settings": "settings", "4": "exit", "exit": "exit"})
        if choice == "new":
            new_game(save_manager)
        elif choice == "load":
            load_game(save_manager)
        elif choice == "settings":
            notify("Settings are not implemented yet.")
        else:
            notify("Goodbye.")
            return


if __name__ == "__main__":
    run()
