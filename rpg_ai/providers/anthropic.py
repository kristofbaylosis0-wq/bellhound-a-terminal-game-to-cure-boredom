"""Anthropic Messages API provider."""

import json
import urllib.error
import urllib.request
from collections.abc import Iterator
from typing import Any

from ..models import AIRequest, AIResponse, ProviderConfig
from ..provider import AIProvider, AIProviderError


class AnthropicProvider(AIProvider):
    name = "anthropic"
    default_base_url = "https://api.anthropic.com/v1"
    api_version = "2023-06-01"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.base_url = (config.base_url or self.default_base_url).rstrip("/")

    def _headers(self) -> dict[str, str]:
        if not self.config.api_key:
            raise AIProviderError("Anthropic requires an API key")
        return {
            "content-type": "application/json",
            "x-api-key": self.config.api_key,
            "anthropic-version": self.api_version,
        }

    @staticmethod
    def _split_messages(request: AIRequest) -> tuple[str | None, list[dict[str, str]]]:
        system_parts: list[str] = []
        messages: list[dict[str, str]] = []
        for message in request.messages:
            if message.role == "system":
                system_parts.append(message.content)
            else:
                role = "assistant" if message.role == "assistant" else "user"
                messages.append({"role": role, "content": message.content})
        return ("\n\n".join(system_parts) or None, messages)

    def _payload(self, request: AIRequest, stream: bool = False) -> dict[str, Any]:
        system, messages = self._split_messages(request)
        payload: dict[str, Any] = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_tokens or 2048,
            "temperature": request.temperature,
            "stream": stream,
        }
        if system:
            payload["system"] = system
        payload.update(request.extra)
        return payload

    def generate(self, request: AIRequest) -> AIResponse:
        if request.stream:
            raise AIProviderError("Use stream() for streaming requests")
        raw = self._post(self._payload(request)).decode("utf-8")
        data = json.loads(raw)
        try:
            text = "".join(
                block.get("text", "")
                for block in data["content"]
                if block.get("type") == "text"
            )
        except (KeyError, TypeError) as exc:
            raise AIProviderError(f"Malformed Anthropic response: {data}") from exc
        return AIResponse(
            text=text,
            model=request.model,
            provider=self.name,
            raw=data,
            usage=data.get("usage", {}),
        )

    def _post(self, payload: dict[str, Any]) -> bytes:
        request = urllib.request.Request(
            f"{self.base_url}/messages",
            data=json.dumps(payload).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeout) as response:
                return response.read()
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"Anthropic HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"Anthropic connection failed: {exc.reason}") from exc

    def stream(self, request: AIRequest) -> Iterator[str]:
        http_request = urllib.request.Request(
            f"{self.base_url}/messages",
            data=json.dumps(self._payload(request, stream=True)).encode("utf-8"),
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.config.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        event = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        text = event.get("delta", {}).get("text")
                        if text:
                            yield text
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"Anthropic HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"Anthropic connection failed: {exc.reason}") from exc

    def validate_config(self) -> None:
        if not self.config.api_key:
            raise AIProviderError("Anthropic requires an API key")
        if not self.base_url.startswith(("http://", "https://")):
            raise AIProviderError("base_url must start with http:// or https://")
