# AI Runtime

The RPG talks to `AIManager`, not directly to a provider.

```python
from rpg_ai import AIManager, AIMessage, AIRequest, ProviderConfig

config = ProviderConfig(name="openai", api_key=None)
ai = AIManager.from_config(config)

response = ai.generate(
    AIRequest(
        model="your-model",
        messages=[AIMessage(role="user", content="Hello")],
    )
)

print(response.text)
```

## Runtime guarantees

- Every request gets a request ID unless the caller supplies one.
- Complete generations retry according to `RetryPolicy`.
- Fallback providers are tried after the primary provider exhausts its retries.
- Responses report the provider, model, attempt count, request ID, and whether a fallback was used.
- Streaming may fall back only before any output has been emitted. Once text reaches the caller, a later provider failure is surfaced instead of restarting and duplicating output.

## Configuration

Provider credentials stay outside the repository. Use environment variables or a future local configuration UI. See `rpg_ai/config.py` for the supported environment variable names.

## Example with fallback

```python
from rpg_ai import AIManager, AIMessage, AIRequest, ProviderConfig
from rpg_ai.models import RetryPolicy

ai = AIManager.from_config(
    ProviderConfig(name="openai"),
    fallback_configs=[ProviderConfig(name="ollama", base_url="http://127.0.0.1:11434/v1")],
    retry_policy=RetryPolicy(max_attempts=2),
)

response = ai.generate(
    AIRequest(
        model="your-model",
        messages=[AIMessage(role="user", content="Continue the scene.")],
    )
)
```
