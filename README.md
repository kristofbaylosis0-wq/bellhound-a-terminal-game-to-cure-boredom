# A text RPG game made by ChatGPT

An open-source AI-assisted terminal text RPG built collaboratively with ChatGPT.

## Vision

A replayable, story-heavy text RPG with a large branching narrative, many endings, persistent world state, and thousands of meaningful interactions.

The game uses a deterministic rules engine for canon and state, while AI can provide dynamic narration, dialogue, interpretation of player intent, and other presentation.

## AI provider support

The provider layer is designed to keep the game independent from any particular model or vendor.

Currently supported adapters:

- OpenAI
- Anthropic
- Google Gemini
- NVIDIA NIM
- OpenRouter
- Ollama
- LM Studio
- Generic OpenAI-compatible endpoints
- On-device/local OpenAI-compatible endpoints

NVIDIA NIM is supported through its OpenAI-compatible inference API, so hosted and self-hosted NIM deployments can use the same adapter pattern.

## Provider architecture

```text
RPG engine
    |
    v
AIManager
    |
    +-- OpenAI
    +-- Anthropic
    +-- Google Gemini
    +-- NVIDIA NIM
    +-- OpenRouter
    +-- Ollama
    +-- LM Studio
    +-- On-device / local endpoint
    +-- Generic OpenAI-compatible API
```

Important game state is never supposed to be controlled solely by the model. The engine owns rules, canon, quests, relationships, inventory, flags, and other authoritative state.

## Security

API keys must be supplied through environment variables or a future local configuration layer. Secrets must never be committed to the repository.

## Development

This project is currently in the provider-abstraction stage. The RPG engine, world, story, dialogue system, memory, quests, and endings will be built on top of this foundation.
