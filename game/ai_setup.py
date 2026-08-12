"""First-run AI provider setup and local configuration."""

from __future__ import annotations

import json
from pathlib import Path

from rpg_ai.manager import AIManager
from rpg_ai.models import ProviderConfig

from .ui import clear, menu, pause, title

CONFIG_DIR = Path.home() / ".config" / "text-rpg-chatgpt"
CONFIG_PATH = CONFIG_DIR / "ai.json"


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        CONFIG_PATH.chmod(0o600)
    except OSError:
        pass


def configured() -> bool:
    data = load_config()
    return bool(data.get("provider") and data.get("model"))


def provider_setup(*, force: bool = False) -> None:
    if configured() and not force:
        return

    providers = list(AIManager.supported_providers().items())
    names = [f"{name} — {description}" for name, description in providers]
    names.extend(["Skip for now", "Exit"])

    while True:
        clear()
        title()
        print("\nAI PROVIDER SETUP\n")
        print("The RPG uses an AI provider for dynamic dialogue and narration.")
        print("Your provider configuration is stored locally on this device.\n")

        selected = menu("CHOOSE AI PROVIDER", names)
        if selected == len(providers):
            return
        if selected == len(providers) + 1:
            raise SystemExit(0)

        provider_name = providers[selected][0]
        clear()
        title()
        print(f"\nConfigure {provider_name}\n")
        model = input("Model name: ").strip()
        if not model:
            print("\nA model name is required.")
            pause()
            continue

        api_key = None
        if provider_name not in {"ollama", "lm-studio", "on-device"}:
            api_key = input("API key: ").strip() or None

        base_url = input("Base URL (press Enter for default): ").strip() or None
        config = ProviderConfig(
            name=provider_name,
            api_key=api_key,
            base_url=base_url,
        )
        try:
            AIManager._provider_from_config(config).validate_config()
        except Exception as exc:
            print(f"\nProvider configuration could not be validated: {exc}")
            print("You can save it anyway and fix the settings later.")
            pause()

        save_config({
            "provider": provider_name,
            "model": model,
            "api_key": api_key,
            "base_url": base_url,
        })
        clear()
        title()
        print(f"\n✓ {provider_name} configured.")
        print(f"Model: {model}")
        print(f"Config: {CONFIG_PATH}")
        pause()
        return
