"""Provider-agnostic request and response models."""

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


@dataclass(frozen=True)
class AIResponse:
    text: str
    model: str
    provider: str
    raw: Any = None
    usage: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration shared by network and local providers."""

    name: str
    api_key: str | None = None
    base_url: str | None = None
    timeout: float = 60.0
    extra: Mapping[str, Any] = field(default_factory=dict)
