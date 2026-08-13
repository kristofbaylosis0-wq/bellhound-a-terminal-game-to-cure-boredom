"""Subtle, replayable events driven by hidden divine resonance."""

from __future__ import annotations

from dataclasses import dataclass
import random

from .models import GameState


@dataclass(frozen=True)
class ResonanceEvent:
    id: str
    domain: str
    threshold: float
    chance: float
    text: str
    flag: str


EVENTS = (
    ResonanceEvent("life_corpse_twitch", "life", 12, 0.08, "A nearby corpse's fingers twitch once, then become still.", "seen_life_corpse"),
    ResonanceEvent("life_flower_bloom", "life", 20, 0.10, "A pale flower opens beside your boot despite the season.", "seen_life_bloom"),
    ResonanceEvent("shadow_ignored", "shadows", 12, 0.08, "Two people nearby continue talking without noticing you are standing directly beside them.", "seen_shadow_ignored"),
    ResonanceEvent("shadow_reflection", "shadows", 20, 0.06, "Your reflection turns a fraction later than you do.", "seen_shadow_reflection"),
    ResonanceEvent("knowledge_memory", "knowledge", 12, 0.07, "You suddenly know the name of a ruined street you have never visited.", "seen_knowledge_memory"),
    ResonanceEvent("war_spar", "war", 12, 0.08, "A stranger's hand drifts toward a weapon when you pass.", "seen_war_tension"),
    ResonanceEvent("death_candle", "death", 12, 0.09, "A candle beside you extinguishes although there is no wind.", "seen_death_candle"),
    ResonanceEvent("storm_static", "storms", 12, 0.08, "The air prickles around your hands while the sky is clear.", "seen_storm_static"),
    ResonanceEvent("sea_distant_salt", "sea", 12, 0.06, "You smell salt water miles from the coast.", "seen_sea_scent"),
    ResonanceEvent("fate_coin", "fate", 12, 0.07, "A coin falls heads-up at your feet even though nobody threw it.", "seen_fate_coin"),
    ResonanceEvent("freedom_lock", "freedom", 12, 0.07, "A locked door clicks open as you reach for it.", "seen_freedom_lock"),
    ResonanceEvent("creation_splinter", "creation", 12, 0.07, "A broken object nearby shifts until its pieces almost fit together.", "seen_creation_splinter"),
    ResonanceEvent("forgotten_ui", "forgotten", 10, 0.035, "For an instant, the world feels like it skipped a frame.", "seen_forgotten_glitch"),
    ResonanceEvent("forgotten_wrong_name", "forgotten", 22, 0.05, "Someone calls you by a name you have never heard—and immediately apologizes.", "seen_forgotten_name"),
)


def roll_resonance_event(state: GameState, *, rng: random.Random | None = None) -> ResonanceEvent | None:
    rng = rng or random.Random(state.random_seed)
    candidates = []
    for event in EVENTS:
        if state.divine_affinity.get(event.domain, 0.0) < event.threshold:
            continue
        if state.world_flags.get(event.flag):
            continue
        if rng.random() <= event.chance:
            candidates.append(event)
    if not candidates:
        return None
    event = rng.choice(candidates)
    state.world_flags[event.flag] = True
    state.history.append(f"resonance_event:{event.id}")
    return event
