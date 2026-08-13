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

from game.ui import clear, menu, pause, title

STORY_ROOT = Path(__file__).resolve().parent


class StoryError(ValueError):
    pass


class StoryEngine:
    def __init__(self, state, manager: SaveManager | None = None) -> None:
        self.state = state
        self.manager = manager
        self.chapters: dict[int, dict[str, Any]] = {}

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
        if not data.get("beats"):
            raise StoryError(f"Story chapter {chapter} has no beats")
        self.chapters[chapter] = data
        return data

    def _nodes(self, chapter: int) -> dict[str, dict[str, Any]]:
        return {str(node["id"]): node for node in self._load_chapter(chapter).get("beats", [])}

    def _node(self, node_id: str) -> dict[str, Any]:
        nodes = self._nodes(self.state.chapter)
        try:
            return nodes[node_id]
        except KeyError as exc:
            raise StoryError(f"Story node not found: {node_id}") from exc

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
            elif key == "gold":
                self.state.player.gold += int(values)
            elif key == "xp":
                self.state.player.add_xp(int(values))
            elif key == "checkpoint" and values:
                self.state.checkpoint_node = self.state.current_story_node
            elif key == "actions":
                for action in values:
                    record_action(self.state, str(action))
        refresh_prediction(self.state)

    def _apply_items(self, values: dict[str, Any]) -> None:
        inventory = self.state.player.inventory
        for entry in values.get("add", []):
            item_id = str(entry["id"])
            quantity = max(0, int(entry.get("quantity", 1)))
            for _ in range(quantity):
                if item_id not in inventory or item_id in {"health-potion"}:
                    inventory.append(item_id)
        for entry in values.get("remove", []):
            item_id = str(entry["id"])
            quantity = max(0, int(entry.get("quantity", 1)))
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

    def _valid_target(self, next_node: str | None) -> str | None:
        if not next_node:
            return None
        if next_node == "chapter_02":
            return next_node
        if next_node not in self._nodes(self.state.chapter):
            raise StoryError(f"Story points to unknown node '{next_node}' in chapter {self.state.chapter}")
        return next_node

    def _transition(self, next_node: str | None) -> bool:
        next_node = self._valid_target(next_node)
        if not next_node:
            return False
        if next_node == "chapter_02":
            self.state.chapter = 2
            self.state.current_story_node = "chapter_02"
            clear()
            title()
            print("\nCHAPTER 1 COMPLETE\n")
            print("Ashenfall survived the night.")
            print("But one of the twelve bells is silent, and twenty-seven people are still missing.")
            print("\nChapter 2 is coming. Your Chapter 1 checkpoint is safe.")
            if self.manager:
                self.manager.save(1, self.state)
            pause()
            return False
        self.state.current_story_node = next_node
        return True

    def run(self) -> None:
        """Run the handcrafted story until Chapter 1 ends or a later chapter is unavailable."""
        while True:
            node = self._node(self.state.current_story_node)
            self._show_node(node)
            self._apply_effects(node.get("effects"))

            if node.get("checkpoint") or node.get("type") == "checkpoint":
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
                    record_action(self.state, action)
                    self.state.history.append(f"action:{node['id']}:{action}")
                    next_node = (node.get("action_next") or {}).get(action, node.get("next"))
            else:
                next_node = node.get("next")

            if not self._transition(next_node):
                return


def run_new_game(manager: SaveManager, state) -> None:
    StoryEngine(state, manager).run()
