# A text RPG game made by ChatGPT

An open-source AI-assisted terminal text RPG built collaboratively with ChatGPT.

## Install + launch

### One-command install

On Linux, macOS, or Termux, run:

```bash
curl -fsSL https://raw.githubusercontent.com/kristofbaylosis0-wq/idk/main/install.sh | bash
```

The installer is intentionally quiet: Git and pip output are hidden while a small progress display shows what is happening. When installation finishes, the game **automatically boots**.

The installer:

1. Checks for Python 3.10+.
2. Downloads the latest version of the repository.
3. Creates an isolated Python environment.
4. Installs the RPG and its development dependencies.
5. Installs the `RPG` command into `~/.local/bin`.
6. Launches the game automatically.

If `~/.local/bin` is not already on your `PATH`, the installer will tell you. You can add it with:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Open a new shell afterward if needed.

### Updating

Run the same install command again. If the RPG is already installed, the installer updates the existing checkout and reinstalls the current version before booting it.

## Boot commands

Open the launcher, where you can choose New Game or browse your saves:

```bash
RPG game
```

`RPG` by itself opens the same launcher:

```bash
RPG
```

Start a new game directly without opening the launcher:

```bash
RPG new game
```

Load a known save directly:

```bash
RPG Save1
```

The available manual save slots are `Save1`, `Save2`, and `Save3`. If you do not remember a save name, use `RPG game` and choose **Boot From Saves**.

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
