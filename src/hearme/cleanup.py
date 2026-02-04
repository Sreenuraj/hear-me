"""
hear-me Cleanup Utilities

Provides process cleanup and engine resource cleanup helpers.
"""

from __future__ import annotations

import os
import platform
import subprocess
from typing import List


def cleanup_resources() -> dict:
    """Force cleanup of loaded TTS engine resources."""
    from hearme.engines.registry import EngineRegistry

    cleaned: List[str] = []

    for name in list(EngineRegistry._instances.keys()):
        engine = EngineRegistry._instances[name]
        if hasattr(engine, "is_loaded") and engine.is_loaded():
            engine.unload()
            cleaned.append(name)

    return {
        "success": True,
        "cleaned_engines": cleaned,
        "message": f"Cleaned {len(cleaned)} engine(s). Memory freed.",
    }


def kill_stale_processes() -> dict:
    """Best-effort termination of stale hear-me/Dia2 processes."""
    system = platform.system().lower()
    killed = []
    errors = []

    if system in ("darwin", "linux"):
        patterns = [
            "python.*-m hearme",
            "uv run -m dia2.cli",
        ]
        for pattern in patterns:
            try:
                subprocess.run(["pkill", "-f", pattern], check=False)
                killed.append(pattern)
            except Exception as e:
                errors.append(f"{pattern}: {e}")
    else:
        errors.append("Process cleanup not implemented for this OS")

    return {
        "success": len(errors) == 0,
        "killed_patterns": killed,
        "errors": errors,
    }


def cli_cleanup() -> int:
    """CLI entry for cleanup: kill processes and unload engines."""
    proc = kill_stale_processes()
    res = cleanup_resources()
    print(proc)
    print(res)
    return 0
