"""First-run AI provider setup and local configuration."""

from __future__ import annotations

from rpg_ai.manager import AIManager
from rpg_ai.models import AIMessage, AIRequest, ProviderConfig
from rpg_ai.provider import AIProviderError
from rpg_ai.settings import AISettings, load_settings, save_settings

from .ui import clear, menu, pause, title


def configured() -> bool:
    settings = load_settings()
    return settings is not None and bool(settings.provider and settings.model)


def _label(name: str) -> str:
    return {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "google": "Google Gemini",
        "nvidia-nim": "NVIDIA NIM",
        "openrouter": "OpenRouter",
        "ollama": "Ollama",
        "lm-studio": "LM Studio",
        "on-device": "On-device / local",
        "openai-compatible": "OpenAI-compatible custom endpoint",
    }.get(name, name)


def _config(name: str, api_key: str | None, base_url: str | None, timeout: float = 30.0) -> ProviderConfig:
    return ProviderConfig(name=name, api_key=api_key, base_url=base_url, timeout=timeout)


def _discover(name: str, api_key: str | None, base_url: str | None) -> list[str]:
    provider = AIManager._provider_from_config(_config(name, api_key, base_url))
    try:
        return provider.list_models()
    except Exception:
        return []


def _test(name: str, api_key: str | None, base_url: str | None, model: str) -> tuple[bool, str]:
    provider = AIManager._provider_from_config(_config(name, api_key, base_url))
    request = AIRequest(
        messages=[AIMessage(role="user", content="Reply with exactly CONNECTION_OK")],
        model=model,
        temperature=0,
        max_tokens=16,
    )
    try:
        response = provider.generate(request)
        return True, response.text.strip() or "Connection succeeded."
    except Exception as exc:
        return False, str(exc)


def _ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default else ""
    return input(f"{prompt}{suffix}\n> ").strip() or (default or "")


def provider_setup(*, force: bool = False) -> AISettings | None:
    """Run the provider wizard. Existing valid settings are kept unless forced."""
    existing = load_settings()
    if existing and configured() and not force:
        return existing

    providers = list(AIManager.supported_providers().keys())
    while True:
        clear()
        title()
        print("\nAI PROVIDER SETUP\n")
        print("Choose the AI backend used for dynamic dialogue, narration, and game interactions.\n")
        labels = [_label(name) for name in providers] + ["Skip for now", "Exit"]
        selected = menu("CHOOSE PROVIDER", labels)
        if selected == len(providers):
            return existing
        if selected == len(providers) + 1:
            raise SystemExit(0)

        name = providers[selected]
        old = existing if existing and existing.provider == name else None
        clear()
        title()
        print(f"\n{_label(name)}\n")

        custom_endpoint = name == "openai-compatible"
        if custom_endpoint:
            base_url = _ask("Base URL", old.base_url if old else None)
            api_key = _ask("API key (leave blank if not required)", old.api_key if old else None) or None
        else:
            base_url = None
            api_key_required = name not in {"ollama", "lm-studio", "on-device"}
            api_key = _ask("API key (leave blank if not required)", old.api_key if old else None) or None if api_key_required else None
            if name in {"ollama", "lm-studio", "on-device"}:
                override = _ask("Base URL override (leave blank for provider default)", old.base_url if old else None)
                base_url = override or None

        clear()
        title()
        print(f"\n{_label(name)} — MODEL\n")
        print("Trying to detect models...\n")
        models = _discover(name, api_key, base_url)

        if models:
            print("Detected models:")
            for index, model_name in enumerate(models[:30], 1):
                print(f"  {index}. {model_name}")
            print("  M. Enter a model slug manually")
            choice = _ask("Select model", "1")
            if choice.lower() == "m":
                model = _ask("Model slug", old.model if old else None)
            else:
                try:
                    model = models[int(choice) - 1]
                except (ValueError, IndexError):
                    model = _ask("Model slug", old.model if old else None)
        else:
            print("Could not automatically detect models from this provider.")
            print("You can enter the model slug manually.\n")
            model = _ask("Model slug", old.model if old else None)

        if not model:
            print("\nA model slug is required.")
            pause()
            continue

        while True:
            clear()
            title()
            print("\nTEST CONNECTION\n")
            print(f"Provider: {_label(name)}")
            print(f"Model:    {model}")
            if base_url:
                print(f"Base URL: {base_url}")
            print("\nTesting...\n")
            ok, detail = _test(name, api_key, base_url, model)
            if ok:
                print("✓ Connection successful")
                print(f"  {detail}")
                print()
                confirm = _ask("Save this configuration?", "Y")
                if confirm.lower() in {"y", "yes"}:
                    settings = AISettings(
                        provider=name,
                        model=model,
                        api_key=api_key,
                        base_url=base_url,
                    )
                    save_settings(settings)
                    return settings
                break

            print("✗ Connection failed")
            print(f"  {detail}")
            print("\n1. Try again")
            print("2. Change configuration")
            print("3. Skip for now")
            action = _ask("Choose", "2")
            if action == "1":
                continue
            if action == "3":
                return existing
            break
