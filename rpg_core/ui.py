"""Terminal UI helpers for the RPG foundation."""

from __future__ import annotations

from collections.abc import Sequence

from .models import GameState, Player
from .save_manager import SaveInfo


WIDTH = 58


def clear() -> None:
    print("\033[2J\033[H", end="")


def panel(title: str, lines: Sequence[str] = ()) -> None:
    print("╔" + "═" * WIDTH + "╗")
    print("║" + title.center(WIDTH) + "║")
    print("╠" + "═" * WIDTH + "╣")
    for line in lines:
        print("║" + line[:WIDTH].ljust(WIDTH) + "║")
    print("╚" + "═" * WIDTH + "╝")


def main_menu() -> None:
    panel("THE LAST SERVER", ["", "> NEW GAME", "> BOOT FROM SAVES", "> SETTINGS", "> EXIT"])


def prompt_name() -> str:
    while True:
        name = input("\nWhat is your name?\n> ").strip()
        if name:
            return name
        print("Name cannot be empty.")


def format_playtime(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def save_selection(infos: Sequence[SaveInfo]) -> None:
    lines: list[str] = []
    for info in infos:
        if not info.exists:
            lines.extend([f"SAVE {info.slot}", "  Empty", ""])
            continue
        lines.extend([
            f"SAVE {info.slot}",
            f"  {info.player_name or 'Unknown'}  |  Level {info.level or 1}",
            f"  Location: {info.location or 'Unknown'}",
            f"  Playtime: {format_playtime(info.playtime_seconds)}",
            f"  Updated: {info.updated_at or 'Unknown'}",
            "",
        ])
    panel("SAVE DATA", lines)


def character_sheet(player: Player) -> None:
    stat_lines = [f"  {name.title():14} {value:>3}" for name, value in player.stats.items()]
    panel(
        "CHARACTER",
        [
            f"Name: {player.name}",
            f"Level: {player.level}",
            f"XP:    {player.xp} / {player.xp_to_next_level()}",
            f"HP:    {player.hp} / {player.max_hp}",
            f"Stat points: {player.stat_points}",
            f"Skill points: {player.skill_points}",
            "",
            "STATS",
            *stat_lines,
        ],
    )


def inventory(state: GameState) -> None:
    player = state.player
    lines = ["WEAPONS", "  " + (player.equipment.get("weapon") or "None")]
    lines += ["ARMOR", "  " + (player.equipment.get("armor") or "None")]
    lines += ["ACCESSORY", "  " + (player.equipment.get("accessory") or "None"), "", "ITEMS"]
    if player.inventory:
        lines.extend([f"  {item}" for item in player.inventory])
    else:
        lines.append("  Empty")
    panel("INVENTORY", lines)


def notify(message: str) -> None:
    print(f"\n> {message}")
