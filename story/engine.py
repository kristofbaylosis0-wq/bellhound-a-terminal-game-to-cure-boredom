"""Deterministic runner for the handcrafted RPG campaign."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rpg_core.achievements import evaluate
from rpg_core.player_service import grant_xp
from rpg_core.progression import can_use_action, record_action, refresh_prediction
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
        evaluate(self.state)

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
        if node_id not in nodes:
            raise StoryError(f"Story node not found: {node_id}")
        return nodes[node_id]

    def _condition_met(self, conditions: dict[str, Any] | None) -> bool:
        if not conditions:
            return True
        for action in conditions.get("actions", []):
            if not can_use_action(self.state, str(action)):
                return False
        for stat, minimum in conditions.get("min_stat", {}).items():
            if self.state.player.stats.get(str(stat), 0) < int(minimum):
                return False
        for flag in conditions.get("flags", []):
            if not self.state.world_flags.get(str(flag)):
                return False
        return True

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
                grant_xp(self.state, int(values))
            elif key == "checkpoint" and values:
                self.state.checkpoint_node = self.state.current_story_node
            elif key == "actions":
                for action in values:
                    record_action(self.state, str(action))
        refresh_prediction(self.state)
        newly_unlocked = evaluate(self.state)
        for achievement in newly_unlocked:
            self.state.history.append(f"achievement:{achievement.id}")

    def _apply_items(self, values: dict[str, Any]) -> None:
        inventory = self.state.player.inventory
        for entry in values.get("add", []):
            item_id = str(entry["id"])
            quantity = max(0, int(entry.get("quantity", 1)))
            for _ in range(quantity):
                if item_id not in inventory or item_id == "health-potion":
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
        valid = [choice for choice in choices if self._condition_met(choice.get("conditions"))]
        if not valid:
            raise StoryError("A story choice has no available options")
        labels = [str(choice.get("text", choice.get("id", "Choice"))) for choice in valid]
        selected = menu("WHAT DO YOU DO?", labels)
        return valid[selected]

    def _actions(self, node: dict[str, Any]) -> str:
        actions = [str(action) for action in node.get("actions", [])]
        available: list[str] = []
        for action in actions:
            if node.get("requires_background", {}).get(action):
                required = str(node["requires_background"][action])
                if self.state.player.background_id != required:
                    continue
            if node.get("requires_action", {}).get(action) and not can_use_action(self.state, action):
                continue
            available.append(action)
        available.append("continue")
        selected = menu(node.get("title", "Explore"), [a.replace("_", " ").title() for a in available])
        return available[selected]

    def _run_combat(self, combat: dict[str, Any]) -> str | None:
        enemy_hp = int(combat.get("hp", 50))
        enemy_attack = int(combat.get("attack", 8))
        enemy_defense = int(combat.get("defense", 3))
        player = self.state.player
        attack = int(player.stats.get("strength", 5) * 2 + player.level)
        defense = int(player.stats.get("endurance", 5) * 1.8 + player.level)

        while enemy_hp > 0 and player.hp > 0:
            clear(); title()
            print("\nCOMBAT\n")
            print(f"{player.name}: HP {player.hp}/{player.max_hp}")
            print(f"Enemy: HP {enemy_hp} | DEF {enemy_defense}\n")
            action = menu("COMBAT", ["Attack", "Defend", "Use Potion", "Flee"])
            defending = False
            if action == 0:
                damage = max(1, attack - enemy_defense)
                enemy_hp -= damage
                print(f"\nYou deal {damage} damage.")
            elif action == 1:
                defending = True
                print("\nYou brace yourself.")
            elif action == 2:
                if "health-potion" not in player.inventory:
                    print("\nYou have no health potions.")
                    pause(); continue
                player.inventory.remove("health-potion")
                player.hp = min(player.max_hp, player.hp + 30)
                record_action(self.state, "heal")
                print("\nYou recover 30 HP.")
            else:
                print("\nYou escape into the darkness.")
                pause()
                return combat.get("on_flee") or combat.get("on_loss")

            if enemy_hp <= 0:
                xp = int(combat.get("reward_xp", 0))
                gold = int(combat.get("reward_gold", 0))
                if xp:
                    grant_xp(self.state, xp)
                player.gold += max(0, gold)
                self.state.world_flags["survived_encounter"] = True
                record_action(self.state, "win_fight")
                self.state.history.append("combat:victory")
                evaluate(self.state)
                print(f"\nVictory! +{xp} XP, +{gold} gold.")
                pause()
                return combat.get("on_win")

            mitigation = defense // 2 if defending else defense // 4
            incoming = max(1, enemy_attack - mitigation)
            player.hp -= incoming
            print(f"The enemy hits you for {incoming}.")
            if player.hp <= 0:
                player.hp = 0
                self.state.history.append("combat:defeat")
                pause()
                return combat.get("on_loss")
            pause()
        return combat.get("on_win")

    def _transition(self, next_node: str | None) -> bool:
        if not next_node:
            return False
        if next_node == "chapter_02":
            self.state.world_flags["chapter_01_complete"] = True
            evaluate(self.state)
            self.state.chapter = 2
            self.state.current_story_node = "chapter_02"
            clear(); title()
            print("\nCHAPTER 1 COMPLETE\n")
            print("Ashenfall survived the night.")
            print("One bell is silent. Twenty-seven people are still missing.")
            print("\nYour Chapter 1 checkpoint is safe.")
            if self.manager:
                self.manager.save(1, self.state)
            pause()
            return False
        if next_node not in self._nodes(self.state.chapter):
            raise StoryError(f"Story points to unknown node '{next_node}' in chapter {self.state.chapter}")
        self.state.current_story_node = next_node
        return True

    def run(self) -> None:
        while True:
            node = self._node(self.state.current_story_node)
            self._show_node(node)
            if node.get("type") == "dungeon_entry":
                self.state.world_flags["entered_below_bell"] = True
            self._apply_effects(node.get("effects"))
            if node.get("checkpoint") or node.get("type") == "checkpoint":
                self.state.checkpoint_node = node["id"]
                if self.manager:
                    self.manager.save(1, self.state)
                evaluate(self.state)
                print("Checkpoint saved.")
                pause()
            combat = node.get("combat")
            if combat:
                next_node = self._run_combat(combat)
                if not self._transition(next_node):
                    return
                continue
            choices = node.get("choices") or []
            actions = node.get("actions") or []
            if choices:
                choice = self._choose(choices)
                self._apply_effects(choice.get("effects"))
                self.state.history.append(f"choice:{node['id']}:{choice.get('id', 'unknown')}")
                next_node = choice.get("next")
            elif actions:
                action = self._actions(node)
                if action == "continue":
                    next_node = node.get("next")
                else:
                    record_action(self.state, action)
                    self.state.history.append(f"action:{node['id']}:{action}")
                    next_node = (node.get("action_next") or {}).get(action, node.get("next"))
                    evaluate(self.state)
            else:
                next_node = node.get("next")
            if not self._transition(next_node):
                return


def run_new_game(manager: SaveManager, state) -> None:
    StoryEngine(state, manager).run()
