from pathlib import Path

from rpg_core.player_service import create_new_game
from rpg_core.save_manager import SaveManager


def test_new_game_creates_save(tmp_path: Path) -> None:
    manager = SaveManager(tmp_path)
    state = create_new_game("Arin")
    manager.save(1, state)

    assert manager.exists(1)
    info = manager.list_slots()[0]
    assert info.player_name == "Arin"
    assert info.level == 1


def test_save_load_round_trip(tmp_path: Path) -> None:
    manager = SaveManager(tmp_path)
    state = create_new_game("Mira")
    state.player.add_xp(250)
    state.location = "greywater-coast"
    manager.save(2, state)

    loaded = manager.load(2)
    assert loaded.player.name == "Mira"
    assert loaded.player.level == 3
    assert loaded.player.xp == 15
    assert loaded.location == "greywater-coast"


def test_empty_slots_are_visible(tmp_path: Path) -> None:
    manager = SaveManager(tmp_path)
    slots = manager.list_slots()
    assert [slot.exists for slot in slots] == [False, False, False]
