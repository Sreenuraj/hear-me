# hear-me MCP

**🎧 Experimental: this repo includes [`hear-me.wav`](hear-me.wav) — a little preview while we keep polishing the pipeline.**

> **Replace your README.md with a hear-me.wav**

hear-me is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) that transforms your project documentation into natural, conversational audio files.

Instead of asking users to *read* your README, let them *listen* to it.

---

## 💡 The Idea

```
README.md  →  hear-me MCP  →  hear-me.wav
```

1. **You** plug hear-me into your AI agent (PostQode, Copilot, Cline, etc.)
2. **Select** the documents you want to convert (README, architecture docs, guides)
3. **Generate** a `hear-me.wav` – a podcast-style audio explanation of your project
4. **Ship it** alongside your code, so users can listen instead of read

Think Google NotebookLM's "Audio Overview" – but for any codebase, running locally on your machine.

---

## 🎧 What You Get

| Traditional | With hear-me |
|-------------|-------------|
| `README.md` – walls of text | `hear-me.wav` – conversational audio |
| Users skim or skip | Users listen while commuting/coding |
| Static documentation | Dynamic, engaging explanations |
| One format fits none | Audio-first understanding |

**Example outputs:**
- 🗣️ *"Hey, welcome to the project! Let me walk you through what this does..."*
- 🎙️ Multi-speaker discussions explaining architecture decisions
- 📖 Narrative walkthroughs of your codebase

---

## ✨ Key Features

- **Local-first** – All processing happens on your machine
- **Privacy-respecting** – No data leaves your device without consent
- **Agent-agnostic** – Works with any MCP-compatible agent
- **Multi-speaker** – Natural conversations with distinct voices
- **Single-command install** – Platform scripts handle setup

---

## 🚀 Quick Start

### Installation

**Default (Fast, Single-Speaker):**
```bash
./scripts/install-macos.sh --engine kokoro
```
*Recommended for quick, consistent narration.*

**Dia2 (Experimental):**
```bash
./scripts/install-macos.sh --engine dia2
```
*Installs hear-me with Dia2 engine (high quality, multi-speaker) using Apple Silicon acceleration.*
*Experimental: long renders/timeouts can occur on real codebases. Use only if you’re OK with slow runs.*

**Cross-Platform (Linux/Windows):**
```bash
python scripts/install.py --profile recommended
```

### Add to Your Agent
After installation, paste the generated JSON config into your MCP settings (e.g., `~/Library/Application Support/Code/.../cline_mcp_settings.json` or similar).

```json
{
  "mcpServers": {
    "hear-me": {
      "command": "/Users/you/.hear-me/venv/bin/python",
      "args": ["-m", "hear-me"]
    }
  }
}
```

### Usage
Ask your agent:
> "Create a 2-person podcast about this project's architecture"

Tip: If you already know which docs to include, you can skip scanning and pass
the file list directly to analysis/context generation.

**Default behavior:** hear‑me now prefers a fast single‑speaker path (Kokoro) for speed and consistency. Multi‑speaker Dia2 is available when explicitly requested and is considered experimental.

---

## 🔊 Audio Engines

hear-me includes several engines to balance quality vs. performance.

| Engine | Quality | Multi-Speaker | Size | Features |
|--------|---------|---------------|------|----------|
| **Dia2** (Experimental) | ⭐⭐⭐⭐⭐ | ✅ Yes (2 Hosts) | ~2GB | NotebookLM-like, Non-verbal cues, MPS/GPU (slow/long renders) |
| **Kokoro** (Default) | ⭐⭐⭐⭐ | ❌ No | ~300MB | High quality single-voice, very fast |
| **Piper** (Fast) | ⭐⭐ | ❌ No | ~50MB | Ultra-lightweight, works on anything |
| **Mock** (Dev) | 🌑 | ✅ Yes | 0MB | Silent placeholder for testing |

*Note: VibeVoice engine support coming soon.*

**No vendored code:** all engines are installed from their upstream projects at install time.

## ⚙️ Configuration
hear-me automatically degrades gracefully. If Dia2 fails (e.g., out of memory), it falls back to Kokoro, then Piper.

You can force a specific engine in your agent prompt:
> "Use the 'piper' engine to read this quickly."


## 📚 Documentation

- [Requirements Specification](docs/requirements.md) – Full technical spec
- [Implementation Roadmap](docs/ROADMAP.md) – Development phases
- [Contributing Guide](docs/CONTRIBUTING.md) – How to contribute

## 🔒 Privacy

hear-me is **local-first by default**:

- ✅ All processing happens on your machine
- ✅ No telemetry or usage tracking
- ✅ Documents never leave your device
- ✅ Network access requires explicit consent (`"allow_network": true`)

## 📄 License

[MIT License](LICENSE) – Use freely in personal and commercial projects.

---

<p align="center">
  <b>hear-me</b> – Because documentation should be heard, not just read.
</p>

## 🧹 Uninstall / Reset

If you want to remove all hear-me artifacts (venv, models, engines, outputs),
use the destroy-all script:

```bash
./scripts/destroy-all.sh
```

Add `--yes` to skip the confirmation prompt.
