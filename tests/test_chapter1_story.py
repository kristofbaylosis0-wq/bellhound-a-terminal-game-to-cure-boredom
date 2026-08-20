from __future__ import annotations

import json
from pathlib import Path

from rpg_core.items import DEFAULT_ITEMS
from rpg_core.player_service import create_new_game
from story.engine import StoryEngine


CHAPTER = Path(__file__).parents[1] / "story" / "chapters" / "chapter_01.json"


def test_chapter_one_json_is_valid_and_has_a_complete_node_graph() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    beats = {node["id"]: node for node in data["beats"]}
    assert data["mode"] == "handcrafted"
    assert data["ai_required"] is False
    assert data["target_playtime_minutes"] == 60
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
        for route in node.get("routes", []):
            target = route.get("next")
            if target and target != "chapter_02":
                assert target in beats, (node["id"], target)
        fallback = node.get("fallback")
        if fallback and fallback != "chapter_02":
            assert fallback in beats, (node["id"], fallback)
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


def test_black_iron_key_gate_has_item_and_background_routes() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    gate = next(node for node in data["beats"] if node["id"] == "ch1_gate")
    choices = {choice["id"]: choice for choice in gate["choices"]}

    assert choices["use_key"]["conditions"] == {"has_items": ["black-iron-key"]}
    assert choices["scholar_reading"]["conditions"] == {"backgrounds": ["scholar"]}
    assert choices["thief_bypass"]["conditions"] == {"backgrounds": ["thief"]}
    assert choices["craftsperson_tune"]["conditions"] == {"backgrounds": ["craftsperson"]}
    assert choices["soldier_force"]["conditions"] == {"backgrounds": ["soldier"]}


def test_story_engine_evaluates_inventory_and_background_conditions() -> None:
    state = create_new_game("Test Hero", background_id="wanderer")
    engine = StoryEngine(state)
    assert not engine._condition_met({"has_items": ["black-iron-key"]})
    assert not engine._condition_met({"backgrounds": ["scholar"]})

    state.player.inventory.append("black-iron-key")
    state.player.background_id = "scholar"
    assert engine._condition_met({"has_items": ["black-iron-key"]})
    assert engine._condition_met({"backgrounds": ["scholar"]})


def test_first_underground_encounter_is_real_and_rewards_echo_shard() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    encounter = next(node for node in data["beats"] if node["id"] == "ch1_first_encounter")
    victory = next(node for node in data["beats"] if node["id"] == "ch1_hound_victory")

    assert encounter["type"] == "combat"
    assert encounter["combat"]["hp"] == 42
    assert encounter["combat"]["reward_xp"] > 0
    assert encounter["combat"]["on_win"] == "ch1_hound_victory"
    assert {item["id"] for item in victory["effects"]["items"]["add"]} == {"echo-shard"}
    assert "echo-shard" in DEFAULT_ITEMS

    state = create_new_game("Test Hero")
    StoryEngine(state)._apply_effects(victory["effects"])
    assert "echo-shard" in state.player.inventory
    assert state.world_flags["memory_hound_defeated"] is True
    assert "seventh_not_first" in state.evidence


def test_relationship_and_evidence_conditions_are_stateful() -> None:
    state = create_new_game("Test Hero")
    engine = StoryEngine(state)

    assert not engine._condition_met({"evidence": ["black_iron_key"]})
    assert not engine._condition_met({"relationship_states": {"mira": "trusted"}})

    state.evidence.append("black_iron_key")
    state.relationship_states["mira"] = "trusted"
    assert engine._condition_met({"evidence": ["black_iron_key"]})
    assert engine._condition_met({"relationship_states": {"mira": "trusted"}})


def test_mira_reaction_has_three_persistent_relationship_outcomes() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    reaction = next(node for node in data["beats"] if node["id"] == "ch1_mira_reaction")
    choice_ids = {choice["id"] for choice in reaction["choices"]}
    assert choice_ids == {"share_evidence", "hold_back", "blame_her"}

    states = {
        choice["effects"]["relationship_states"]["mira"]
        for choice in reaction["choices"]
    }
    assert states == {"trusted", "uncertain", "opposed"}

    share = next(choice for choice in reaction["choices"] if choice["id"] == "share_evidence")
    assert share["conditions"] == {"evidence": ["black_iron_key"]}


def test_three_dawns_routes_from_accumulated_state() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    dawn = next(node for node in data["beats"] if node["id"] == "ch1_dawn_split")

    state = create_new_game("Test Hero")
    engine = StoryEngine(state)
    state.relationship_states["mira"] = "trusted"
    state.evidence.append("mira_trusts_player")
    assert engine._route_next(dawn) == "ch1_dawn_mira"

    state.relationship_states.clear()
    state.evidence.clear()
    state.world_flags["official_investigation"] = True
    assert engine._route_next(dawn) == "ch1_dawn_crown"

    state.world_flags["memory_hound_escaped"] = True
    assert engine._route_next(dawn) == "ch1_dawn_hollow"


def test_three_dawn_rewards_are_distinct_and_persistent() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    nodes = {node["id"]: node for node in data["beats"]}
    state = create_new_game("Test Hero")
    engine = StoryEngine(state)

    engine._apply_effects(nodes["ch1_dawn_mira"]["effects"])
    assert state.world_flags["chapter1_dawn"] == "mira"
    assert "bellkeeper-seal" in state.player.inventory
    assert state.relationship_states["mira"] == "trusted"

    state = create_new_game("Test Hero")
    engine = StoryEngine(state)
    engine._apply_effects(nodes["ch1_dawn_crown"]["effects"])
    assert state.world_flags["chapter1_dawn"] == "crown"
    assert "crown-writ" in state.player.inventory

    state = create_new_game("Test Hero")
    engine = StoryEngine(state)
    engine._apply_effects(nodes["ch1_dawn_hollow"]["effects"])
    assert state.world_flags["chapter1_dawn"] == "hollow"
    assert "hollow-mark" in state.player.inventory
    assert state.relationship_states["mira"] == "opposed"


def test_chapter_one_has_an_expanded_investigation_arc() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    beats = {node["id"]: node for node in data["beats"]}
    assert len(beats) >= 39
    assert sum(node.get("type") == "combat" for node in beats.values()) >= 2

    before_midnight = beats["ch1_before_midnight"]
    actions = set(before_midnight["actions"])
    assert {"visit_market", "visit_tavern", "visit_scholar_quarter"}.issubset(actions)

    expanded_nodes = {
        "ch1_market_aftershock",
        "ch1_tavern_aftershock",
        "ch1_scholar_aftershock",
        "ch1_second_house",
        "ch1_footprint_encounter",
        "ch1_footprint_chamber",
        "ch1_footprint_victory",
    }
    assert expanded_nodes.issubset(beats)
    all_text = " ".join(" ".join(node.get("text", [])) for node in beats.values())
    assert "Nessa Vale" in all_text
    assert "Rowan" in all_text
    assert "Elian Marr" in all_text
    assert "Vesper Rill" in all_text


def test_every_major_path_has_an_extended_intermediate_scene() -> None:
    data = json.loads(CHAPTER.read_text(encoding="utf-8"))
    beats = {node["id"]: node for node in data["beats"]}

    mira = beats["ch1_mira_reaction"]
    assert '"next":"ch1_mira_investigation"' in json.dumps(mira, ensure_ascii=False, separators=(",", ":"))

    tower = beats["ch1_tower_entry"]
    tower_targets = {choice.get("next") for choice in tower["choices"]}
    assert "ch1_stairwell_choice" in tower_targets

    abandon = beats["ch1_abandon_tower"]
    abandon_targets = {choice.get("next") for choice in abandon["choices"]}
    assert "ch1_abandon_city" in abandon_targets

    guardian = beats["ch1_hollow_guardian"]
    guardian_targets = {choice.get("next") for choice in guardian["choices"]}
    assert "ch1_guardian_question" in guardian_targets

    required = {
        "ch1_mira_investigation",
        "ch1_mira_evidence",
        "ch1_stairwell_choice",
        "ch1_maintenance_alcove",
        "ch1_mira_echo",
        "ch1_abandon_city",
        "ch1_abandon_witness",
        "ch1_guardian_question",
    }
    assert required.issubset(beats)
