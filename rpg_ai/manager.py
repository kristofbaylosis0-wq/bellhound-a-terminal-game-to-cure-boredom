"""Provider registry and routing layer."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .models import AIRequest, AIResponse, ProviderConfig
from .provider import AIProvider
from .providers import (
    AnthropicProvider,
    GoogleGeminiProvider,
    LMStudioProvider,
    NvidiaNIMProvider,
    OllamaProvider,
    OnDeviceProvider,
    OpenAIProvider,
    OpenAICompatibleProvider,
    OpenRouterProvider,
)


@dataclass(frozen=True)
class ProviderSpec:
    factory: Callable[[ProviderConfig], AIProvider]
    description: str


class AIManager:
    """Owns provider registration and selects the configured backend."""

    DEFAULTS: dict[str, ProviderSpec] = {
        "openai": ProviderSpec(OpenAIProvider, "OpenAI API"),
        "anthropic": ProviderSpec(AnthropicProvider, "Anthropic Messages API"),
        "google": ProviderSpec(GoogleGeminiProvider, "Google Gemini API"),
        "nvidia-nim": ProviderSpec(NvidiaNIMProvider, "NVIDIA NIM / OpenAI-compatible API"),
        "openrouter": ProviderSpec(OpenRouterProvider, "OpenRouter API"),
        "ollama": ProviderSpec(OllamaProvider, "Ollama local API"),
        "lm-studio": ProviderSpec(LMStudioProvider, "LM Studio local API"),
        "on-device": ProviderSpec(OnDeviceProvider, "Local/on-device OpenAI-compatible API"),
        "openai-compatible": ProviderSpec(
            OpenAICompatibleProvider,
            "Generic OpenAI-compatible endpoint",
        ),
    }

    def __init__(self, provider: AIProvider | None = None) -> None:
        self._provider = provider

    @classmethod
    def supported_providers(cls) -> dict[str, str]:
        return {name: spec.description for name, spec in cls.DEFAULTS.items()}

    @classmethod
    def from_config(cls, config: ProviderConfig) -> "AIManager":
        try:
            spec = cls.DEFAULTS[config.name]
        except KeyError as exc:
            raise ValueError(f"Unsupported AI provider: {config.name}") from exc
        return cls(spec.factory(config))

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            raise RuntimeError("No AI provider configured")
        return self._provider

    def validate(self) -> None:
        self.provider.validate_config()

    def generate(self, request: AIRequest) -> AIResponse:
        return self.provider.generate(request)

    def stream(self, request: AIRequest):
        return self.provider.stream(request)
