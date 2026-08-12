# A text RPG game made by ChatGPT

An open-source AI-assisted terminal text RPG built collaboratively with ChatGPT.

## Install + launch

On Linux, macOS, or Termux, run:

```bash
curl -fsSL https://raw.githubusercontent.com/kristofbaylosis0-wq/idk/main/install.sh | bash
```

The installer downloads the repository, creates its virtual environment, installs the game, creates the `RPG` command, and automatically boots the launcher.

If `~/.local/bin` is not already on your `PATH`, add it and open a new shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

## Boot commands

Open the launcher:

```bash
RPG game
```

Or simply:

```bash
RPG
```

Start a new game directly:

```bash
RPG new game
```

Load a known save by name:

```bash
RPG Save1
```

The launcher will also provide a save browser when you do not remember a save name.

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
