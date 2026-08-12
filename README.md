# A text RPG game made by ChatGPT

An open-source AI-assisted terminal text RPG built collaboratively with ChatGPT.

## Quick start

### Linux / macOS / Termux

```bash
git clone https://github.com/kristofbaylosis0-wq/idk.git
cd idk
chmod +x install.sh boot.sh
./install.sh
./boot.sh
```

After installation, you can also boot the game with:

```bash
text-rpg
```

### Windows

The Python entry point is:

```text
python -m game
```

A native Windows installer/launcher can be added later.

## Development

The project is currently building its core systems: AI providers/runtime, persistent game state, player progression, terminal UI, inventory, and world topology. Story, dialogue, quests, characters, and endings will be layered on top of this foundation.

## AI providers

- OpenAI
- Anthropic
- Google Gemini
- NVIDIA NIM
- OpenRouter
- Ollama
- LM Studio
- Generic OpenAI-compatible endpoints
- On-device/local endpoints

Important game state remains authoritative in the game engine; AI is used for dynamic presentation and interpretation rather than being trusted to arbitrarily rewrite canon.
