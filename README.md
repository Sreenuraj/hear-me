# HEARME MCP

> **Replace your README.md with a hearme.mp3**

HEARME is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) that transforms your project documentation into natural, conversational audio files.

Instead of asking users to *read* your README, let them *listen* to it.

---

## 💡 The Idea

```
README.md  →  HEARME MCP  →  hearme.mp3
```

1. **You** plug HEARME into your AI agent (PostQode, Copilot, Cline, etc.)
2. **Select** the documents you want to convert (README, architecture docs, guides)
3. **Generate** a `hearme.mp3` – a podcast-style audio explanation of your project
4. **Ship it** alongside your code, so users can listen instead of read

Think Google NotebookLM's "Audio Overview" – but for any codebase, running locally on your machine.

---

## 🎧 What You Get

| Traditional | With HEARME |
|-------------|-------------|
| `README.md` – walls of text | `hearme.mp3` – conversational audio |
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

```bash
# macOS
./scripts/install-macos.sh --engine vibevoice

# Linux
./scripts/install-linux.sh --engine vibevoice

# Cross-platform
pip install hearme-mcp && hearme-install --engine vibevoice
```

### Add to Your Agent

After installation, add the generated config to your MCP settings:

```json
{
  "mcpServers": {
    "hearme": {
      "command": "python",
      "args": ["~/.hearme/server.py"],
      "env": {
        "HEARME_ENGINE": "vibevoice"
      }
    }
  }
}
```

### Generate Audio

Once configured, your agent can:

```
"Generate an audio overview of this project"
"Create a podcast-style discussion about the architecture"
"Explain the codebase in a casual conversation"
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   Your AI Agent                         │
│            (PostQode, Copilot, Cline, etc.)            │
└─────────────────────────┬───────────────────────────────┘
                          │ MCP Protocol
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     HEARME MCP                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Document   │  │   Audio     │  │   Prerequisite  │ │
│  │  Pipeline   │  │   Engine    │  │   Detection     │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Responsibility Split

| Layer | Handles |
|-------|---------|
| **Agent/LLM** | Meaning, narration, personality, tone, structure |
| **HEARME MCP** | File discovery, audio rendering, persistence |
| **Audio Engine** | Speech synthesis (VibeVoice, Kokoro, etc.) |

## 🔊 Audio Engines

| Engine | Multi-Speaker | Quality | Size | GPU |
|--------|--------------|---------|------|-----|
| **VibeVoice** | ✅ Up to 4 | ⭐⭐⭐⭐⭐ | 3GB | Recommended |
| **Dia2** | ✅ + nonverbal | ⭐⭐⭐⭐⭐ | 2GB | Recommended |
| **ChatTTS** | ✅ | ⭐⭐⭐⭐ | 1.5GB | Optional |
| **Kokoro** | ❌ | ⭐⭐⭐⭐ | 300MB | No |
| **Piper** | ❌ | ⭐⭐⭐ | 100MB | No |

## ⚙️ Configuration

```json
{
  "hearme": {
    "audio": {
      "engine": "vibevoice",
      "fallback_engine": "kokoro",
      "voices": "auto",
      "format": "mp3"
    },
    "privacy": {
      "allow_network": false
    }
  }
}
```

## 📚 Documentation

- [Requirements Specification](docs/requirements.md) – Full technical spec
- [Implementation Roadmap](docs/ROADMAP.md) – Development phases
- [Contributing Guide](docs/CONTRIBUTING.md) – How to contribute

## 🔒 Privacy

HEARME is **local-first by default**:

- ✅ All processing happens on your machine
- ✅ No telemetry or usage tracking
- ✅ Documents never leave your device
- ✅ Network access requires explicit consent (`"allow_network": true`)

## 📄 License

[MIT License](LICENSE) – Use freely in personal and commercial projects.

---

<p align="center">
  <b>HEARME</b> – Because documentation should be heard, not just read.
</p>
