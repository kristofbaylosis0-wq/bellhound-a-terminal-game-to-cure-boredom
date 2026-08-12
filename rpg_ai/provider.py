"""Base class for all AI providers."""

from abc import ABC, abstractmethod
from collections.abc import Iterator

from .models import AIRequest, AIResponse, ProviderConfig


class AIProviderError(RuntimeError):
    """Base exception for provider failures."""


class AIProvider(ABC):
    """Minimal interface used by the RPG engine."""

    name: str

    def __init__(self, config: ProviderConfig) -> None:
        self.config = config

    @abstractmethod
    def generate(self, request: AIRequest) -> AIResponse:
        """Generate one complete response."""

    @abstractmethod
    def stream(self, request: AIRequest) -> Iterator[str]:
        """Yield generated text chunks."""

    def validate_config(self) -> None:
        """Raise an error when provider configuration is unusable."""

    def list_models(self) -> list[str]:
        """Return models when the provider exposes model discovery."""
        return []
