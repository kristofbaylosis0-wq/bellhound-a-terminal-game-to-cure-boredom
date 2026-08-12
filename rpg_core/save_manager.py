"""Local save-slot persistence for the terminal game."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import GameState

SAVE_SLOTS = (1, 2, 3)


@dataclass(frozen=True)
class SaveInfo:
    slot: int
    exists: bool
    player_name: str | None = None
    level: int | None = None
    location: str | None = None
    updated_at: str | None = None
    playtime_seconds: int = 0


class SaveManager:
    """Manages three manual save slots plus one autosave on the local machine."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".text-rpg")
        self.save_dir = self.root / "saves"
        self.save_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, slot: int | str) -> Path:
        if slot == "autosave":
            return self.save_dir / "autosave.json"
        if slot not in SAVE_SLOTS:
            raise ValueError(f"Invalid save slot: {slot}")
        return self.save_dir / f"save{slot}.json"

    def exists(self, slot: int | str) -> bool:
        return self._path(slot).is_file()

    def list_slots(self) -> list[SaveInfo]:
        return [self._inspect(slot) for slot in SAVE_SLOTS]

    def _inspect(self, slot: int) -> SaveInfo:
        path = self._path(slot)
        if not path.is_file():
            return SaveInfo(slot=slot, exists=False)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            player = payload["state"]["player"]
            return SaveInfo(
                slot=slot,
                exists=True,
                player_name=player.get("name"),
                level=int(player.get("level", 1)),
                location=payload["state"].get("location"),
                updated_at=payload.get("updated_at"),
                playtime_seconds=int(payload.get("playtime_seconds", 0)),
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return SaveInfo(slot=slot, exists=True)

    def save(
        self,
        slot: int,
        state: GameState,
        *,
        playtime_seconds: int = 0,
    ) -> None:
        self._write(slot, state, playtime_seconds=playtime_seconds)

    def autosave(self, state: GameState, *, playtime_seconds: int = 0) -> None:
        self._write("autosave", state, playtime_seconds=playtime_seconds)

    def load(self, slot: int | str) -> GameState:
        path = self._path(slot)
        if not path.is_file():
            raise FileNotFoundError(f"Save slot {slot} is empty")
        payload = json.loads(path.read_text(encoding="utf-8"))
        return GameState.from_dict(payload["state"])

    def delete(self, slot: int) -> None:
        path = self._path(slot)
        try:
            path.unlink()
        except FileNotFoundError:
            return

    def _write(self, slot: int | str, state: GameState, *, playtime_seconds: int) -> None:
        path = self._path(slot)
        now = datetime.now(timezone.utc).isoformat()
        payload: dict[str, Any] = {
            "save_version": state.to_dict()["save_version"],
            "game_version": "0.1.0",
            "created_at": self._existing_created_at(path) or now,
            "updated_at": now,
            "playtime_seconds": max(0, int(playtime_seconds)),
            "state": state.to_dict(),
        }
        encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        self._atomic_write(path, encoded)

    @staticmethod
    def _existing_created_at(path: Path) -> str | None:
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            value = data.get("created_at")
            return value if isinstance(value, str) else None
        except (OSError, json.JSONDecodeError, AttributeError):
            return None

    @staticmethod
    def _atomic_write(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, path)
        finally:
            try:
                os.unlink(temp_name)
            except FileNotFoundError:
                pass
