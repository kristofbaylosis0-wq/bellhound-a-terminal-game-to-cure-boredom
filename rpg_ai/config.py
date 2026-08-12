"""Configuration helpers for AI providers.

Secrets are intentionally sourced from environment variables rather than stored
in the repository or save files.
"""

from __future__ import annotations

import os

from .models import ProviderConfig


ENV_KEYS = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GOOGLE_API_KEY",
    "nvidia-nim": "NVIDIA_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
}


def provider_config(
    name: str,
    *,
    model: str | None = None,
    base_url: str | None = None,
    timeout: float = 60.0,
) -> tuple[ProviderConfig, str | None]:
    """Create provider config from environment and return the selected model."""

    api_key = os.getenv(ENV_KEYS.get(name, "")) if name in ENV_KEYS else None

    if name in {"ollama", "lm-studio"} and base_url is None:
        default_urls = {
            "ollama": "http://127.0.0.1:11434/v1",
            "lm-studio": "http://127.0.0.1:1234/v1",
        }
        base_url = default_urls[name]

    config = ProviderConfig(
        name=name,
        api_key=api_key,
        base_url=base_url,
        timeout=timeout,
    )
    return config, model
