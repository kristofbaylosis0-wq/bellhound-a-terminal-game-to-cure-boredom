"""Main launcher flows for the terminal RPG."""

from __future__ import annotations

from rpg_core.player_service import create_new_game
from rpg_core.save_manager import SaveManager
from rpg_core.progression import BACKGROUNDS
from rpg_core.models import STORY_MODES

from .ai_setup import configured, provider_setup
from .preview import preview
from .ui import clear, menu, pause, prompt_name, title
from story.engine import StoryEngine


def _choose_background() -> str:
    ids = list(BACKGROUNDS)
    options = [f"{BACKGROUNDS[item].name} — {BACKGROUNDS[item].description}" for item in ids]
    selected = menu("CHOOSE YOUR BACKGROUND", options, footer="This shapes your starting options, not your destiny.")
    return ids[selected]


def _choose_story_mode() -> str | None:
    labels = [
        "Hard-coded Story — Offline, AI not required",
        "Dynamic Story — AI required, online",
        "Back",
    ]
    selected = menu("CHOOSE STORY MODE", labels, footer="Dynamic Story uses AI for presentation; the game engine remains authoritative.")
    if selected == 0:
        return "handcrafted"
    if selected == 1:
        if not configured():
            clear()
            title()
            print("\nDynamic Story requires an AI provider and model.\n")
            print("Let's configure one before starting.\n")
            if provider_setup(force=True) is None:
                return None
        return "dynamic"
    return None


def _start_story(manager: SaveManager, state, *, save_slot: int) -> None:
    try:
        if state.story_mode == "dynamic":
            from story.dynamic import run_dynamic
            run_dynamic(manager, state, save_slot=save_slot)
        else:
            StoryEngine(state, manager, save_slot=save_slot).run()
    except Exception as exc:
        clear()
        title()
        print("\nThe story engine encountered an error.\n")
        print(f"{type(exc).__name__}: {exc}")
        print(f"\nYour current state has been kept in Save{save_slot}.")
        manager.save(save_slot, state)
        manager.autosave(state)
        pause()


def new_game(manager: SaveManager) -> None:
    clear()
    title()
    print("\nStarting a new game...\n")

    story_mode = _choose_story_mode()
    if story_mode is None:
        return

    name = prompt_name(create_new_game)
    background_id = _choose_background()
    state = create_new_game(name, background_id=background_id, story_mode=story_mode)
    manager.save(1, state)
    manager.autosave(state)

    clear()
    title()
    print(f"\nWelcome, {state.player.name}.\n")
    print(f"Story mode: {'Dynamic' if story_mode == 'dynamic' else 'Hard-coded'}")
    print(f"Background: {BACKGROUNDS[background_id].name}")
    print("Your choices—not your background—will shape who you become.")
    print("\nYour journey begins...\n")
    pause()
    _start_story(manager, state, save_slot=1)


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
        print(f"Story mode: {'Dynamic' if state.story_mode == 'dynamic' else 'Hard-coded'}")
        print(f"Story: Chapter {state.chapter} — {state.current_story_node}")
        pause()
        _start_story(manager, state, save_slot=slot)
        return


def launcher(manager: SaveManager) -> None:
    while True:
        selected = menu(
            "MAIN MENU",
            ["New Game", "Boot From Saves", "Edit AI Provider", "Preview", "Exit"],
        )
        if selected == 0:
            new_game(manager)
        elif selected == 1:
            load_saves(manager)
        elif selected == 2:
            provider_setup(force=True)
        elif selected == 3:
            preview()
        else:
            return
