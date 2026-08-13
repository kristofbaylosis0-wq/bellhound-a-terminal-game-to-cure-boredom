from rpg_core.player_service import create_new_game
from rpg_core.progression import (
    BACKGROUNDS,
    derived_stats,
    grant_xp,
    record_action,
    refresh_prediction,
    set_background,
    stat_multiplier,
)


def test_background_adds_identity_and_starting_bonus():
    state = create_new_game("Tester")
    set_background(state, "soldier")
    assert state.player.background_id == "soldier"
    assert state.player.profession == "soldier"
    assert state.player.stats["strength"] == 6
    assert state.player.gold == 60


def test_leveling_awards_stat_and_skill_points():
    state = create_new_game("Tester")
    gained = grant_xp(state, 100)
    assert gained == 1
    assert state.player.level == 2
    assert state.player.stat_points == 3
    assert state.player.skill_points == 1
    assert state.player.max_hp == 110


def test_stats_amplify_resonance_but_actions_create_it():
    state = create_new_game("Tester")
    assert stat_multiplier(state, "life") == 1.0
    record_action(state, "heal")
    assert state.divine_affinity["life"] > 0


def test_prediction_is_not_locked():
    state = create_new_game("Tester")
    for _ in range(10):
        record_action(state, "heal")
    first = refresh_prediction(state)[0]
    for _ in range(20):
        record_action(state, "sneak")
    second = refresh_prediction(state)[0]
    assert first == "life"
    assert second == "shadows"


def test_derived_stats_exist():
    state = create_new_game("Tester")
    stats = derived_stats(state)
    assert stats["attack"] > 0
    assert stats["defense"] > 0
    assert stats["evasion"] > 0
    assert stats["healing_power"] > 0
    assert stats["crit_chance"] > 0
    assert stats["carry_capacity"] > 0


def test_background_catalog_is_data_driven():
    assert {"soldier", "thief", "scholar", "healer", "merchant", "craftsperson", "wanderer"}.issubset(BACKGROUNDS)
