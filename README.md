# A text RPG game made by ChatGPT and Manus

An open-source AI-assisted terminal text RPG built collaboratively with ChatGPT and Manus.

## Install + launch

### Linux / macOS / Termux

Run:

```bash
curl -fsSL https://raw.githubusercontent.com/kristofbaylosis0-wq/bellhound-a-terminal-game-to-cure-boredom/main/install.sh | bash
```

The installer is intentionally quiet: Git and pip output are hidden while a small progress display shows what is happening. When installation finishes, the game automatically boots.

### Windows PowerShell

Windows Terminal + PowerShell is supported too. Run:

```powershell
irm https://raw.githubusercontent.com/kristofbaylosis0-wq/bellhound-a-terminal-game-to-cure-boredom/main/install.ps1 | iex
```

The PowerShell installer downloads the repository, creates the Python virtual environment, installs the RPG, creates an `RPG` launcher in your user `bin` directory, updates your user `PATH`, and automatically boots the game.

You need **Git for Windows** and **Python 3.10+** installed first.

If Windows PowerShell does not recognize `RPG` after installation, restart PowerShell so the updated user `PATH` is loaded.

### Updating

Run the same installer command again for your platform. It updates the existing installation to the latest `main` branch before booting the game.

## Boot commands

Open the launcher, where you can choose New Game, browse saves, edit the AI provider, or exit:

```text
RPG game
```

`RPG` by itself opens the same launcher:

```text
RPG
```

Start a new game directly:

```text
RPG new game
```

Load a known save directly:

```text
RPG Save1
```

The available manual save slots are `Save1`, `Save2`, and `Save3`. If you do not remember a save name, use `RPG game` and choose **Boot From Saves**.

## Story modes

Every new game asks which story mode to use:

- **Hard-coded Story** — deterministic handcrafted campaign. AI is not required and the campaign can run offline.
- **Dynamic Story** — AI-directed presentation and connective scenes. An AI provider and model must be configured first.

Dynamic Story does not give the AI authority over canon game state. The game engine remains authoritative over progression, stats, inventory, resonance, chapter rules, and other permanent state; the AI controls presentation, dialogue, connective scenes, and bounded choice wording.

The selected story mode is stored in the save file, so loading a save resumes the correct story engine automatically.

## Development

The project is currently building its core systems: AI providers/runtime, persistent game state, player progression, terminal UI, inventory, combat, resonance, achievements, and world topology. Story, dialogue, quests, characters, and endings are layered on top of this foundation.

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
