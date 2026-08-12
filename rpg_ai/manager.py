"""Provider registry and resilient runtime routing layer."""

from __future__ import annotations

import time
import uuid
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Callable

from .models import AIRequest, AIResponse, ProviderConfig, RetryPolicy
from .provider import AIProvider, AIProviderError
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


@dataclass(frozen=True)
class ProviderRoute:
    """A provider plus its per-route retry/fallback settings."""

    name: str
    provider: AIProvider
    retry_policy: RetryPolicy


class AIManager:
    """Single runtime entry point for all AI generation in the RPG.

    The game talks to this class instead of directly calling providers. It owns
    provider selection, retries, fallback routing, request IDs, and response
    metadata while keeping provider-specific details isolated.
    """

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

    def __init__(
        self,
        provider: AIProvider | None = None,
        *,
        fallback_providers: list[AIProvider] | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self._provider = provider
        self._fallback_providers = list(fallback_providers or [])
        self._retry_policy = retry_policy or RetryPolicy()

    @classmethod
    def supported_providers(cls) -> dict[str, str]:
        return {name: spec.description for name, spec in cls.DEFAULTS.items()}

    @classmethod
    def from_config(
        cls,
        config: ProviderConfig,
        *,
        fallback_configs: list[ProviderConfig] | None = None,
        retry_policy: RetryPolicy | None = None,
    ) -> "AIManager":
        return cls(
            provider=cls._provider_from_config(config),
            fallback_providers=[cls._provider_from_config(item) for item in fallback_configs or []],
            retry_policy=retry_policy,
        )

    @classmethod
    def _provider_from_config(cls, config: ProviderConfig) -> AIProvider:
        try:
            spec = cls.DEFAULTS[config.name]
        except KeyError as exc:
            raise ValueError(f"Unsupported AI provider: {config.name}") from exc
        return spec.factory(config)

    @property
    def provider(self) -> AIProvider:
        if self._provider is None:
            raise RuntimeError("No AI provider configured")
        return self._provider

    def add_fallback(self, provider: AIProvider) -> None:
        self._fallback_providers.append(provider)

    def validate(self) -> None:
        """Validate the primary provider and all configured fallbacks."""
        self.provider.validate_config()
        for provider in self._fallback_providers:
            provider.validate_config()

    def generate(self, request: AIRequest) -> AIResponse:
        """Generate a complete response with retries and provider fallback."""
        request_id = request.request_id or uuid.uuid4().hex
        request = AIRequest(**{**request.__dict__, "request_id": request_id})
        errors: list[Exception] = []

        for provider_index, provider in enumerate(self._providers()):
            try:
                response, attempts = self._generate_with_retries(provider, request)
                return AIResponse(
                    text=response.text,
                    model=response.model,
                    provider=response.provider,
                    raw=response.raw,
                    usage=response.usage,
                    request_id=request_id,
                    attempts=attempts,
                    fallback_used=provider_index > 0,
                )
            except Exception as exc:  # provider adapters normalize failures where possible
                errors.append(exc)

        raise AIProviderError(self._format_failure("generation", request_id, errors))

    def stream(self, request: AIRequest) -> Iterator[str]:
        """Stream from the first provider that can successfully start the stream.

        A fallback is attempted only before any chunks are yielded. Once output
        reaches the caller, switching providers would duplicate or corrupt text.
        """
        request_id = request.request_id or uuid.uuid4().hex
        request = AIRequest(**{**request.__dict__, "request_id": request_id, "stream": True})
        errors: list[Exception] = []

        for provider_index, provider in enumerate(self._providers()):
            for attempt in range(1, self._retry_policy.max_attempts + 1):
                iterator = None
                emitted = False
                try:
                    iterator = provider.stream(request)
                    for chunk in iterator:
                        emitted = True
                        yield chunk
                    return
                except Exception as exc:
                    errors.append(exc)
                    if emitted or attempt >= self._retry_policy.max_attempts:
                        break
                    self._sleep_before_retry(attempt)
            # Only proceed to another provider when this provider never emitted text.
            if provider_index + 1 < len(self._providers()):
                continue

        raise AIProviderError(self._format_failure("streaming", request_id, errors))

    def _providers(self) -> list[AIProvider]:
        return [self.provider, *self._fallback_providers]

    def _generate_with_retries(self, provider: AIProvider, request: AIRequest) -> tuple[AIResponse, int]:
        errors: list[Exception] = []
        for attempt in range(1, self._retry_policy.max_attempts + 1):
            try:
                return provider.generate(request), attempt
            except Exception as exc:
                errors.append(exc)
                if attempt >= self._retry_policy.max_attempts:
                    break
                self._sleep_before_retry(attempt)
        raise AIProviderError(
            self._format_failure(f"provider {provider.name}", request.request_id or "unknown", errors)
        )

    def _sleep_before_retry(self, attempt: int) -> None:
        delay = self._retry_policy.backoff_seconds * (
            self._retry_policy.backoff_multiplier ** (attempt - 1)
        )
        if delay:
            time.sleep(delay)

    @staticmethod
    def _format_failure(operation: str, request_id: str, errors: list[Exception]) -> str:
        details = "; ".join(f"{type(error).__name__}: {error}" for error in errors)
        return f"AI {operation} failed (request_id={request_id}). {details}"
