# HEARME Implementation Roadmap

> **Building the tool that replaces README.md with hearme.mp3**

This document tracks the phased implementation of HEARME MCP – transforming project documentation into natural, conversational audio.

---

## Phase 1: Foundation

**Timeline:** Weeks 1-2  
**Goal:** Establish MCP server skeleton and core infrastructure

### Tasks

- [x] **1.1 MCP Server Setup**
  - [x] Initialize Python MCP server using `mcp-python-sdk`
  - [x] Define tool interface stubs for all 6 core tools
  - [x] Implement server configuration loading
  - [x] Create development environment setup script

- [x] **1.2 Prerequisite Detection System**
  - [x] Implement platform detection (macOS/Linux/Windows)
  - [x] Create Python version checker
  - [x] Build audio engine availability scanner
  - [x] Implement system dependency checker (ffmpeg, espeak-ng)
  - [x] Design `PrerequisiteReport` schema

- [x] **1.3 Configuration System**
  - [x] Define JSON configuration schema
  - [x] Implement config file discovery (`hearme.json`, MCP settings)
  - [x] Create config validation and defaults
  - [x] Handle privacy settings (`allow_network`)

### Deliverables
- ✅ MCP server responds to `check_prerequisites` tool
- ✅ Configuration loads and validates correctly
- ✅ Server runs locally with `python -m hearme`
- ✅ 18 tests passing

---

## Phase 2: Document Pipeline

**Timeline:** Weeks 3-4  
**Goal:** Implement document discovery, parsing, and classification

### Tasks

- [x] **2.1 Workspace Scanning (`scan_workspace`)**
  - [x] Implement directory traversal with gitignore support
  - [x] Detect documentation files (README, ARCHITECTURE, /docs/)
  - [x] Generate file metadata (size, path, type)
  - [x] Handle large repository limits

- [x] **2.2 Document Analysis (`analyze_documents`)**
  - [x] Parse Markdown structure (headings, sections)
  - [x] Extract document signals (keywords, patterns)
  - [x] Classify document type (architecture, contributing, etc.)
  - [x] Preserve document boundaries for multi-doc context

- [x] **2.3 Audio Context Preparation (`prepare_audio_context`)**
  - [x] Transform document structure for spoken narrative
  - [x] Remove non-speakable elements (tables, code blocks → descriptions)
  - [x] Generate speaker hints for multi-voice scenarios
  - [x] Apply length constraints (overview/balanced/thorough)

- [x] **2.4 Audio Plan Proposal (`propose_audio_plan`)**
  - [x] Suggest document ordering and prioritization
  - [x] Identify ambiguities for agent resolution
  - [x] Propose speaker assignments based on content
  - [x] Estimate output duration

### Deliverables
- ✅ `scan_workspace` returns classified document list
- ✅ `analyze_documents` outputs structured metadata
- ✅ `prepare_audio_context` produces LLM-ready narrative context
- ✅ Full document pipeline testable end-to-end (40 tests passing)

---

## Phase 3: Audio Generation

**Timeline:** Weeks 5-7  
**Goal:** Implement audio engine abstraction and multi-speaker rendering

### Tasks

- [x] **3.1 Engine Abstraction Layer**
  - [x] Define `AudioEngine` interface/protocol
  - [x] Implement engine registry and selection
  - [x] Handle fallback chain logic
  - [x] Create engine capability introspection

- [x] **3.2 Kokoro Integration (Tier 3 Fallback)**
  - [x] Implement `KokoroEngine` class
  - [x] Handle model loading and caching
  - [x] Single-speaker audio generation
  - [x] WAV output encoding

- [x] **3.3 Mock Engine (Development)**
  - [x] Implement `MockEngine` for testing
  - [x] Returns placeholder silent audio

- [x] **3.4 Audio Rendering (`render_audio`)**
  - [x] Parse script format (`{speaker, text}` array)
  - [x] Apply voice mapping to speaker labels
  - [x] Handle pause/timing hints
  - [x] Concatenate multi-segment audio
  - [x] Export to configured format

- [x] **3.5 Output Persistence (`persist_outputs`)**
  - [x] Write audio file to `.hearme/` directory
  - [x] Generate script files (txt, json)
  - [x] Create metadata manifest
  - [x] Handle file naming and overwrites

### Deliverables
- ✅ Audio generated from agent-provided script
- ✅ Multi-speaker conversations with voice mapping
- ✅ Mock engine for development, Kokoro for production
- ✅ Output files properly persisted with manifest (59 tests passing)

---

## Phase 3.5: Enhanced TTS Engines

**Timeline:** Weeks 7-8  
**Goal:** Add high-quality multi-speaker TTS engines for NotebookLM-like audio

> **Fallback Chain:** VibeVoice → Dia2 → Kokoro → Piper

### TTS Engine Quality Comparison

| Engine | Quality | Multi-Speaker | MacBook Pro | GPU Required |
|--------|---------|---------------|-------------|--------------|
| **VibeVoice** | ⭐⭐⭐⭐⭐ | Yes (4+) | ✅ MPS | Optional |
| **Dia2** | ⭐⭐⭐⭐ | Yes (2) | ✅ CPU/MPS | No |
| **Kokoro** | ⭐⭐⭐ | No | ✅ CPU | No |
| **Piper** | ⭐⭐ | No | ✅ CPU | No |

### Tasks

- [ ] **3.5.1 Dia2 Integration (Multi-Speaker)**
  - [ ] Implement `Dia2Engine` class
  - [ ] Two-speaker conversational synthesis
  - [ ] Apple Silicon MPS acceleration
  - [ ] ~2GB RAM requirement handling
  - [ ] Voice style configuration

- [ ] **3.5.2 Piper Integration (Lightweight Fallback)**
  - [ ] Implement `PiperEngine` class
  - [ ] ONNX-based fast synthesis
  - [ ] Multiple voice model support
  - [ ] Ultra-low resource usage

- [ ] **3.5.3 VibeVoice Integration (Premium)**
  - [ ] Implement `VibeVoiceEngine` class
  - [ ] 4+ speaker synthesis
  - [ ] NotebookLM-style conversational audio
  - [ ] Long-form chunking (90+ minutes)
  - [ ] GPU acceleration (optional)

- [ ] **3.5.4 Fallback Chain Logic**
  - [ ] Auto-detect available engines on startup
  - [ ] Priority-based engine selection
  - [ ] Graceful degradation (multi → single speaker)
  - [ ] User override via config

### Deliverables
- Dia2 produces NotebookLM-like two-host conversations
- Piper provides fast fallback for resource-constrained systems
- VibeVoice available for premium quality when GPU present
- All engines work on MacBook Pro (M1/M2/M3)

---

## Phase 4: Installation & UX

**Timeline:** Week 8  
**Goal:** Create frictionless installation experience across platforms

### Tasks

- [ ] **4.1 macOS Installer Script**
  - [ ] Homebrew dependency installation
  - [ ] Python venv creation
  - [ ] Engine-specific model downloads
  - [ ] MCP config JSON output

- [ ] **4.2 Linux Installer Script**
  - [ ] Support apt/dnf/pacman package managers
  - [ ] Handle CUDA detection for GPU engines
  - [ ] Model downloading with progress

- [ ] **4.3 Cross-Platform Python Installer**
  - [ ] `install.py` with profile support (minimal/recommended/full)
  - [ ] Dependency verification
  - [ ] Interactive and non-interactive modes

- [ ] **4.4 Installation Validation**
  - [ ] Generate test audio (5-second sample)
  - [ ] Verify engine functionality
  - [ ] Output success/failure report

- [ ] **4.5 First-Run Experience**
  - [ ] Detect first run via missing config
  - [ ] Guide through engine selection
  - [ ] Provide sample commands to agent

### Deliverables
- `./install-macos.sh --engine vibevoice` works end-to-end
- Installation outputs ready-to-use MCP config
- User hears sample audio after successful install

---

## Phase 5: Polish & Release

**Timeline:** Weeks 9-10  
**Goal:** Production-quality error handling, documentation, and release prep

### Tasks

- [ ] **5.1 Error Handling & Degradation**
  - [ ] Graceful failure for missing engines
  - [ ] Multi-speaker → single-speaker fallback
  - [ ] Script-only output on audio failure
  - [ ] Clear error messages for agents

- [ ] **5.2 Testing Suite**
  - [ ] Unit tests for document pipeline
  - [ ] Integration tests for audio generation
  - [ ] Cross-platform install script tests
  - [ ] CI/CD pipeline setup (GitHub Actions)

- [ ] **5.3 Documentation**
  - [ ] Complete API reference for all tools
  - [ ] Engine comparison guide with samples
  - [ ] Troubleshooting guide
  - [ ] Agent integration examples (PostQode, Cline)

- [ ] **5.4 Release Preparation**
  - [ ] Version tagging and changelog
  - [ ] PyPI package publication
  - [ ] GitHub Release with binaries
  - [ ] Announcement assets (demo audio, screenshots)

### Deliverables
- All tests pass on macOS, Linux
- Documentation complete and published
- v0.1.0 released on PyPI and GitHub

---

## Progress Summary

| Phase | Status | Progress |
|-------|--------|----------|
| Phase 1: Foundation | ✅ Complete | 100% |
| Phase 2: Document Pipeline | ✅ Complete | 100% |
| Phase 3: Audio Generation | ✅ Complete | 100% |
| Phase 3.5: Enhanced TTS Engines | 🔲 Not Started | 0% |
| Phase 4: Installation & UX | 🔲 Not Started | 0% |
| Phase 5: Polish & Release | 🔲 Not Started | 0% |

---

## Legend

- [ ] Task not started
- [/] Task in progress
- [x] Task completed
- 🔲 Phase not started
- 🔶 Phase in progress
- ✅ Phase completed
