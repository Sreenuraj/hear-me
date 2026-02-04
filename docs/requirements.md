# HEARME MCP – Requirements Specification

> **Replace your README.md with a hearme.mp3**

---

## 1. Purpose & Vision

**HEARME** is a Model Context Protocol (MCP) that transforms project documentation into natural, conversational audio files.

```
README.md  →  HEARME MCP  →  hearme.mp3
```

Instead of asking users to *read* your documentation, let them *listen* to it – podcast-style, with multi-speaker conversations, like Google NotebookLM's Audio Overview.

**The goal is not text-to-speech.** The goal is to produce:
- Conversational walkthroughs that explain your project
- Multi-speaker discussions about architecture decisions  
- Audio overviews users can listen to while commuting or coding

HEARME is designed to be:
- **Agent-driven** – Your AI controls tone, personality, structure
- **Local-first** – All processing on your machine
- **Privacy-respecting** – No data leaves without consent
- **LLM-agnostic** – Works with any MCP-compatible agent
- **Extensible** – Pluggable audio engines

---

## 2. Core Principles

1. **Agent-led intelligence**  
   HEARME does not embed or depend on any LLM.  
   All reasoning, interpretation, personality, tone, prioritization, and narrative structure are decided by the **invoking AI agent** (PostQode, Copilot, Cline, etc.).

2. **Execution-only MCP**  
   HEARME is responsible only for:
   - Document discovery and structuring
   - Preparing audio-suitable context
   - Rendering audio
   - Persisting outputs

3. **Audio-first, not TTS-first**  
   Output must sound natural when spoken and suitable for passive listening.  
   This is not text-to-speech; it is **documentation-to-understanding**.

4. **User-owned configuration**  
   All configuration (audio engines, voices, formats) is owned by the user via the MCP configuration JSON.

---

## 3. High-Level Architecture

```
Invoking Agent (LLM)
        │
        ▼
HEARME MCP (tools + execution)
        │
        ▼
Local Audio Engine + Workspace
```

### Responsibility Split

| Layer | Responsibility |
|------|----------------|
| Agent / LLM | Meaning, narration, personality, tone, structure |
| HEARME MCP | Files, structure, constraints, audio execution |
| Audio Engine | Deterministic audio synthesis |

---

## 4. Document Detection & Classification

### 4.1 Workspace Scanning

The MCP scans the workspace and detects documentation files using heuristics.

Supported formats:
- Markdown (`.md`)
- Plain text (`.txt`)
- Agent-approved text formats

Common entry points include:
- `README.md`
- `CONTRIBUTING.md`
- `ARCHITECTURE.md`
- `DESIGN.md`
- `/docs/**/*.md`

---

### 4.2 Classification & Signals

Each detected document is annotated with metadata:

```json
{
  "path": "docs/architecture.md",
  "category": "architecture",
  "size": 12400,
  "signals": ["components", "decisions", "diagrams"]
}
```

The MCP **does not decide relevance**.  
It provides signals; the agent decides how documents are used.

---

## 5. Multi-Document Support

- Unlimited documents (bounded only by agent context limits)
- Documents may be:
  - Primary (spoken content)
  - Secondary (background context)
- Document boundaries and structure are preserved
- MCP does not merge or summarize content

---

## 6. Audio Experience Intent (Modes)

Audio modes are **intent hints**, not rigid templates.

Examples (non-exhaustive):
- Explainer
- Discussion
- Narrative / Story
- Onboarding
- Architecture walkthrough
- Contributor-focused
- Executive summary
- Agent-decided

The agent may blend, ignore, or switch modes as it sees fit.

---

## 7. Length & Depth Control

Length is **semantic**, not time-based.

Supported values:
- `overview`
- `balanced`
- `thorough`
- `agent-decided`

The MCP never enforces duration or word count.

---

## 8. Personality & Tone (LLM-Owned)

### MCP Responsibilities
- Declare that output is **audio-first**
- Provide narration constraints:
  - Prefer spoken language
  - Avoid bullet lists and headings
  - Avoid reading code verbatim
  - Optimize for passive listening

### Agent / LLM Responsibilities
- Tone (formal, casual, enthusiastic, calm)
- Personality (teacher, peer, narrator, guide)
- Speaker behavior and dynamics
- Emphasis, prioritization, and narrative flow

HEARME never injects personality or opinions.

---

## 9. LLM Instruction Contract

HEARME defines a **semantic contract**, not a fixed prompt.

The MCP must communicate that:
- The output will be converted to audio
- It must sound natural when spoken
- It may involve one or more speakers
- The agent should decide narration style based on project context

Example (conceptual):

> Generate a narration script suitable for spoken audio.  
> Avoid lists and headings.  
> Explain concepts naturally.  
> Decide tone, personality, and structure based on the documentation.

Each agent may implement this contract in its own prompting system.

---

## 10. MCP Tools

### 10.1 `scan_workspace`
Detects and classifies documentation files.

### 10.2 `analyze_documents`
Parses structure (sections, headings, signals).  
No summarization or interpretation.

### 10.3 `propose_audio_plan`
Suggests documents, intent hints, speakers, and ambiguities.

### 10.4 `prepare_audio_context`
Produces LLM-ready context optimized for spoken explanation.

### 10.5 `render_audio`
Converts agent-generated script into audio.

### 10.6 `persist_outputs`
Writes generated artifacts to the workspace.

---

## 11. Script Interface (Canonical)

The MCP expects agent-generated scripts in the following form:

```json
[
  { "speaker": "narrator", "text": "This project exists to..." },
  { "speaker": "peer", "text": "Who is this meant for?" }
]
```

- Speaker labels are symbolic
- Text must already be narration-ready
- MCP does not edit or rewrite text

---

## 12. Audio Generation – Technical Requirements

### 12.1 Audio Engine Strategy

HEARME uses a **pluggable local audio engine model**.

- No cloud dependency
- No hardcoded providers
- No embedded voices
- Configuration-driven selection

The goal is to achieve audio quality comparable to **Google NotebookLM's Audio Overview** – natural, conversational, multi-speaker discussions that feel human.

---

### 12.2 Supported Audio Engines

> [!IMPORTANT]
> Engine selection is critical for achieving NotebookLM-quality output. The engines below are ordered by recommendation for multi-speaker conversational audio.

#### Tier 1: Multi-Speaker Conversational (Recommended)

| Engine | Best For | Multi-Speaker | Voice Cloning | License |
|--------|----------|---------------|---------------|---------|
| **VibeVoice** | Long-form podcasts, up to 90 min | ✅ Up to 4 speakers | ✅ | Open Source |
| **Dia2** | Dialogue w/ nonverbal (laughter, sighs) | ✅ Speaker tags [S1], [S2] | ✅ | Open Source |
| **ChatTTS** | Conversational, prosody control | ✅ | Limited | Open Source |

**VibeVoice** is the closest open-source match to NotebookLM's style:
- Designed specifically for multi-speaker conversational audio
- Maintains speaker consistency across long-form content
- Uses LLM-based turn management for natural dialogue flow
- Handles up to 90 minutes of synthesized content

**Dia2** excels at expressive dialogue:
- Supports nonverbal cues (laughter, coughing, sighing)
- Streaming architecture for real-time generation
- Speaker tag format: `[S1]`, `[S2]` etc.

**ChatTTS** provides fine-grained control:
- Prosody control (pauses, interjections)
- Optimized for chatbot and LLM assistant output
- English and Chinese support

#### Tier 2: High-Quality Single/Multi-Speaker

| Engine | Best For | Multi-Speaker | Voice Cloning | License |
|--------|----------|---------------|---------------|---------|
| **F5-TTS** | Consistent voice cloning | ✅ | ✅ Excellent | Open Source |
| **StyleTTS2** | Human-level naturalness | Limited | ✅ | Open Source |
| **XTTS-v2** | Multilingual, versatile | ✅ | ✅ | CPML (Coqui) |

**F5-TTS** offers the most consistent voice cloning:
- Fast inference (RTF ~0.15)
- Excellent speaker similarity
- Some instability with complex sentences

**StyleTTS2** achieves human-level naturalness:
- Best-in-class for single-speaker quality
- Very fast inference
- Limited multi-speaker support

**XTTS-v2** (formerly Coqui) remains viable:
- Multilingual (17+ languages)
- Good multi-speaker support
- Note: Coqui company shut down in 2023; community-maintained

#### Tier 3: Lightweight Fallback

| Engine | Best For | Multi-Speaker | Voice Cloning | License |
|--------|----------|---------------|---------------|---------|
| **Kokoro** | Edge/offline deployment | ❌ | Limited | Apache 2.0 |
| **Piper** | Reliability, minimal resources | ❌ | ❌ | MIT |
| **MeloTTS** | CPU-only, real-time | ❌ | ❌ | MIT |

**Kokoro** is the recommended fallback:
- Only 82M parameters
- Quality comparable to larger systems
- Suitable for resource-constrained environments

---

### 12.3 Engine Selection & Fallback

Audio engine selection is configuration-driven.

```json
{
  "hearme": {
    "audio": {
      "engine": "vibevoice",
      "fallback_engine": "kokoro",
      "format": "mp3"
    }
  }
}
```

Resolution rules:
1. Use primary engine
2. Downgrade unsupported features if needed (e.g., multi-speaker → single speaker)
3. Fall back to secondary engine on failure
4. Produce script-only output if all audio fails

---

### 12.4 Voice Mapping Contract

The MCP accepts voice mappings that bind speaker labels to engine-specific voice identifiers:

```json
{
  "voiceMap": {
    "narrator": { "voice": "emma", "style": "calm" },
    "peer": { "voice": "james", "style": "curious" }
  }
}
```

When `"voices": "auto"` is set, the MCP will:
1. Detect number of speakers from script
2. Assign distinct, complementary voices automatically
3. Prefer pairing male/female voices for dialogue

---

### 12.5 Audio Rendering Contract

```ts
renderAudio(script, voiceMap, outputFormat) → AudioFile
```

---

## 13. Prerequisite Detection & Installation

### 13.1 MCP Responsibility

The MCP **must detect missing prerequisites** and guide installation through the invoking agent.

When a user plugs HEARME into their agent, the MCP should:
1. Detect the user's platform (macOS, Linux, Windows)
2. Check for required dependencies (Python, audio engines, system libraries)
3. Report missing prerequisites with actionable installation guidance
4. Help the agent guide the user through installation

### 13.2 Prerequisite Detection Tool

```ts
check_prerequisites() → PrerequisiteReport
```

Returns:

```json
{
  "platform": "darwin",
  "python_version": "3.11.5",
  "audio_engines": {
    "vibevoice": { "installed": false, "required_deps": ["pytorch", "transformers"] },
    "kokoro": { "installed": true, "version": "0.2.1" }
  },
  "system_deps": {
    "ffmpeg": { "installed": true, "version": "6.0" },
    "espeak-ng": { "installed": false }
  },
  "ready": false,
  "missing": ["vibevoice", "espeak-ng"],
  "install_command": "hearme-install --engine vibevoice"
}
```

### 13.3 Installation Assistant Tool

```ts
install_prerequisites(engine: string, platform?: string) → InstallResult
```

The MCP provides guidance; the agent executes:
- Shows installation commands for the user's platform
- Handles dependency chains (e.g., PyTorch → TTS engine)
- Validates installation success

---

## 14. Installer Scripts

### 14.1 User Experience Goal

Users should install HEARME with a **single command** that:
1. Detects their platform
2. Installs required dependencies
3. Downloads the chosen TTS engine
4. Generates the MCP configuration file

### 14.2 Installer Script Structure

```
scripts/
  install-macos.sh       # macOS (Homebrew-based)
  install-linux.sh       # Linux (apt/dnf/pacman)
  install-windows.ps1    # Windows (winget/choco)
  install.py             # Cross-platform Python installer
```

### 14.3 Installer Behavior

**Input:**
```bash
./install-macos.sh --engine vibevoice
```

**Output:**
```
✅ Installation complete!

Add this to your agent's MCP configuration:

{
  "mcpServers": {
    "hearme": {
      "command": "python",
      "args": ["/Users/user/.hearme/server.py"],
      "env": {
        "HEARME_ENGINE": "vibevoice",
        "HEARME_MODELS_DIR": "/Users/user/.hearme/models"
      }
    }
  }
}
```

### 14.4 Engine-Specific Installation

| Engine | Model Size | GPU Required |
|--------|------------|--------------|
| VibeVoice | ~3GB | Recommended |
| Dia2 | ~2GB | Recommended |
| ChatTTS | ~1.5GB | Optional |
| Kokoro | ~300MB | No |
| Piper | ~100MB | No |

### 14.5 Installation Profiles

```bash
# Minimal (Kokoro only, CPU, small footprint)
./install.py --profile minimal

# Recommended (VibeVoice + Kokoro fallback)
./install.py --profile recommended

# Custom
./install.py --engines vibevoice,dia2 --gpu cuda
```

---

## 15. Configuration Model (Client-Owned)

```json
{
  "hearme": {
    "audio": {
      "engine": "vibevoice",
      "fallback_engine": "kokoro",
      "voices": "auto",
      "format": "mp3"
    },
    "defaults": {
      "mode": "agent-decided",
      "length": "balanced"
    },
    "output": {
      "dir": ".hearme"
    },
    "privacy": {
      "allow_network": false
    },
    "installation": {
      "models_dir": "~/.hearme/models",
      "venv_path": "~/.hearme/venv"
    }
  }
}
```

---

## 16. Output Artifacts

```
.hearme/
  hearme.audio.mp3
  hearme.script.txt
  hearme.script.json
  hearme.meta.json
```

---

## 17. Error Handling & Degradation

- Missing README → ask agent/user
- Unsupported multi-speaker → fallback to single speaker
- Audio failure → script-only output
- Partial success is acceptable and reported

---

## 18. Security & Privacy

> [!CAUTION]
> HEARME is **local-first by default**. No data leaves the user's machine unless they explicitly consent.

### Privacy Principles

- **All processing is local** – documents, scripts, and audio stay on-device
- **No telemetry** – no usage data, analytics, or crash reports sent anywhere
- **No document exfiltration** – content is never uploaded to external services
- **Explicit consent for network** – any network access requires `"allow_network": true` in config

### Network Access Scenarios

Network access may be requested for:
- Downloading TTS model weights (first-time setup only)
- Checking for model updates (if enabled)

These actions:
1. Require explicit user consent via configuration
2. Display clear prompts explaining what will be downloaded
3. Support fully offline operation after initial setup

---

## 19. Portability & Viability

- No vendor lock-in
- No cloud dependency
- No account requirement
- Reproducible behavior

---

## 20. Non-Goals

- No embedded LLM
- No hardcoded personality
- No UI assumptions
- No cloud-only operation

---

## 21. Extensibility (Future)

- CI-based HEARME generation
- Multi-language narration
- Accessibility-focused output
- Repo-wide audio indexing

---

## 22. Final Positioning

HEARME is not a TTS tool or summarizer.

HEARME **is**:
A local-first, privacy-respecting, documentation-to-audio execution layer powered by the intelligence of the invoking agent.
