from __future__ import annotations

import pytest

from rpg_ai.manager import AIManager
from rpg_ai.models import AIMessage, AIRequest, AIResponse, RetryPolicy
from rpg_ai.provider import AIProvider, AIProviderError
from rpg_ai.models import ProviderConfig


REQUEST = AIRequest(
    messages=[AIMessage(role="user", content="Hello")],
    model="test-model",
)


class FakeProvider(AIProvider):
    name = "fake"

    def __init__(self, config: ProviderConfig, *, failures: int = 0, stream_failure: bool = False):
        super().__init__(config)
        self.failures = failures
        self.stream_failure = stream_failure
        self.calls = 0

    def generate(self, request: AIRequest) -> AIResponse:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("temporary failure")
        return AIResponse(text="ok", model=request.model, provider=self.name)

    def stream(self, request: AIRequest):
        self.calls += 1
        if self.stream_failure:
            yield "partial"
            raise RuntimeError("stream broke")
        yield "ok"


def manager(primary: AIProvider, *fallbacks: AIProvider, attempts: int = 1) -> AIManager:
    return AIManager(
        primary,
        fallback_providers=list(fallbacks),
        retry_policy=RetryPolicy(max_attempts=attempts, backoff_seconds=0),
    )


def test_retries_before_returning_success() -> None:
    provider = FakeProvider(ProviderConfig(name="fake"), failures=2)

    response = manager(provider, attempts=3).generate(REQUEST)

    assert response.text == "ok"
    assert response.attempts == 3
    assert response.fallback_used is False
    assert response.request_id


def test_generation_falls_back_after_primary_exhausts_retries() -> None:
    primary = FakeProvider(ProviderConfig(name="fake"), failures=5)
    fallback = FakeProvider(ProviderConfig(name="fake"))

    response = manager(primary, fallback, attempts=2).generate(REQUEST)

    assert response.text == "ok"
    assert response.fallback_used is True
    assert primary.calls == 2
    assert fallback.calls == 1


def test_streaming_falls_back_before_any_output() -> None:
    primary = FakeProvider(ProviderConfig(name="fake"), failures=1)
    fallback = FakeProvider(ProviderConfig(name="fake"))

    chunks = list(manager(primary, fallback, attempts=1).stream(REQUEST))

    assert chunks == ["ok"]
    assert primary.calls == 1
    assert fallback.calls == 1


def test_streaming_does_not_fallback_after_output_started() -> None:
    primary = FakeProvider(ProviderConfig(name="fake"), stream_failure=True)
    fallback = FakeProvider(ProviderConfig(name="fake"))

    iterator = manager(primary, fallback, attempts=1).stream(REQUEST)
    assert next(iterator) == "partial"

    with pytest.raises(AIProviderError):
        next(iterator)

    assert fallback.calls == 0
