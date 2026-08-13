from rpg_core.models import GameState
from rpg_core.player_service import create_new_game


def test_new_game_defaults_to_handcrafted_story():
    state = create_new_game("Tester")
    assert state.story_mode == "handcrafted"
    assert state.to_dict()["save_version"] == 5


def test_new_game_can_select_dynamic_story():
    state = create_new_game("Tester", story_mode="dynamic")
    assert state.story_mode == "dynamic"
    restored = GameState.from_dict(state.to_dict())
    assert restored.story_mode == "dynamic"


def test_legacy_save_without_story_mode_remains_handcrafted():
    state = create_new_game("Tester")
    payload = state.to_dict()
    payload.pop("story_mode")
    payload["save_version"] = 4
    restored = GameState.from_dict(payload)
    assert restored.story_mode == "handcrafted"
