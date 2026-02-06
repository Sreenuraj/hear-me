"""
hear-me Prerequisite Detection System

Detects platform, Python version, audio engines, and system dependencies.
Provides actionable installation guidance when prerequisites are missing.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class DependencyStatus:
    """Status of a single dependency."""
    installed: bool
    version: str | None = None
    path: str | None = None
    install_hint: str | None = None


@dataclass
class EngineStatus:
    """Status of an audio engine."""
    installed: bool
    version: str | None = None
    required_deps: list[str] = field(default_factory=list)
    install_command: str | None = None


@dataclass 
class PrerequisiteReport:
    """Complete prerequisite check report."""
    platform: Literal["darwin", "linux", "windows"]
    platform_name: str
    python_version: str
    python_ok: bool
    
    audio_engines: dict[str, EngineStatus]
    system_deps: dict[str, DependencyStatus]
    
    ready: bool
    missing: list[str]
    install_command: str | None
    model_cache: dict[str, bool] = field(default_factory=dict)
    engine_status: dict[str, str] = field(default_factory=dict)
    
    def model_dump(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "platform": self.platform,
            "platform_name": self.platform_name,
            "python_version": self.python_version,
            "python_ok": self.python_ok,
            "audio_engines": {
                name: {
                    "installed": engine.installed,
                    "version": engine.version,
                    "required_deps": engine.required_deps,
                    "install_command": engine.install_command,
                }
                for name, engine in self.audio_engines.items()
            },
            "system_deps": {
                name: {
                    "installed": dep.installed,
                    "version": dep.version,
                    "path": dep.path,
                    "install_hint": dep.install_hint,
                }
                for name, dep in self.system_deps.items()
            },
            "model_cache": self.model_cache,
            "engine_status": self.engine_status,
            "ready": self.ready,
            "missing": self.missing,
            "install_command": self.install_command,
        }


def detect_platform() -> tuple[Literal["darwin", "linux", "windows"], str]:
    """Detect the current platform."""
    system = platform.system().lower()
    
    if system == "darwin":
        # Get macOS version
        mac_ver = platform.mac_ver()[0]
        return "darwin", f"macOS {mac_ver}"
    elif system == "linux":
        # Try to get distribution info
        try:
            import distro
            name = distro.name(pretty=True)
        except ImportError:
            name = "Linux"
        return "linux", name
    elif system == "windows":
        win_ver = platform.win32_ver()[0]
        return "windows", f"Windows {win_ver}"
    else:
        return "linux", system  # Default to linux-like


def check_python_version() -> tuple[str, bool]:
    """Check Python version (requires 3.10+)."""
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 10)
    return version, ok


def check_command_exists(cmd: str) -> DependencyStatus:
    """Check if a command exists and get its version."""
    path = shutil.which(cmd)
    
    if path is None:
        # Provide installation hints based on command
        hints = {
            "ffmpeg": "brew install ffmpeg (macOS) / apt install ffmpeg (Linux)",
            "espeak-ng": "brew install espeak-ng (macOS) / apt install espeak-ng (Linux)",
        }
        return DependencyStatus(
            installed=False,
            install_hint=hints.get(cmd, f"Install {cmd} using your package manager")
        )
    
    # Try to get version
    version = None
    try:
        result = subprocess.run(
            [cmd, "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        # Extract first line of version output
        if result.stdout:
            version = result.stdout.strip().split("\n")[0][:50]
    except Exception:
        pass
    
    return DependencyStatus(installed=True, version=version, path=path)


def _get_engine_deps(engine: str) -> list[str]:
    """Get required dependencies for an engine."""
    deps = {
        "dia2": ["torch", "transformers", "dia2"],
        "kokoro": ["kokoro"],
        "piper": ["piper-tts"],
    }
    return deps.get(engine.lower(), [])


def _get_install_command(engine: str) -> str | None:
    """Get install command for an engine."""
    commands = {
        "dia2": "pip install \"dia2 @ git+https://github.com/nari-labs/dia2\"",
        "kokoro": "pip install kokoro",
        "piper": "pip install piper-tts",
    }
    return commands.get(engine.lower())


def check_audio_engine(engine: str) -> EngineStatus:
    """
    Check if an audio engine is available using the registry.
    
    This ensures consistent detection with render_audio and other tools.
    """
    try:
        # Import here to avoid circular imports
        from hearme.engines.registry import get_engine
        
        # Try to get engine from registry
        engine_instance = get_engine(engine.lower())
        
        if engine_instance and engine_instance.is_available():
            return EngineStatus(
                installed=True,
                required_deps=_get_engine_deps(engine),
            )
    except Exception:
        pass  # Fall through to not-installed case
    
    # Not available - return install hints
    return EngineStatus(
        installed=False,
        required_deps=_get_engine_deps(engine),
        install_command=_get_install_command(engine),
    )


def check_all_prerequisites() -> PrerequisiteReport:
    """
    Run complete prerequisite check.
    
    Returns a detailed report with:
    - Platform info
    - Python version check
    - Audio engine availability
    - System dependency status
    - Overall readiness
    - Installation guidance
    """
    # Platform detection
    plat, plat_name = detect_platform()
    
    # Python version
    py_version, py_ok = check_python_version()
    
    # Check all audio engines
    engines = ["dia2", "kokoro", "piper"]
    audio_engines = {name: check_audio_engine(name) for name in engines}
    
    # Check system dependencies
    system_deps = {
        "ffmpeg": check_command_exists("ffmpeg"),
        "espeak-ng": check_command_exists("espeak-ng"),
    }

    # Model cache presence (best-effort)
    model_cache = {}
    try:
        from pathlib import Path
        import os
        hf_home = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))
        model_cache["dia2"] = (hf_home / "hub" / "models--nari-labs--Dia2-2B").exists()
        model_cache["kokoro"] = (hf_home / "hub" / "models--hexgrad--Kokoro-82M").exists()
    except Exception:
        model_cache = {}
    
    # Determine what's missing
    missing = []
    
    if not py_ok:
        missing.append("python>=3.10")
    
    if not system_deps["ffmpeg"].installed:
        missing.append("ffmpeg")
    
    # Check if at least one engine is available
    any_engine = any(e.installed for e in audio_engines.values())
    if not any_engine:
        missing.append("audio_engine")
    
    # Determine overall readiness
    ready = len(missing) == 0
    
    # Generate install command
    install_cmd = None
    if not ready:
        if plat == "darwin":
            install_cmd = "brew install ffmpeg && pip install kokoro"
        elif plat == "linux":
            install_cmd = "apt install ffmpeg && pip install kokoro"
        else:
            install_cmd = "pip install kokoro"
    
    # Engine status hints
    engine_status = {}
    preferred = None
    if audio_engines.get("dia2") and audio_engines["dia2"].installed and model_cache.get("dia2"):
        preferred = "dia2"
    elif audio_engines.get("kokoro") and audio_engines["kokoro"].installed and model_cache.get("kokoro"):
        preferred = "kokoro"
    elif audio_engines.get("piper") and audio_engines["piper"].installed:
        preferred = "piper"
    engine_status["preferred_engine"] = preferred or "mock"

    return PrerequisiteReport(
        platform=plat,
        platform_name=plat_name,
        python_version=py_version,
        python_ok=py_ok,
        audio_engines=audio_engines,
        system_deps=system_deps,
        model_cache=model_cache,
        engine_status=engine_status,
        ready=ready,
        missing=missing,
        install_command=install_cmd,
    )
