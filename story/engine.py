"""Deterministic story runner for the handcrafted RPG campaign.

The engine deliberately knows nothing about AI providers. A chapter is a data
file containing scenes, choices, effects, and transitions. That makes the
opening campaign fully playable offline once installed.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rpg_core.progression import record_action, refresh_prediction
from rpg_core.save_manager import SaveManager

from game.ui import clear, menu, pause, terminal_input, title

STORY_ROOT = Path(__file__).resolve().parent


class StoryError(ValueError):
    pass


class StoryEngine:
    def __init__(self, state, manager: SaveManager | None = None) -> None:
        self.state = state
        self.manager = manager
        self.chapters: dict[int, dict[str, Any]] = {}
        self._load_chapter(1)

    def _load_chapter(self, chapter: int) -> dict[str, Any]:
        if chapter in self.chapters:
            return self.chapters[chapter]
        path = STORY_ROOT / "chapters" / f"chapter_{chapter:02d}.json"
        if not path.exists():
            raise StoryError(f"Story chapter {chapter} is not installed")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StoryError(f"Could not load chapter {chapter}: {exc}") from exc
        self.chapters[chapter] = data
        return data

    def _node(self, node_id: str) -> dict[str, Any]:
        chapter = self._load_chapter(self.state.chapter)
        for node in chapter.get("beats", []):
            if node.get("id") == node_id:
                return node
        raise StoryError(f"Story node not found: {node_id}")

    def _apply_effects(self, effects: dict[str, Any] | None) -> None:
        if not effects:
            return
        for key, values in effects.items():
            if key == "divine_affinity":
                for domain, amount in values.items():
                    record_action(self.state, f"story_{domain}", outcomes={domain: float(amount)})
            elif key in {"world_flags", "flags"}:
                self.state.world_flags.update(values)
            elif key == "relationships":
                for person, amount in values.items():
                    self.state.relationships[person] = self.state.relationships.get(person, 0) + int(amount)
            elif key == "faction_reputation":
                for faction, amount in values.items():
                    self.state.faction_reputation[faction] = self.state.faction_reputation.get(faction, 0) + int(amount)
            elif key == "quest_states":
                self.state.quest_states.update({str(k): str(v) for k, v in values.items()})
            elif key == "discovered_lore":
                for lore in values:
                    if lore not in self.state.discovered_lore:
                        self.state.discovered_lore.append(lore)
            elif key == "items":
                self._apply_items(values)
            elif key == "chapter":
                self.state.chapter = int(values)
            elif key == "checkpoint" and values:
                self.state.checkpoint_node = self.state.current_story_node
            else:
                self.state.history.append(f"story_effect_ignored:{key}")
        refresh_prediction(self.state)

    def _apply_items(self, values: dict[str, Any]) -> None:
        inventory = self.state.player.inventory
        for entry in values.get("add", []):
            item_id = str(entry["id"])
            quantity = int(entry.get("quantity", 1))
            inventory.extend([item_id] * max(0, quantity))
        for entry in values.get("remove", []):
            item_id = str(entry["id"])
            quantity = int(entry.get("quantity", 1))
            for _ in range(quantity):
                if item_id in inventory:
                    inventory.remove(item_id)

    def _show_node(self, node: dict[str, Any]) -> None:
        clear()
        title()
        print(f"\n{node.get('title', 'Story')}\n")
        for paragraph in node.get("text", []):
            print(paragraph)
            print()

    def _choose(self, choices: list[dict[str, Any]]) -> dict[str, Any]:
        labels = [str(choice.get("text", choice.get("id", "Choice"))) for choice in choices]
        selected = menu("WHAT DO YOU DO?", labels)
        return choices[selected]

    def _actions(self, actions: list[str]) -> str:
        labels = [str(action).replace("_", " ").title() for action in actions]
        labels.append("Continue")
        selected = menu("EXPLORE", labels)
        if selected == len(actions):
            return "continue"
        return actions[selected]

    def _transition(self, next_node: str | None) -> bool:
        if not next_node:
            return False
        if next_node == "chapter_02":
            self.state.chapter = 2
            self.state.current_story_node = "chapter_02"
            clear(); title()
            print("\nCHAPTER 1 COMPLETE\n")
            print("The road beyond Ashenfall is waiting.")
            print("Chapter 2 is not installed yet.")
            pause()
            return False
        self.state.current_story_node = next_node
        return True

    def run(self) -> None:
        """Run until the current handcrafted chapter reaches an unavailable chapter."""
        while True:
            node = self._node(self.state.current_story_node)
            self._show_node(node)
            self._apply_effects(node.get("effects"))

            if node.get("type") == "checkpoint":
                self.state.checkpoint_node = node["id"]
                if self.manager:
                    self.manager.save(1, self.state)
                print("Checkpoint saved.")
                pause()

            choices = node.get("choices") or []
            actions = node.get("actions") or []
            if choices:
                choice = self._choose(choices)
                self._apply_effects(choice.get("effects"))
                self.state.history.append(f"choice:{node['id']}:{choice.get('id', 'unknown')}")
                next_node = choice.get("next")
            elif actions:
                action = self._actions(actions)
                if action == "continue":
                    next_node = node.get("next")
                else:
                    # Actions are deliberately lightweight in Chapter 1: they
                    # record behavior and return to the same node unless the
                    # node provides an explicit transition for that action.
                    record_action(self.state, action)
                    self.state.history.append(f"action:{node['id']}:{action}")
                    next_node = node.get("next")
            else:
                next_node = node.get("next")

            if not self._transition(next_node):
                return


def run_new_game(manager: SaveManager, state) -> None:
    """Enter the handcrafted campaign with an already-created player state."""
    StoryEngine(state, manager).run()
