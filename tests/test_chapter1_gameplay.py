from rpg_core.player_service import create_new_game
from story.chapter1_gameplay import (
    CHAPTER1_ENCOUNTERS,
    chapter1_progression_snapshot,
    learn_available_skill,
    resolve_chapter1_encounter,
    spend_available_stat_point,
)


def test_chapter1_encounter_uses_reusable_combat_rules():
    state = create_new_game("Hero")
    result = resolve_chapter1_encounter(state, "bell_shadow", seed=2)
    assert result.outcome in {"victory", "defeat"}
    assert any("chapter1_encounter:bell_shadow" in entry for entry in state.history)


def test_chapter1_progression_snapshot_exposes_player_progress_without_revealing_god():
    state = create_new_game("Hero")
    snapshot = chapter1_progression_snapshot(state)
    assert snapshot["level"] == 1
    assert "xp_to_next" in snapshot
    assert "stat_points" in snapshot
    assert "skill_points" in snapshot
    assert "resonance" in snapshot
    assert "god" not in snapshot


def test_chapter1_stat_and_skill_hooks_use_authoritative_state():
    state = create_new_game("Hero")
    state.player.stat_points = 1
    spend_available_stat_point(state, "strength")
    assert state.player.stats["strength"] == 6
    assert state.player.stat_points == 0

    state.player.background_id = "soldier"
    state.player.skill_points = 1
    learn_available_skill(state, "power_strike")
    assert state.player.skills["power_strike"] == 1


def test_chapter1_encounters_have_rewards():
    assert all(enemy.xp_reward > 0 and enemy.gold_reward >= 0 for enemy in CHAPTER1_ENCOUNTERS.values())
