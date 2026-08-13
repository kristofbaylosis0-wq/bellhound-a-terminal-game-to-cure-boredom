"""Persistent achievement definitions and unlock logic for the RPG."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class Achievement:
    id: str
    name: str
    description: str
    hidden: bool = False


ACHIEVEMENTS: dict[str, Achievement] = {
    "first_steps": Achievement("first_steps", "First Steps", "Begin your journey in the world."),
    "name_in_stone": Achievement("name_in_stone", "Name in Stone", "Discover your first ancient inscription."),
    "seventh_silence": Achievement("seventh_silence", "The Seventh Silence", "Witness the first bell failure."),
    "twenty_seven": Achievement("twenty_seven", "The Twenty-Seven", "Begin the investigation into the vanished citizens."),
    "below_the_bell": Achievement("below_the_bell", "Below the Bell", "Enter the hidden depths beneath a bell tower."),
    "first_echo": Achievement("first_echo", "First Echo", "Experience your first divine memory."),
    "checkpoint": Achievement("checkpoint", "Safe Enough", "Reach and save at a story checkpoint."),
    "merchant": Achievement("merchant", "Fair Trade", "Complete your first purchase or sale."),
    "blacksmith": Achievement("blacksmith", "Make It Yourself", "Forge or repair an item yourself."),
    "trained": Achievement("trained", "Practice Makes Power", "Complete your first training session."),
    "resonance": Achievement("resonance", "Something Within", "Cause a divine resonance prediction to emerge."),
    "secret": Achievement("secret", "You Weren't Supposed To See That", "Discover a hidden anomaly."),
    "survivor": Achievement("survivor", "Still Standing", "Recover from a dangerous encounter and continue the story."),
    "mercy": Achievement("mercy", "Mercy", "Choose mercy when violence was available."),
    "reckless": Achievement("reckless", "No Going Back", "Make a deliberately destructive choice."),
    "chapter_one": Achievement("chapter_one", "The First Bell", "Complete Chapter 1."),
    "collector": Achievement("collector", "Curious Soul", "Discover five pieces of lore."),
}


_TRIGGER_RULES: dict[str, Callable[[Any], bool]] = {
    "first_steps": lambda s: s.player.level >= 1,
    "name_in_stone": lambda s: bool(s.discovered_lore),
    "seventh_silence": lambda s: bool(s.world_flags.get("bell_07_silent")),
    "twenty_seven": lambda s: bool(s.world_flags.get("twenty_seven_missing")),
    "below_the_bell": lambda s: bool(s.world_flags.get("entered_below_bell")),
    "first_echo": lambda s: bool(s.world_flags.get("first_divine_echo")),
    "checkpoint": lambda s: bool(s.checkpoint_node and s.checkpoint_node != "ch1_arrival"),
    "resonance": lambda s: s.player.divine_prediction not in {"", "undetermined"},
    "secret": lambda s: bool(s.world_flags.get("saw_bell_anomaly") or s.world_flags.get("heard_second_name")),
    "survivor": lambda s: bool(s.world_flags.get("survived_encounter")),
    "mercy": lambda s: any("mercy" in h for h in s.history),
    "reckless": lambda s: any(x in " ".join(s.history) for x in ("betray", "unnecessary_kill", "destroy")),
    "chapter_one": lambda s: bool(s.world_flags.get("chapter_01_complete")),
    "collector": lambda s: len(s.discovered_lore) >= 5,
}


def ensure_state(state: Any) -> None:
    if not hasattr(state, "achievements"):
        state.achievements = []


def unlock(state: Any, achievement_id: str) -> bool:
    if achievement_id not in ACHIEVEMENTS:
        raise ValueError(f"Unknown achievement: {achievement_id}")
    ensure_state(state)
    if achievement_id in state.achievements:
        return False
    state.achievements.append(achievement_id)
    return True


def evaluate(state: Any) -> list[Achievement]:
    ensure_state(state)
    unlocked: list[Achievement] = []
    for achievement_id, rule in _TRIGGER_RULES.items():
        if achievement_id not in state.achievements and rule(state):
            unlock(state, achievement_id)
            unlocked.append(ACHIEVEMENTS[achievement_id])
    return unlocked


def progress(state: Any) -> dict[str, Any]:
    ensure_state(state)
    return {
        "unlocked": [ACHIEVEMENTS[item] for item in state.achievements if item in ACHIEVEMENTS],
        "total": len(ACHIEVEMENTS),
        "unlocked_count": len(state.achievements),
    }
