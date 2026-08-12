"""Local persistent AI provider settings and first-run helpers."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import asdict, dataclass
from pathlib import Path

from .models import ProviderConfig

CONFIG_DIR = Path.home() / ".config" / "text-rpg-chatgpt"
CONFIG_PATH = CONFIG_DIR / "ai.json"


@dataclass
class AISettings:
    provider: str
    model: str
    api_key: str | None = None
    base_url: str | None = None

    def to_provider_config(self) -> ProviderConfig:
        return ProviderConfig(
            name=self.provider,
            api_key=self.api_key,
            base_url=self.base_url,
        )


def load_settings(path: Path = CONFIG_PATH) -> AISettings | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return AISettings(
            provider=str(raw["provider"]),
            model=str(raw["model"]),
            api_key=raw.get("api_key"),
            base_url=raw.get("base_url"),
        )
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def save_settings(settings: AISettings, path: Path = CONFIG_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asdict(settings), indent=2, ensure_ascii=False) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        os.chmod(temp_name, stat.S_IRUSR | stat.S_IWUSR)
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
        try:
            os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)
        except OSError:
            pass
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
