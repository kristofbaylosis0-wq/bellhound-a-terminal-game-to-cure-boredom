from __future__ import annotations

import json
from pathlib import Path

from rpg_core.player_service import create_new_game
from story.engine import StoryEngine


CHAPTER = Path(__file__).parents[1] / "story" / "chapters" / "chapter_01.json"


def test_chapter_one_json_is_valid_and_has_a_complete_node_graph() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    beats = {node["id"]: node for node in data["beats"]}
    assert data["mode"] == "handcrafted"
    assert data["ai_required"] is False
    assert "ch1_arrival" in beats
    assert "ch1_checkpoint" in beats

    for node in beats.values():
        for target in [node.get("next")]:
            if target and target != "chapter_02":
                assert target in beats, (node["id"], target)
        for choice in node.get("choices", []):
            target = choice.get("next")
            if target and target != "chapter_02":
                assert target in beats, (node["id"], target)
        for target in (node.get("action_next") or {}).values():
            if target and target != "chapter_02":
                assert target in beats, (node["id"], target)
        combat = node.get("combat") or {}
        for target_key in ("on_win", "on_loss", "on_flee"):
            target = combat.get(target_key)
            if target and target != "chapter_02":
                assert target in beats, (node["id"], target)


def test_story_engine_can_start_new_chapter_one_game() -> None:
    state = create_new_game("Test Hero")
    engine = StoryEngine(state)
    assert state.current_story_node == "ch1_arrival"
    assert engine._node("ch1_arrival")["title"] == "Ashenfall at Dusk"
