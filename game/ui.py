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


def _terminal_stream():
    """Return the real terminal input stream, even when stdin is a pipe."""
    if sys.stdin.isatty():
        return sys.stdin, False
    try:
        return open("/dev/tty", "r", encoding="utf-8", errors="replace"), True
    except OSError:
        return sys.stdin, False


def terminal_input(prompt: str = "") -> str:
    """Read a line from the user's terminal, not an installer/curl pipe."""
    stream, should_close = _terminal_stream()
    try:
        if prompt:
            print(prompt, end="", flush=True)
        return stream.readline().rstrip("\r\n")
    finally:
        if should_close:
            stream.close()


def pause(message: str = "Press Enter to continue...") -> None:
    terminal_input(f"\n{message}")


def title() -> None:
    print("╔══════════════════════════════════════════════╗")
    print("║    A TEXT RPG GAME MADE BY CHATGPT + MANUS ║")
    print("╚══════════════════════════════════════════════╝")


def menu(title_text: str, options: list[str], *, footer: str = "Use ↑/↓ and Enter, or type a number.", context: list[str] | None = None) -> int:
    selected = 0
    while True:
        clear()
        if context:
            for paragraph in context:
                print(paragraph)
                print()
            print("─" * 46)
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
    """Read one selection key from the actual terminal, including curl installs."""
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

    stream, should_close = _terminal_stream()
    fd = stream.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        first = os.read(fd, 1).decode("utf-8", errors="ignore")
        if first in {"\r", "\n"}:
            return "enter"
        if first == "\x1b":
            sequence = os.read(fd, 2).decode("utf-8", errors="ignore")
            return {"[A": "up", "[B": "down"}.get(sequence, "escape")
        return first.lower()
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
        if should_close:
            stream.close()


def prompt_name(create: Callable[[str], object]) -> str:
    while True:
        clear()
        title()
        print("\nCHARACTER CREATION\n")
        print("What should the world call you?\n")
        name = terminal_input("> ").strip()
        try:
            create(name)
            return name
        except ValueError as exc:
            print(f"\n{name or 'That name'} will not work: {exc}")
            pause()
