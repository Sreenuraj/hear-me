#!/usr/bin/env python3
"""
hear-me Cross-Platform Installer

Install hear-me with optional TTS engines.
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
import ctypes
from pathlib import Path


# Installation profiles
PROFILES = {
    "minimal": {
        "description": "Just hear-me core (mock engine only)",
        "engines": [],
        "extras": [],
    },
    "recommended": {
        "description": "hear-me + Kokoro (good quality, works everywhere)",
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
        "package": ".[dia2]",  # Install local package with extras
        "requires": ["torch", "transformers"],
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
    print("🎙️  hear-me Installer")
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


def get_ram_gb():
    """Return total system RAM in GB."""
    system = platform.system().lower()
    if system == "darwin":
        try:
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"]).decode().strip()
            return int(out) / (1024 ** 3)
        except Exception:
            return 0
    if system == "linux":
        try:
            with open("/proc/meminfo") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb / (1024 ** 2)
        except Exception:
            return 0
    if system == "windows":
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
            return stat.ullTotalPhys / (1024 ** 3)
    return 0


def get_free_disk_gb(path):
    """Return free disk space in GB for a path."""
    try:
        usage = shutil.disk_usage(path)
        return usage.free / (1024 ** 3)
    except Exception:
        return 0


def check_system_requirements(engine, install_dir):
    """Check RAM and disk requirements for chosen engine."""
    min_ram_gb = 4
    min_disk_gb = 2
    if engine == "dia2":
        min_ram_gb = 16
        min_disk_gb = 8
    elif engine == "piper":
        min_ram_gb = 2
        min_disk_gb = 1

    ram_gb = get_ram_gb()
    disk_gb = get_free_disk_gb(install_dir)

    print(f"🧠 System check: RAM {ram_gb:.1f}GB, Free disk {disk_gb:.1f}GB")
    if ram_gb < min_ram_gb:
        print(f"❌ Not enough RAM for {engine} (need {min_ram_gb}GB+)")
        sys.exit(1)
    if disk_gb < min_disk_gb:
        print(f"❌ Not enough free disk for {engine} (need {min_disk_gb}GB+)")
        sys.exit(1)

    if engine == "dia2" and platform.system().lower() == "darwin":
        if platform.machine().lower() != "arm64":
            print("⚠️  Dia2 on Intel Macs will run CPU-only and may be very slow.")


def check_command_exists(cmd):
    """Check if a command exists on PATH."""
    return shutil.which(cmd) is not None


def install_system_deps(plat):
    """Install or verify system dependencies."""
    deps = ["ffmpeg", "espeak-ng"]
    missing = [d for d in deps if not check_command_exists(d)]
    if not missing:
        print("✅ System dependencies present")
        return True

    print(f"📦 Missing system dependencies: {', '.join(missing)}")
    if plat.startswith("macos"):
        if check_command_exists("brew"):
            cmd = ["brew", "install"] + missing
            subprocess.run(cmd, check=False)
        else:
            print("❌ Homebrew not found. Install it and re-run.")
            return False
    elif plat == "linux":
        if check_command_exists("apt-get"):
            cmd = ["sudo", "apt-get", "update"]
            subprocess.run(cmd, check=False)
            cmd = ["sudo", "apt-get", "install", "-y"] + missing
            subprocess.run(cmd, check=False)
        else:
            print("❌ apt-get not found. Install dependencies manually.")
            return False
    else:
        print("❌ Please install dependencies manually and re-run.")
        return False

    still_missing = [d for d in deps if not check_command_exists(d)]
    if still_missing:
        print(f"❌ Still missing: {', '.join(still_missing)}")
        return False

    print("✅ System dependencies installed")
    return True


def install_uv(plat):
    """Ensure uv is installed (required for Dia2 runtime)."""
    if check_command_exists("uv"):
        return True
    if plat.startswith("macos"):
        if check_command_exists("brew"):
            subprocess.run(["brew", "install", "uv"], check=False)
        else:
            print("❌ Homebrew not found. Install uv and re-run.")
            return False
    elif plat == "linux":
        if check_command_exists("apt-get"):
            subprocess.run(["sudo", "apt-get", "update"], check=False)
            subprocess.run(["sudo", "apt-get", "install", "-y", "uv"], check=False)
        else:
            print("❌ apt-get not found. Install uv and re-run.")
            return False
    else:
        print("❌ Please install uv manually and re-run.")
        return False

    return check_command_exists("uv")


def install_dia2_repo(install_dir):
    """Clone and sync Dia2 repo using uv."""
    repo_dir = (install_dir / "engines" / "dia2").resolve()
    repo_dir.parent.mkdir(parents=True, exist_ok=True)
    if (repo_dir / ".git").exists():
        subprocess.run(["git", "-C", str(repo_dir), "pull", "--rebase"], check=False)
    else:
        subprocess.run(["git", "clone", "https://github.com/nari-labs/dia2", str(repo_dir)], check=False)

    print("⏳ Syncing Dia2 dependencies with uv...")
    env = os.environ.copy()
    env.pop("VIRTUAL_ENV", None)
    subprocess.run(["uv", "sync"], cwd=str(repo_dir), check=False, env=env)

    # Verify torch in dia2 runtime, retry sync if needed
    print("🧪 Verifying Dia2 runtime dependencies (torch)...")
    check = subprocess.run(["uv", "run", "python", "-c", "import torch; print(torch.__version__)"], cwd=str(repo_dir), check=False, env=env)
    if check.returncode != 0:
        print("⚠️  Dia2 dependency check failed, retrying uv sync...")
        subprocess.run(["uv", "sync"], cwd=str(repo_dir), check=False, env=env)
        check = subprocess.run(["uv", "run", "python", "-c", "import torch; print(torch.__version__)"], cwd=str(repo_dir), check=False, env=env)
        if check.returncode != 0:
            print("❌ Dia2 dependencies not installed (torch missing).")
            sys.exit(1)

    # Pre-download via CLI to validate (skip if cache already exists)
    hf_home = Path(os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface")))
    dia2_cache = hf_home / "hub" / "models--nari-labs--Dia2-2B"
    if dia2_cache.exists():
        print("✅ Dia2 model cache found, skipping download")
    else:
        input_path = repo_dir / "install-check.txt"
        input_path.write_text("[S1] Hello. [S2] This is a Dia2 install check.", encoding="utf-8")
        for attempt in range(1, 3):
            result = subprocess.run(
                ["uv", "run", "-m", "dia2.cli", "--hf", "nari-labs/Dia2-2B", "--input", str(input_path), str(repo_dir / "install-check.wav")],
                cwd=str(repo_dir),
                check=False,
                env=env,
            )
            if result.returncode == 0:
                break
            print(f"⚠️  Dia2 download attempt {attempt} failed, retrying...")

    return repo_dir


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


def install_hearme(root_dir):
    """Install hear-me core."""
    print("📥 Installing hear-me...")
    
    # Check if running from source repo
    if (root_dir / "pyproject.toml").exists():
        print(f"📦 Installing from local source: {root_dir}")
        # Install in editable mode for dev convenience, or normal for users
        if pip_install(["-e", str(root_dir)]):
            print("✅ hear-me installed from source")
            return True
    
    # Fallback to PyPI
    print("⚠️  Installing from PyPI...")
    if pip_install("hear-me"):
        print("✅ hear-me installed from PyPI")
        return True
        
    print("❌ Failed to install hear-me")
    return False


def install_engine(name, root_dir):
    """Install a TTS engine."""
    if name not in ENGINES:
        print(f"⚠️  Unknown engine: {name}")
        return False
    
    engine = ENGINES[name]
    packages = [engine["package"]] + engine.get("requires", [])

    if name == "dia2":
        packages = []
    
    print(f"🔊 Installing {name}...")
    if pip_install(packages):
        # Trigger pre-download for installed engine
        print(f"⏳ Pre-downloading {name} models...")
        script_path = Path(__file__).parent / "download_models.py"
        try:
             subprocess.run([sys.executable, str(script_path), "--engine", name], check=True)
        except subprocess.CalledProcessError:
             print(f"⚠️  {name} model download failed (or skipped). It will be attempted at runtime.")
        
        print(f"✅ {name} installed")
        return True
    else:
        print(f"⚠️  Failed to install {name}")
        return False


def generate_mcp_config(install_dir, engine_name):
    """Generate MCP configuration JSON."""
    python_path = sys.executable
    
    config = {
        "mcpServers": {
            "hear-me": {
                "command": python_path,
                "args": ["-m", "hearme"]
            }
        }
    }
    
    mcp_config_path = install_dir / "mcp_config.json"
    mcp_config_path.write_text(json.dumps(config, indent=2))
    print(f"✅ MCP config saved to: {mcp_config_path}")
    
    # Generate app config (to set default engine)
    app_config = {
        "hear-me": {
            "audio": {
                "engine": engine_name
            },
            "installation": {
                "dia2_repo_dir": str((install_dir / "engines" / "dia2").resolve())
            }
        }
    }
    app_config_path = install_dir / "config.json"
    app_config_path.write_text(json.dumps(app_config, indent=2))
    print(f"✅ Default engine set to: {engine_name}")

    return json.dumps(config, indent=2)


def verify_installation():
    """Verify hear-me is working."""
    print()
    print("🧪 Verifying installation...")
    
    try:
        from hearme import __version__
        from hearme.engines import get_engine, list_engines
        
        print(f"✅ hear-me v{__version__}")
        
        # Check available engines
        engines = list_engines()
        available = [e.name for e in engines if get_engine(e.name) and get_engine(e.name).is_available()]
        print(f"✅ Engines: {', '.join(available) if available else 'mock only'}")
        
        return True
    except Exception as e:
        print(f"⚠️  Verification failed: {e}")
        return False


def smoke_test(engine_name, output_path):
    """Render a short audio sample using the chosen engine."""
    print()
    print(f"🧪 Rendering a short audio sample with {engine_name}...")
    script = [
        {"speaker": "narrator", "text": "Install check. Audio synthesis is working."},
    ]
    try:
        from hearme.renderer import render_audio
        result = render_audio(script=script, output_path=output_path, engine_name=engine_name)
        if not result.success:
            print(f"❌ Smoke test failed: {result.error}")
            sys.exit(1)
        print(f"✅ Audio sample created: {result.output_path}")
    except Exception as e:
        print(f"❌ Smoke test failed: {e}")
        sys.exit(1)


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
    parser = argparse.ArgumentParser(description="Install hear-me")
    parser.add_argument("--engine", help="TTS engine to install")
    parser.add_argument("--profile", choices=PROFILES.keys(), help="Installation profile")
    parser.add_argument("--non-interactive", action="store_true", help="Non-interactive mode")
    parser.add_argument("--skip-smoke-test", action="store_true", help="Skip final audio smoke test")
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
    
    install_dir = Path(os.environ.get("HEARME_INSTALL_DIR", str(Path.home() / ".hear-me"))).resolve()
    install_dir.mkdir(parents=True, exist_ok=True)
    root_dir = Path(__file__).parent.resolve().parent
    engine_name = engines[0] if engines else "mock"

    # System checks
    check_system_requirements(engine_name, install_dir)
    if not install_system_deps(plat):
        sys.exit(1)
    if engine_name == "dia2" and not install_uv(plat):
        sys.exit(1)

    # Install hear-me
    if not install_hearme(root_dir):
        sys.exit(1)
    
    # Install engines
    for engine in engines:
        if engine == "dia2":
            install_dia2_repo(install_dir)
        install_engine(engine, root_dir)
    
    # Verify
    verify_installation()
    if engines and not args.skip_smoke_test:
        smoke_test(engine_name, str(install_dir / "install-test.wav"))
    elif args.skip_smoke_test:
        print("⚠️  Skipping smoke test (per flag)")
    
    # Generate and display MCP config
    print()
    print("=" * 40)
    print("✅ Installation Complete!")
    print("=" * 40)
    print()
    print("Add this to your MCP client config:")
    print()
    print(generate_mcp_config(install_dir, engine_name))
    print()


if __name__ == "__main__":
    main()
