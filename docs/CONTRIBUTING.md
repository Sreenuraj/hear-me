# Contributing to HEARME

Thank you for your interest in contributing to HEARME! This document provides guidelines for contributing.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Run the development setup:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e ".[dev]"
   ```

## Development Workflow

1. Create a feature branch from `main`
2. Make your changes
3. Run tests: `pytest`
4. Run linting: `ruff check .`
5. Submit a pull request

## Code Style

- Follow PEP 8 for Python code
- Use type hints for function signatures
- Write docstrings for public functions
- Keep functions focused and small

## Commit Messages

Use conventional commits:
- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `test:` Test additions/changes
- `refactor:` Code refactoring

## Pull Request Process

1. Update documentation if needed
2. Add tests for new functionality
3. Ensure all tests pass
4. Request review from maintainers

## Reporting Issues

When reporting bugs:
- Describe expected vs actual behavior
- Include OS, Python version, and audio engine
- Provide minimal reproduction steps

## Questions?

Open a discussion on GitHub or reach out to maintainers.
