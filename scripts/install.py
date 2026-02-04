#!/usr/bin/env python3
"""
HEARME Cross-Platform Installer

Install HEARME with optional TTS engines.
Works on macOS, Linux, and Windows.

Usage:
    python install.py                    # Interactive mode
    python install.py --engine dia2      # Install with Dia2
    python install.py --profile minimal  # Minimal installation
"""

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


# Installation profiles
PROFILES = {
    "minimal": {
        "description": "Just HEARME core (mock engine only)",
        "engines": [],
        "extras": [],
    },
    "recommended": {
        "description": "HEARME + Kokoro (good quality, works everywhere)",
        "engines": ["kokoro"],
        "extras": [],
    },
    "full": {
        "description": "All engines including Dia2 (best quality)",
        "engines": ["kokoro", "dia2", "piper"],
        "extras": ["torch"],
    },
}

# Engine configurations
ENGINES = {
    "dia2": {
        "package": "dia-tts",
        "requires": ["torch"],
        "quality": "⭐⭐⭐⭐",
        "multi_speaker": True,
        "memory_mb": 2000,
    },
    "kokoro": {
        "package": "kokoro",
        "requires": [],
        "quality": "⭐⭐⭐",
        "multi_speaker": False,
        "memory_mb": 300,
    },
    "piper": {
        "package": "piper-tts",
        "requires": [],
        "quality": "⭐⭐",
        "multi_speaker": False,
        "memory_mb": 50,
    },
}


def print_header():
    """Print installation header."""
    print()
    print("🎙️  HEARME Installer")
    print("=" * 40)
    print()


def detect_platform():
    """Detect current platform."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "darwin":
        if "arm" in machine:
            return "macos-arm64"
        return "macos-x64"
    elif system == "linux":
        return "linux"
    elif system == "windows":
        return "windows"
    return "unknown"


def check_python():
    """Check Python version."""
    version = sys.version_info
    if version < (3, 10):
        print(f"❌ Python 3.10+ required (found {version.major}.{version.minor})")
        sys.exit(1)
    print(f"✅ Python {version.major}.{version.minor}")


def pip_install(packages, quiet=True):
    """Install packages with pip."""
    if isinstance(packages, str):
        packages = [packages]
    
    cmd = [sys.executable, "-m", "pip", "install"] + packages
    if quiet:
        cmd.append("--quiet")
    
    try:
        subprocess.run(cmd, check=True, capture_output=quiet)
        return True
    except subprocess.CalledProcessError:
        return False


def install_hearme():
    """Install HEARME core."""
    print("📥 Installing HEARME...")
    
    # Try PyPI first, then git
    if not pip_install("hearme"):
        # Fallback to local install (for development)
        script_dir = Path(__file__).parent.parent
        if (script_dir / "pyproject.toml").exists():
            pip_install(str(script_dir))
        else:
            print("❌ Failed to install HEARME")
            return False
    
    print("✅ HEARME installed")
    return True


def install_engine(name):
    """Install a TTS engine."""
    if name not in ENGINES:
        print(f"⚠️  Unknown engine: {name}")
        return False
    
    engine = ENGINES[name]
    packages = [engine["package"]] + engine.get("requires", [])
    
    print(f"🔊 Installing {name}...")
    if pip_install(packages):
        print(f"✅ {name} installed")
        return True
    else:
        print(f"⚠️  Failed to install {name}")
        return False


def generate_mcp_config(install_dir=None):
    """Generate MCP configuration JSON."""
    python_path = sys.executable
    
    config = {
        "mcpServers": {
            "hearme": {
                "command": python_path,
                "args": ["-m", "hearme"]
            }
        }
    }
    
    return json.dumps(config, indent=2)


def verify_installation():
    """Verify HEARME is working."""
    print()
    print("🧪 Verifying installation...")
    
    try:
        from hearme import __version__
        from hearme.engines import get_engine, list_engines
        
        print(f"✅ HEARME v{__version__}")
        
        # Check available engines
        engines = list_engines()
        available = [e.name for e in engines if get_engine(e.name) and get_engine(e.name).is_available()]
        print(f"✅ Engines: {', '.join(available) if available else 'mock only'}")
        
        return True
    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
        return False


def interactive_mode():
    """Run interactive installation."""
    print("Select installation profile:")
    print()
    for i, (name, profile) in enumerate(PROFILES.items(), 1):
        print(f"  {i}. {name.capitalize()}: {profile['description']}")
    print()
    
    choice = input("Enter choice [2]: ").strip() or "2"
    
    try:
        idx = int(choice) - 1
        profile_name = list(PROFILES.keys())[idx]
    except (ValueError, IndexError):
        profile_name = "recommended"
    
    return profile_name


def main():
    parser = argparse.ArgumentParser(description="Install HEARME")
    parser.add_argument("--engine", help="TTS engine to install")
    parser.add_argument("--profile", choices=PROFILES.keys(), help="Installation profile")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    args = parser.parse_args()
    
    print_header()
    
    # Check platform
    plat = detect_platform()
    print(f"🖥️  Platform: {plat}")
    
    # Check Python
    check_python()
    print()
    
    # Determine what to install
    if args.profile:
        profile = PROFILES[args.profile]
        engines = profile["engines"]
    elif args.engine:
        engines = [args.engine]
    elif args.non_interactive:
        engines = PROFILES["recommended"]["engines"]
    else:
        profile_name = interactive_mode()
        profile = PROFILES[profile_name]
        engines = profile["engines"]
    
    # Install HEARME
    if not install_hearme():
        sys.exit(1)
    
    # Install engines
    for engine in engines:
        install_engine(engine)
    
    # Verify
    verify_installation()
    
    # Generate and display MCP config
    print()
    print("=" * 40)
    print("✅ Installation Complete!")
    print("=" * 40)
    print()
    print("Add this to your MCP client config:")
    print()
    print(generate_mcp_config())
    print()


if __name__ == "__main__":
    main()
