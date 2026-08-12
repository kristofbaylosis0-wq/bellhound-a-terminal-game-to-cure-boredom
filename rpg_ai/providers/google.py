"""Google Gemini API provider using the public REST interface."""

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Iterator
from typing import Any

from ..models import AIRequest, AIResponse, ProviderConfig
from ..provider import AIProvider, AIProviderError


class GoogleGeminiProvider(AIProvider):
    name = "google"
    default_base_url = "https://generativelanguage.googleapis.com/v1beta"

    def __init__(self, config: ProviderConfig) -> None:
        super().__init__(config)
        self.base_url = (config.base_url or self.default_base_url).rstrip("/")

    def _payload(self, request: AIRequest) -> dict[str, Any]:
        system_parts: list[dict[str, Any]] = []
        contents: list[dict[str, Any]] = []
        for message in request.messages:
            if message.role == "system":
                system_parts.append({"text": message.content})
                continue
            role = "model" if message.role == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.content}]})
        payload: dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "temperature": request.temperature,
            },
        }
        if request.max_tokens is not None:
            payload["generationConfig"]["maxOutputTokens"] = request.max_tokens
        if system_parts:
            payload["systemInstruction"] = {"parts": system_parts}
        payload.update(request.extra)
        return payload

    def _url(self, request: AIRequest, stream: bool = False) -> str:
        action = "streamGenerateContent" if stream else "generateContent"
        query = {"key": self.config.api_key}
        if stream:
            query["alt"] = "sse"
        return f"{self.base_url}/models/{urllib.parse.quote(request.model)}:{action}?{urllib.parse.urlencode(query)}"

    def generate(self, request: AIRequest) -> AIResponse:
        if not self.config.api_key:
            raise AIProviderError("Google Gemini requires an API key")
        if request.stream:
            raise AIProviderError("Use stream() for streaming requests")
        raw = self._request(self._url(request), self._payload(request))
        try:
            data = json.loads(raw)
            candidates = data["candidates"]
            parts = candidates[0]["content"]["parts"]
            text = "".join(part.get("text", "") for part in parts)
        except (json.JSONDecodeError, KeyError, IndexError, TypeError) as exc:
            raise AIProviderError(f"Malformed Google Gemini response: {raw[:1000]}") from exc
        return AIResponse(
            text=text,
            model=request.model,
            provider=self.name,
            raw=data,
            usage=data.get("usageMetadata", {}),
        )

    def stream(self, request: AIRequest) -> Iterator[str]:
        if not self.config.api_key:
            raise AIProviderError("Google Gemini requires an API key")
        http_request = urllib.request.Request(
            self._url(request, stream=True),
            data=json.dumps(self._payload(request)).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.config.timeout) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line.startswith("data:"):
                        continue
                    try:
                        data = json.loads(line[5:].strip())
                        parts = data["candidates"][0]["content"]["parts"]
                    except (json.JSONDecodeError, KeyError, IndexError, TypeError):
                        continue
                    for part in parts:
                        text = part.get("text")
                        if text:
                            yield text
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"Google Gemini HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"Google Gemini connection failed: {exc.reason}") from exc

    def _request(self, url: str, payload: dict[str, Any]) -> str:
        http_request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(http_request, timeout=self.config.timeout) as response:
                return response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise AIProviderError(f"Google Gemini HTTP {exc.code}: {body[:1000]}") from exc
        except urllib.error.URLError as exc:
            raise AIProviderError(f"Google Gemini connection failed: {exc.reason}") from exc

    def validate_config(self) -> None:
        if not self.config.api_key:
            raise AIProviderError("Google Gemini requires an API key")
