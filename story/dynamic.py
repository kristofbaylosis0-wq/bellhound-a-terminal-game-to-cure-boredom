"""Bounded AI-directed story mode.

The AI writes presentation and choice labels, but game state remains authoritative.
It cannot invent gods, mutate stats, award arbitrary items, or bypass chapter rules.
"""

from __future__ import annotations

import json
import re
from typing import Any

from rpg_ai.manager import AIManager
from rpg_ai.models import AIMessage, AIRequest
from rpg_ai.settings import load_settings

from game.ui import clear, menu, pause, title
from rpg_core.progression import record_action, refresh_prediction
from rpg_core.save_manager import SaveManager


ALLOWED_ACTIONS = (
    "explore", "research", "listen", "sneak", "negotiate", "intimidate",
    "protect", "heal", "pray", "risk", "mercy", "kill", "return",
)

CHAPTER_DIRECTION = (
    "You are directing Chapter 1 of Bellbound, set in Ashenfall.",
    "The central mystery is the Seventh Bell going silent and twenty-seven people disappearing.",
    "The player is a reincarnated divine being, but never reveal which god they are becoming.",
    "The twelve Bells and their gods are mysteries. Bell Five has special memory significance, but do not explain the final identity reveal.",
    "The chapter must eventually converge toward the underground bell chamber and the Hollow Bellkeeper encounter.",
    "Choices should reflect the player's actions, background, stats, relationships, quests, and current location.",
    "The AI may create connective scenes, dialogue, rumors, minor encounters, and choice wording.",
    "The AI may not invent arbitrary permanent game mechanics, change authoritative stats directly, grant unsupported items, reveal hidden god identity, or skip the chapter's core convergence.",
)


def _extract_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return json.loads(cleaned)


def _snapshot(state: Any) -> dict[str, Any]:
    return {
        "name": state.player.name,
        "level": state.player.level,
        "xp": state.player.xp,
        "hp": state.player.hp,
        "max_hp": state.player.max_hp,
        "stats": state.player.stats,
        "background": state.player.background_id,
        "profession": state.player.profession,
        "location": state.location,
        "chapter": state.chapter,
        "current_node": state.current_story_node,
        "checkpoint": state.checkpoint_node,
        "world_flags": state.world_flags,
        "quest_states": state.quest_states,
        "relationships": state.relationships,
        "faction_reputation": state.faction_reputation,
        "discovered_lore": state.discovered_lore[-12:],
        "recent_actions": state.player.action_history[-12:],
        "story_mode": state.story_mode,
        "resonance_summary": {
            key: round(value, 2)
            for key, value in state.divine_affinity.items()
            if value > 0
        },
    }


def _manager() -> AIManager:
    settings = load_settings()
    if not settings or not settings.provider or not settings.model:
        raise RuntimeError("Dynamic Story requires a configured AI provider and model.")
    from rpg_ai.models import ProviderConfig
    config = ProviderConfig(
        name=settings.provider,
        api_key=settings.api_key,
        base_url=settings.base_url,
        timeout=30.0,
    )
    manager = AIManager.from_config(config)
    manager.validate()
    return manager


def _director_prompt(state: Any, history: list[str]) -> str:
    snapshot = json.dumps(_snapshot(state), ensure_ascii=False)
    return "\n".join([
        *CHAPTER_DIRECTION,
        "",
        "AUTHORITATIVE GAME STATE:",
        snapshot,
        "",
        "RECENT DYNAMIC HISTORY:",
        json.dumps(history[-8:], ensure_ascii=False),
        "",
        "Return ONLY valid JSON with this exact shape:",
        '{"title":"...","narration":["..."],"choices":[{"text":"...","action":"..."},{"text":"...","action":"..."},{"text":"...","action":"..."}],"checkpoint":false,"end_chapter":false}',
        "Use exactly 3 choices. Each action MUST be one of: " + ", ".join(ALLOWED_ACTIONS) + ".",
        "Do not use markdown fences.",
        "Keep the scene concise enough for a terminal RPG but atmospheric.",
    ])


def _fallback_scene(state: Any) -> dict[str, Any]:
    return {
        "title": "Ashenfall Waits",
        "narration": [
            "The streets of Ashenfall are quieter than they should be.",
            "Somewhere beyond the roofs, the silent bell seems to wait for you.",
        ],
        "choices": [
            {"text": "Investigate the strange silence.", "action": "research"},
            {"text": "Listen for anything out of place.", "action": "listen"},
            {"text": "Move toward the bell tower.", "action": "explore"},
        ],
        "checkpoint": False,
        "end_chapter": False,
    }


def _safe_scene(payload: dict[str, Any]) -> dict[str, Any]:
    choices = payload.get("choices", [])
    if not isinstance(choices, list):
        choices = []
    clean_choices = []
    for choice in choices[:3]:
        if not isinstance(choice, dict):
            continue
        action = str(choice.get("action", "explore")).strip().lower()
        if action not in ALLOWED_ACTIONS:
            action = "explore"
        text = str(choice.get("text", "Continue"))[:180]
        clean_choices.append({"text": text or "Continue", "action": action})
    while len(clean_choices) < 3:
        clean_choices.append({"text": "Continue.", "action": "explore"})
    narration = [str(item)[:1200] for item in payload.get("narration", []) if str(item).strip()]
    return {
        "title": str(payload.get("title", "Ashenfall"))[:120],
        "narration": narration[:5] or ["The city waits."],
        "choices": clean_choices,
        "checkpoint": bool(payload.get("checkpoint", False)),
        "end_chapter": bool(payload.get("end_chapter", False)),
    }


def run_dynamic(manager: SaveManager, state: Any, *, save_slot: int) -> None:
    ai = _manager()
    history: list[str] = []
    turns = 0

    while turns < 40 and not (state.chapter != 1 or state.world_flags.get("dynamic_chapter_complete")):
        turns += 1
        request = AIRequest(
            messages=[
                AIMessage(role="system", content="You are the bounded story director for Bellbound."),
                AIMessage(role="user", content=_director_prompt(state, history)),
            ],
            model=load_settings().model,
            temperature=0.8,
            max_tokens=700,
        )
        try:
            response = ai.generate(request)
            scene = _safe_scene(_extract_json(response.text))
        except Exception:
            scene = _fallback_scene(state)

        clear()
        title()
        print(f"\n{scene['title']}\n")
        for paragraph in scene["narration"]:
            print(paragraph)
            print()

        if scene["checkpoint"]:
            state.checkpoint_node = state.current_story_node
            manager.save(save_slot, state)
            manager.autosave(state)
            print("Checkpoint saved.\n")
            pause()

        context = [scene["title"], *scene["narration"]]
        selected = menu("WHAT DO YOU DO?", [choice["text"] for choice in scene["choices"]], context=context)
        action = scene["choices"][selected]["action"]
        history.append(f"{scene['title']} -> {action}")
        record_action(state, action)
        refresh_prediction(state)
        state.history.append(f"dynamic:{turns}:{action}")

        # Core chapter progression remains deterministic regardless of AI prose.
        if action in {"explore", "research", "listen"} and turns >= 6:
            state.world_flags.setdefault("dynamic_discovered_under_bell", True)
        if state.world_flags.get("dynamic_discovered_under_bell") and turns >= 10:
            state.world_flags["dynamic_chapter_complete"] = True
            state.world_flags["chapter_01_complete"] = True
            manager.save(save_slot, state)
            manager.autosave(state)

        if scene["end_chapter"]:
            state.world_flags["dynamic_chapter_complete"] = True
            state.world_flags["chapter_01_complete"] = True
            manager.save(save_slot, state)
            manager.autosave(state)

    clear()
    title()
    print("\nDYNAMIC CHAPTER 1 COMPLETE\n")
    print("Your choices shaped the journey, but the Bellbound mystery remains unresolved.")
    print("The next chapter can continue from the same authoritative game state.")
    pause()
