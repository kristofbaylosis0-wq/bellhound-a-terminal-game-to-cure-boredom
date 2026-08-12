"""OpenAI-compatible provider used by OpenAI, NVIDIA NIM, OpenRouter, Ollama, etc.

Uses only Python's standard library so the RPG has a tiny dependency footprint.
"""

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from ..models import AIRequest, AIResponse, ProviderConfig
from ..provider import AIProvider, AIProviderError


class OpenAICompatibleProvider(AIProvider):
    """Provider for APIs implementing /v1/chat/completions."""

    name = "openai-compatible"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.base_url = (config.base_url or "https://api.openai.com/v1").rstrip("/")

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        return headers

    def _payload(self, request: AIRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": [{"role": m.role, "content": m.content} for m in request.messages],
            "temperature": request.temperature,
            "stream": request.stream,
        }
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens
        payload.update(request.extra)
        return payload

    def _post(self, payload: dict[str, Any]) -> bytes:
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"{self.name} HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"{self.name} connection failed: {exc.reason}") from exc

    def generate(self, request: AIRequest) -> AIResponse:
        if request.stream:
            raise AIProviderError("Use stream() for streaming requests")
        raw = json.loads(self._post(self._payload(request)))
        try:
            text = raw["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(f"Malformed {self.name} response: {raw}") from exc
        return AIResponse(
            text=text or "",
            model=request.model,
            provider=self.name,
            raw=raw,
            usage=raw.get("usage", {}),
        )

    def stream(self, request: AIRequest) -> Iterator[str]:
        payload = self._payload(request)
        payload["stream"] = True
        data = json.dumps(payload).encode("utf-8")
        http_request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=data,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.config.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    data_line = line[5:].strip()
                    if data_line == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_line)
                        delta = chunk["choices"][0].get("delta", {}).get("content")
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        continue
                    if delta:
                        yield delta
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"{self.name} HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"{self.name} connection failed: {exc.reason}") from exc

    def list_models(self) -> list[str]:
        request = urllib.request.Request(
            f"{self.base_url}/models",
            headers=self._headers(),
            method="GET",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                raw = json.loads(response.read())
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"{self.name} HTTP {exc.code}: {body[:1000]}") from exc
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            raise AIProviderError(f"{self.name} model discovery failed: {exc}") from exc
        return [item["id"] for item in raw.get("data", []) if isinstance(item, dict) and "id" in item]

    def validate_config(self) -> None:
        if not self.base_url.startswith(("http://", "https://")):
            raise AIProviderError("base_url must start with http:// or https://")


class OpenAIProvider(OpenAICompatibleProvider):
    name = "openai"


class NvidiaNIMProvider(OpenAICompatibleProvider):
    """NVIDIA NIM LLM endpoint; NIM exposes an OpenAI-compatible API."""

    name = "nvidia-nim"

    def __init__(self, config: ProviderConfig) -> None:
        if config.base_url is None:
            config = ProviderConfig(
                name=config.name,
                api_key=config.api_key,
                base_url="https://integrate.api.nvidia.com/v1",
                timeout=config.timeout,
                extra=config.extra,
            )
        super().__init__(config)


class OpenRouterProvider(OpenAICompatibleProvider):
    name = "openrouter"

    def __init__(self, config: ProviderConfig) -> None:
        if config.base_url is None:
            config = ProviderConfig(
                name=config.name,
                api_key=config.api_key,
                base_url="https://openrouter.ai/api/v1",
                timeout=config.timeout,
                extra=config.extra,
            )
        super().__init__(config)


class OllamaProvider(OpenAICompatibleProvider):
    name = "ollama"

    def __init__(self, config: ProviderConfig) -> None:
        if config.base_url is None:
            config = ProviderConfig(
                name=config.name,
                api_key=config.api_key,
                base_url="http://127.0.0.1:11434/v1",
                timeout=config.timeout,
                extra=config.extra,
            )
        super().__init__(config)


class LMStudioProvider(OpenAICompatibleProvider):
    name = "lm-studio"

    def __init__(self, config: ProviderConfig) -> None:
        if config.base_url is None:
            config = ProviderConfig(
                name=config.name,
                api_key=config.api_key,
                base_url="http://127.0.0.1:1234/v1",
                timeout=config.timeout,
                extra=config.extra,
            )
        super().__init__(config)


class OnDeviceProvider(OpenAICompatibleProvider):
    """Generic local/on-device adapter.

    Android runtimes can point this at an OpenAI-compatible local server such as
    an on-device inference bridge. The engine does not require internet access.
    """

    name = "on-device"
