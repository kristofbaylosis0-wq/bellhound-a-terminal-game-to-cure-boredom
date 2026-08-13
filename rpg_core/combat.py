"""Reusable deterministic combat rules for Bellbound."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from .models import GameState
from .progression import derived_stats, grant_xp, record_action


@dataclass(frozen=True)
class Enemy:
    id: str
    name: str
    max_hp: int
    attack: int
    defense: int
    evasion: float = 0.0
    crit_chance: float = 0.05
    crit_multiplier: float = 1.5
    xp_reward: int = 0
    gold_reward: int = 0
    actions: tuple[str, ...] = ()
    weakness: str | None = None


@dataclass
class CombatantState:
    name: str
    hp: int
    max_hp: int
    defending: bool = False
    stunned: int = 0
    poisoned: int = 0


@dataclass
class CombatResult:
    outcome: str
    rounds: int
    damage_dealt: int = 0
    damage_taken: int = 0
    xp_reward: int = 0
    gold_reward: int = 0
    flee_attempts: int = 0
    critical_hits: int = 0
    history: list[str] = field(default_factory=list)


def player_attack_power(state: GameState) -> float:
    return float(derived_stats(state)["attack"])


def player_defense(state: GameState) -> float:
    return float(derived_stats(state)["defense"])


def player_evasion(state: GameState) -> float:
    return min(0.75, float(derived_stats(state)["evasion"]) / 100.0)


def player_crit_chance(state: GameState) -> float:
    return min(0.75, float(derived_stats(state)["crit_chance"]) / 100.0)


def calculate_damage(attack: float, defense: float, *, crit: bool = False, multiplier: float = 1.5) -> int:
    base = max(1.0, attack - defense)
    return max(1, int(round(base * (multiplier if crit else 1.0))))


def roll_hit(rng: random.Random, accuracy: float, evasion: float) -> bool:
    return rng.random() <= max(0.05, min(0.99, 1.0 - evasion + accuracy))


def roll_critical(rng: random.Random, chance: float) -> bool:
    return rng.random() < max(0.0, min(0.95, chance))


def enemy_from_dict(data: dict) -> Enemy:
    return Enemy(
        id=str(data.get("id", "enemy")),
        name=str(data.get("name", "Enemy")),
        max_hp=max(1, int(data.get("hp", data.get("max_hp", 50)))),
        attack=max(1, int(data.get("attack", 8))),
        defense=max(0, int(data.get("defense", 3))),
        evasion=max(0.0, float(data.get("evasion", 0.0))),
        crit_chance=max(0.0, float(data.get("crit_chance", 0.05))),
        crit_multiplier=max(1.0, float(data.get("crit_multiplier", 1.5))),
        xp_reward=max(0, int(data.get("reward_xp", data.get("xp_reward", 0)))),
        gold_reward=max(0, int(data.get("reward_gold", data.get("gold_reward", 0)))),
        actions=tuple(str(action) for action in data.get("actions", ())),
        weakness=data.get("weakness"),
    )


def perform_player_attack(state: GameState, enemy: CombatantState, rng: random.Random) -> tuple[int, bool, bool]:
    if not roll_hit(rng, 0.0, 0.0):
        return 0, False, False
    crit = roll_critical(rng, player_crit_chance(state))
    damage = calculate_damage(player_attack_power(state), 0.0, crit=crit)
    enemy.hp = max(0, enemy.hp - damage)
    record_action(state, "critical_hit" if crit else "attack")
    return damage, crit, True


def perform_enemy_attack(state: GameState, enemy: Enemy, player: CombatantState, rng: random.Random) -> tuple[int, bool, bool]:
    if not roll_hit(rng, 0.0, player_evasion(state)):
        return 0, False, False
    crit = roll_critical(rng, enemy.crit_chance)
    defense = player_defense(state) * (1.75 if player.defending else 1.0)
    damage = calculate_damage(enemy.attack, defense, crit=crit, multiplier=enemy.crit_multiplier)
    player.hp = max(0, player.hp - damage)
    return damage, crit, True


def resolve_combat(state: GameState, enemy: Enemy, *, seed: int | None = None, max_rounds: int = 100) -> CombatResult:
    rng = random.Random(seed if seed is not None else state.random_seed)
    player = CombatantState(state.player.name, state.player.hp, state.player.max_hp)
    foe = CombatantState(enemy.name, enemy.max_hp, enemy.max_hp)
    result = CombatResult(outcome="defeat", rounds=0, xp_reward=enemy.xp_reward, gold_reward=enemy.gold_reward)

    while result.rounds < max_rounds and player.hp > 0 and foe.hp > 0:
        result.rounds += 1
        player.defending = False
        damage, crit, hit = perform_player_attack(state, foe, rng)
        if hit:
            result.damage_dealt += damage
            result.critical_hits += int(crit)
            result.history.append(f"player:hit:{damage}:{'crit' if crit else 'normal'}")
        else:
            result.history.append("player:miss")
        if foe.hp <= 0:
            result.outcome = "victory"
            break

        damage, _crit, hit = perform_enemy_attack(state, enemy, player, rng)
        if hit:
            result.damage_taken += damage
            result.history.append(f"enemy:hit:{damage}")
        else:
            result.history.append("enemy:miss")

    state.player.hp = max(0, min(state.player.max_hp, player.hp))
    if result.outcome == "victory":
        grant_xp(state, enemy.xp_reward)
        state.player.gold += enemy.gold_reward
        state.world_flags["survived_encounter"] = True
        record_action(state, "win_fight")
    else:
        record_action(state, "combat_defeat")
    return result
