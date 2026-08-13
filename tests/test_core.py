from pathlib import Path

import pytest

from rpg_core.models import GameState, Player
from rpg_core.player_service import create_new_game, grant_xp, spend_stat_point
from rpg_core.save_manager import SaveManager


def test_new_game_requires_name() -> None:
    with pytest.raises(ValueError):
        create_new_game("   ")


def test_leveling_and_stat_points() -> None:
    state = create_new_game("Hero")
    gained = grant_xp(state, 100)

    assert gained == 1
    assert state.player.level == 2
    assert state.player.stat_points == 3
    assert state.player.skill_points == 1
    assert state.player.max_hp == 110
    assert state.player.hp == 110

    spend_stat_point(state, "strength")
    assert state.player.stats["strength"] == 6
    assert state.player.stat_points == 2


def test_save_load_round_trip(tmp_path: Path) -> None:
    state = create_new_game("TestPlayer", random_seed=1234)
    state.location = "old_market"
    state.relationships["mira"] = 72
    state.world_flags["found_key"] = True
    grant_xp(state, 150)

    saves = SaveManager(tmp_path / "profile")
    saves.save(1, state, playtime_seconds=3720)

    loaded = saves.load(1)
    assert loaded.to_dict() == state.to_dict()

    info = saves.list_slots()[0]
    assert info.exists is True
    assert info.player_name == "TestPlayer"
    assert info.level == state.player.level
    assert info.location == "old_market"
    assert info.playtime_seconds == 3720


def test_empty_slot_cannot_be_loaded(tmp_path: Path) -> None:
    saves = SaveManager(tmp_path / "profile")
    with pytest.raises(FileNotFoundError):
        saves.load(2)


def test_atomic_save_creates_only_final_file(tmp_path: Path) -> None:
    saves = SaveManager(tmp_path / "profile")
    saves.save(1, GameState(player=Player("Hero")))
    files = list((tmp_path / "profile" / "saves").iterdir())
    assert [path.name for path in files] == ["save1.json"]
