"""Skill catalog and point-spending rules."""

from __future__ import annotations

from dataclasses import dataclass

from .models import GameState
from .progression import record_action


@dataclass(frozen=True)
class Skill:
    id: str
    name: str
    description: str
    max_rank: int = 5
    requires_background: str | None = None
    requires_skill: str | None = None


SKILLS = {
    "power_strike": Skill("power_strike", "Power Strike", "A heavier physical attack.", requires_background="soldier"),
    "guard_break": Skill("guard_break", "Guard Break", "A precise strike that weakens defensive enemies.", requires_background="soldier"),
    "shadowstep": Skill("shadowstep", "Shadowstep", "A stealth maneuver that improves evasion.", requires_background="thief"),
    "quick_hands": Skill("quick_hands", "Quick Hands", "Improves pickpocketing and item use.", requires_background="thief"),
    "field_medicine": Skill("field_medicine", "Field Medicine", "Restores more health outside combat.", requires_background="healer"),
    "arcane_research": Skill("arcane_research", "Arcane Research", "Reveals deeper lore and hidden clues.", requires_background="scholar"),
    "master_haggle": Skill("master_haggle", "Master Haggle", "Improves merchant prices.", requires_background="merchant"),
    "masterwork": Skill("masterwork", "Masterwork", "Improves crafted equipment.", requires_background="craftsperson"),
    "second_wind": Skill("second_wind", "Second Wind", "Once per encounter, recover from low health.", max_rank=3),
    "critical_eye": Skill("critical_eye", "Critical Eye", "Increases critical-hit potential.", max_rank=5),
}


def skill_rank(state: GameState, skill_id: str) -> int:
    return int(state.player.skills.get(skill_id, 0))


def can_learn(state: GameState, skill_id: str) -> bool:
    skill = SKILLS.get(skill_id)
    if skill is None:
        return False
    rank = skill_rank(state, skill_id)
    if rank >= skill.max_rank or state.player.skill_points <= 0:
        return False
    if skill.requires_background and state.player.background_id != skill.requires_background:
        return False
    if skill.requires_skill and skill_rank(state, skill.requires_skill) <= 0:
        return False
    return True


def learn_skill(state: GameState, skill_id: str) -> int:
    skill = SKILLS.get(skill_id)
    if skill is None:
        raise ValueError(f"Unknown skill: {skill_id}")
    if not can_learn(state, skill_id):
        raise ValueError(f"Cannot learn {skill.name}")
    new_rank = skill_rank(state, skill_id) + 1
    state.player.skills[skill_id] = new_rank
    state.player.discovered_abilities.append(skill_id)
    state.player.skill_points -= 1
    record_action(state, "learn_skill")
    return new_rank


def available_skills(state: GameState) -> list[Skill]:
    return [skill for skill in SKILLS.values() if can_learn(state, skill.id)]
