# HEARME MCP

> **Turn documentation into listenable understanding**

HEARME is a [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) implementation that converts project documentation into natural, conversational audio – designed for listening, not reading.

## 🎯 What It Does

Unlike simple text-to-speech, HEARME creates an **audio experience**:

- 🗣️ Multi-speaker conversations (like Google NotebookLM's Audio Overview)
- 🎙️ Narrative walkthroughs of your codebase
- 📖 Spoken explanations optimized for passive listening
- 🤖 Agent-driven – your AI agent controls tone, personality, and structure

## ✨ Key Features

- **Local-first** – All processing happens on your machine
- **Privacy-respecting** – No data leaves your device without consent
- **Agent-agnostic** – Works with any MCP-compatible agent (PostQode, Copilot, Cline, etc.)
- **Multi-engine support** – VibeVoice, Dia2, ChatTTS, and more
- **Single-command install** – Platform-specific scripts handle everything

## 🚀 Quick Start

### Installation

```bash
# macOS
curl -sSL https://raw.githubusercontent.com/hearme-mcp/hearme/main/scripts/install-macos.sh | bash

# Linux
curl -sSL https://raw.githubusercontent.com/hearme-mcp/hearme/main/scripts/install-linux.sh | bash

# Or with Python (cross-platform)
pip install hearme-mcp
hearme-install --engine vibevoice
```

### Add to Your Agent

After installation, add the generated config to your agent's MCP settings:

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
