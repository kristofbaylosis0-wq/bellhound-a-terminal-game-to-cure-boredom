"""Provider-agnostic request, response, and runtime models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AIMessage:
    role: str
    content: str


@dataclass(frozen=True)
class AIRequest:
    messages: list[AIMessage]
    model: str
    temperature: float = 0.8
    max_tokens: int | None = 2048
    stream: bool = False
    extra: Mapping[str, Any] = field(default_factory=dict)
    request_id: str | None = None


@dataclass(frozen=True)
class AIResponse:
    text: str
    model: str
    provider: str
    raw: Any = None
    usage: Mapping[str, Any] = field(default_factory=dict)
    request_id: str | None = None
    attempts: int = 1
    fallback_used: bool = False


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration shared by network and local providers."""

    name: str
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 60.0
    extra: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RetryPolicy:
    """Controls transient failure handling in :class:`AIManager`."""

    max_attempts: int = 3
    backoff_seconds: float = 0.75
    backoff_multiplier: float = 2.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.backoff_seconds < 0:
            raise ValueError("backoff_seconds cannot be negative")
        if self.backoff_multiplier < 1:
            raise ValueError("backoff_multiplier must be at least 1")
