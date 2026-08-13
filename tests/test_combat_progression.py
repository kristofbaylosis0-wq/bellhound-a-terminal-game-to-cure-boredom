import random

import pytest

from rpg_core.combat import (
    CombatantState,
    Enemy,
    calculate_damage,
    perform_enemy_attack,
    player_attack_power,
    player_defense,
    resolve_combat,
)
from rpg_core.player_service import create_new_game
from rpg_core.skills import available_skills, learn_skill, skill_rank
from rpg_core.progression import grant_xp


def test_damage_has_a_minimum_and_critical_multiplier():
    assert calculate_damage(10, 100) == 1
    assert calculate_damage(20, 5, crit=True, multiplier=2.0) == 30


def test_enemy_attack_respects_defense():
    state = create_new_game("Hero")
    player = CombatantState("Hero", 100, 100)
    enemy = Enemy("rat", "Rat", 20, 12, 1)
    damage, _crit, hit = perform_enemy_attack(state, enemy, player, random.Random(1))
    assert hit
    assert damage >= 1
    assert player.hp == 100 - damage
    assert player_defense(state) > 0


def test_combat_victory_awards_xp_and_gold():
    state = create_new_game("Hero")
    enemy = Enemy("slime", "Slime", 1, 1, 0, xp_reward=100, gold_reward=7)
    result = resolve_combat(state, enemy, seed=1)
    assert result.outcome == "victory"
    assert state.player.xp < 100
    assert state.player.level == 2
    assert state.player.gold == 32
    assert player_attack_power(state) > 0


def test_combat_defeat_reduces_hp_and_does_not_award_rewards():
    state = create_new_game("Hero")
    state.player.stats["strength"] = 1
    enemy = Enemy("ogre", "Ogre", 999, 999, 0, xp_reward=100, gold_reward=50)
    result = resolve_combat(state, enemy, seed=1, max_rounds=2)
    assert result.outcome == "defeat"
    assert state.player.hp == 0
    assert state.player.gold == 25


def test_skill_learning_consumes_one_point_and_records_rank():
    state = create_new_game("Hero")
    state.player.background_id = "soldier"
    state.player.skill_points = 1
    assert any(skill.id == "power_strike" for skill in available_skills(state))
    assert learn_skill(state, "power_strike") == 1
    assert skill_rank(state, "power_strike") == 1
    assert state.player.skill_points == 0
    assert "power_strike" in state.player.discovered_abilities


def test_skill_cannot_exceed_rank_or_points():
    state = create_new_game("Hero")
    state.player.background_id = "soldier"
    with pytest.raises(ValueError):
        learn_skill(state, "power_strike")
    state.player.skill_points = 1
    assert learn_skill(state, "power_strike") == 1
    with pytest.raises(ValueError):
        learn_skill(state, "power_strike")


def test_xp_can_cross_multiple_levels_without_losing_remainder():
    state = create_new_game("Hero")
    gained = grant_xp(state, 1000)
    assert gained >= 3
    assert state.player.xp >= 0
    assert state.player.stat_points == gained * 3
    assert state.player.skill_points == gained
