"""Chapter 1 gameplay hooks for the reusable combat/progression systems."""

from __future__ import annotations

from dataclasses import dataclass

from rpg_core.combat import Enemy, resolve_combat
from rpg_core.models import GameState
from rpg_core.progression import derived_stats, spend_stat_point
from rpg_core.skills import available_skills, learn_skill


CHAPTER1_ENCOUNTERS = {
    "tower_guardian": Enemy(
        id="tower_guardian",
        name="Hollow Bellkeeper",
        max_hp=42,
        attack=11,
        defense=4,
        crit_chance=0.10,
        xp_reward=120,
        gold_reward=18,
        actions=("guard",),
    ),
    "bell_shadow": Enemy(
        id="bell_shadow",
        name="Bell Shadow",
        max_hp=30,
        attack=9,
        defense=2,
        evasion=0.15,
        crit_chance=0.12,
        xp_reward=90,
        gold_reward=10,
        actions=("shadow",),
    ),
}


@dataclass(frozen=True)
class LevelUpSummary:
    levels_gained: int
    stat_points: int
    skill_points: int


def resolve_chapter1_encounter(state: GameState, encounter_id: str, *, seed: int | None = None):
    enemy = CHAPTER1_ENCOUNTERS[encounter_id]
    result = resolve_combat(state, enemy, seed=seed)
    state.history.append(f"chapter1_encounter:{encounter_id}:{result.outcome}")
    return result


def spend_available_stat_point(state: GameState, stat: str) -> None:
    spend_stat_point(state, stat)
    state.history.append(f"stat_point_spent:{stat}")


def learn_available_skill(state: GameState, skill_id: str) -> int:
    rank = learn_skill(state, skill_id)
    state.history.append(f"skill_learned:{skill_id}:{rank}")
    return rank


def chapter1_progression_snapshot(state: GameState) -> dict[str, object]:
    return {
        "level": state.player.level,
        "xp": state.player.xp,
        "xp_to_next": state.player.xp_to_next_level(),
        "stat_points": state.player.stat_points,
        "skill_points": state.player.skill_points,
        "stats": dict(state.player.stats),
        "derived": derived_stats(state),
        "available_skills": [skill.id for skill in available_skills(state)],
        "resonance": dict(state.divine_affinity),
    }
