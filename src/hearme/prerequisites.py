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


def check_audio_engine(engine: str) -> EngineStatus:
    """Check if an audio engine is available."""
    # Engine-specific checks
    engine_checks = {
        "vibevoice": _check_vibevoice,
        "dia2": _check_dia2,
        "chattts": _check_chattts,
        "kokoro": _check_kokoro,
        "piper": _check_piper,
        "xtts": _check_xtts,
    }
    
    checker = engine_checks.get(engine.lower())
    if checker:
        return checker()
    
    return EngineStatus(installed=False, install_command=f"Unknown engine: {engine}")


def _check_vibevoice() -> EngineStatus:
    """Check VibeVoice availability."""
    try:
        # VibeVoice is typically installed as a Python package
        import importlib.util
        spec = importlib.util.find_spec("vibevoice")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=["torch", "transformers"])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["torch", "transformers", "vibevoice"],
        install_command="pip install vibevoice"
    )


def _check_dia2() -> EngineStatus:
    """Check Dia2 availability."""
    try:
        import importlib.util
        spec = importlib.util.find_spec("dia")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=["torch", "soundfile"])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["torch", "soundfile", "dia"],
        install_command="pip install dia-tts"
    )


def _check_chattts() -> EngineStatus:
    """Check ChatTTS availability."""
    try:
        import importlib.util
        spec = importlib.util.find_spec("ChatTTS")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=["torch"])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["torch", "ChatTTS"],
        install_command="pip install ChatTTS"
    )


def _check_kokoro() -> EngineStatus:
    """Check Kokoro availability."""
    try:
        import importlib.util
        spec = importlib.util.find_spec("kokoro")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=["onnxruntime"])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["onnxruntime", "kokoro"],
        install_command="pip install kokoro-onnx"
    )


def _check_piper() -> EngineStatus:
    """Check Piper TTS availability."""
    # Check for piper command
    piper_path = shutil.which("piper")
    if piper_path:
        return EngineStatus(installed=True, required_deps=[])
    
    # Check for Python package
    try:
        import importlib.util
        spec = importlib.util.find_spec("piper")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=[])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["piper-tts"],
        install_command="pip install piper-tts"
    )


def _check_xtts() -> EngineStatus:
    """Check XTTS-v2 (Coqui) availability."""
    try:
        import importlib.util
        spec = importlib.util.find_spec("TTS")
        if spec is not None:
            return EngineStatus(installed=True, required_deps=["torch"])
    except Exception:
        pass
    
    return EngineStatus(
        installed=False,
        required_deps=["torch", "TTS"],
        install_command="pip install TTS"
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
    engines = ["vibevoice", "dia2", "chattts", "kokoro", "piper", "xtts"]
    audio_engines = {name: check_audio_engine(name) for name in engines}
    
    # Check system dependencies
    system_deps = {
        "ffmpeg": check_command_exists("ffmpeg"),
        "espeak-ng": check_command_exists("espeak-ng"),
    }
    
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
            install_cmd = "brew install ffmpeg && pip install kokoro-onnx"
        elif plat == "linux":
            install_cmd = "apt install ffmpeg && pip install kokoro-onnx"
        else:
            install_cmd = "pip install kokoro-onnx"
    
    return PrerequisiteReport(
        platform=plat,
        platform_name=plat_name,
        python_version=py_version,
        python_ok=py_ok,
        audio_engines=audio_engines,
        system_deps=system_deps,
        ready=ready,
        missing=missing,
        install_command=install_cmd,
    )
