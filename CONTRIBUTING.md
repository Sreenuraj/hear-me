# Contributing to HEARME

We love your input! We want to make contributing to HEARME as easy and transparent as possible.

## Development Setup

### fast setup for macOS
```bash
./scripts/dev-setup.sh
```

### Manual Setup
1. Fork the repo and clone it
2. Create virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Engine Setup

HEARME uses a plugin-like architecture for TTS engines.

### 1. Install optional engines
```bash
# High quality multi-speaker (requires ~2GB RAM)
pip install dia-tts torch

# Good quality single-speaker
pip install kokoro

# Lightweight fallback
pip install piper-tts
```

### 2. Verify setup
```bash
pytest tests/test_engines.py
```

## Running Tests

We use `pytest` for testing.

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_renderer.py

# Run with output
pytest -v -s
```

## Pull Requests

1. Fork the repo and create your branch from `main`.
2. Keep your PR small and focused.
3. Ensure all tests pass.
4. Add tests for new features.

## Code Style

- We use standard Python style (PEP 8).
- Type hints are required for all implementation code.
- Docstrings are required for all public functions/classes.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
