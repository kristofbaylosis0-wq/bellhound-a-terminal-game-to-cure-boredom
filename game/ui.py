"""Terminal UI helpers for the RPG launcher and early-game shell."""

from __future__ import annotations

import os
import sys
from collections.abc import Callable


def clear() -> None:
    if os.name == "nt":
        os.system("cls")
    else:
        print("\033[2J\033[H", end="")


def pause(message: str = "Press Enter to continue...") -> None:
    input(f"\n{message}")


def title() -> None:
    print("╔══════════════════════════════════════════════╗")
    print("║       A TEXT RPG GAME MADE BY CHATGPT      ║")
    print("╚══════════════════════════════════════════════╝")


def menu(title_text: str, options: list[str], *, footer: str = "Use ↑/↓ and Enter, or type a number.") -> int:
    selected = 0
    while True:
        clear()
        print("╔══════════════════════════════════════════════╗")
        print(f"║ {title_text[:44].center(44)} ║")
        print("╠══════════════════════════════════════════════╣")
        print("║                                              ║")
        for index, option in enumerate(options):
            marker = "▸" if index == selected else " "
            line = f"{marker} {index + 1}. {option}"
            print(f"║ {line[:42].ljust(42)} ║")
        print("║                                              ║")
        print("╠══════════════════════════════════════════════╣")
        print(f"║ {footer[:44].center(44)} ║")
        print("╚══════════════════════════════════════════════╝")

        key = read_key()
        if key == "up":
            selected = (selected - 1) % len(options)
        elif key == "down":
            selected = (selected + 1) % len(options)
        elif key in {"enter", "select"}:
            return selected
        elif key.isdigit() and 1 <= int(key) <= len(options):
            return int(key) - 1


def read_key() -> str:
    """Read one selection key without requiring an external UI dependency."""
    if not sys.stdin.isatty():
        return input("> ").strip().lower() or "enter"

    if os.name == "nt":
        import msvcrt

        key = msvcrt.getwch()
        if key in {"\r", "\n"}:
            return "enter"
        if key == "\xe0":
            extended = msvcrt.getwch()
            return {"H": "up", "P": "down"}.get(extended, extended)
        return key.lower()

    import termios
    import tty

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = sys.stdin.read(1)
        if first in {"\r", "\n"}:
            return "enter"
        if first == "\x1b":
            sequence = sys.stdin.read(2)
            return {"[A": "up", "[B": "down"}.get(sequence, "escape")
        return first.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def prompt_name(create: Callable[[str], object]) -> str:
    while True:
        clear()
        title()
        print("\nCHARACTER CREATION\n")
        print("What should the world call you?\n")
        name = input("> ").strip()
        try:
            create(name)
            return name
        except ValueError as exc:
            print(f"\n{name or 'That name'} will not work: {exc}")
            pause()
