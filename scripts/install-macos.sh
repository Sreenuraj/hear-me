#!/bin/bash
# hear-me macOS Installation Script
# Install hear-me with optional TTS engine setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}🎙️  hear-me Installer for macOS${NC}"
echo "=================================="
echo ""

# Parse arguments
ENGINE="kokoro"  # Default engine
PROFILE="recommended"
INSTALL_DIR="${HOME}/.hear-me"
SKIP_SMOKE_TEST=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --engine)
            ENGINE="$2"
            shift 2
            ;;
        --profile)
            PROFILE="$2"
            shift 2
            ;;
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        --skip-smoke-test)
            SKIP_SMOKE_TEST=1
            shift 1
            ;;
        --help)
            echo "Usage: ./install-macos.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --engine ENGINE    TTS engine: dia2, kokoro, piper (default: kokoro)"
            echo "  --profile PROFILE  Installation profile: minimal, recommended, full"
            echo "  --dir PATH         Installation directory (default: ~/.hear-me)"
            echo "  --skip-smoke-test  Skip the final audio render smoke test"
            echo ""
            echo "Engines:"
            echo "  dia2     NotebookLM-like multi-speaker (requires high RAM + disk)"
            echo "  kokoro   Good quality single-speaker (default)"
            echo "  piper    Fast, lightweight (low resources)"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Resolve script directory at the start, BEFORE changing directories
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "Engine:  ${GREEN}${ENGINE}${NC}"
echo -e "Profile: ${GREEN}${PROFILE}${NC}"
echo -e "Dir:     ${GREEN}${INSTALL_DIR}${NC}"
echo -e "Source:  ${GREEN}${ROOT_DIR}${NC}"
echo ""

# Check macOS
if [[ "$(uname)" != "Darwin" ]]; then
    echo -e "${RED}❌ This script is for macOS only${NC}"
    exit 1
fi
echo -e "${GREEN}✅ macOS detected${NC}"

# Stop any stale hear-me servers before install
echo ""
echo -e "${BLUE}🧹 Stopping stale hear-me servers (if any)...${NC}"
if pgrep -f "python.*-m hearme" >/dev/null 2>&1; then
    pkill -f "python.*-m hearme" || true
    echo -e "${GREEN}✅ Stopped existing hear-me server processes${NC}"
else
    echo -e "${GREEN}✅ No stale hear-me servers detected${NC}"
fi

# Check Python
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED="3.10"
if [ "$(printf '%s\n' "$REQUIRED" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED" ]; then
    echo -e "${RED}❌ Python $REQUIRED+ required (found $PYTHON_VERSION)${NC}"
    echo ""
    echo "Install Python with: brew install python@3.11"
    exit 1
fi
echo -e "${GREEN}✅ Python $PYTHON_VERSION${NC}"

# Helper: get RAM in GB
get_ram_gb() {
    local bytes
    bytes=$(sysctl -n hw.memsize)
    echo $((bytes / 1024 / 1024 / 1024))
}

# Helper: get free disk in GB for target directory
get_free_disk_gb() {
    local target="$1"
    local kb
    kb=$(df -k "$target" | tail -1 | awk '{print $4}')
    echo $((kb / 1024 / 1024))
}

# Engine requirements (minimums)
MIN_RAM_GB=4
MIN_DISK_GB=2
case "$ENGINE" in
    dia2)
        MIN_RAM_GB=16
        MIN_DISK_GB=8
        ;;
    kokoro)
        MIN_RAM_GB=4
        MIN_DISK_GB=2
        ;;
    piper)
        MIN_RAM_GB=2
        MIN_DISK_GB=1
        ;;
esac

RAM_GB=$(get_ram_gb)
DISK_GB=$(get_free_disk_gb "$(dirname "$INSTALL_DIR")")

echo -e "${BLUE}🧠 System check:${NC} RAM ${RAM_GB}GB, Free disk ${DISK_GB}GB"
if [ "$RAM_GB" -lt "$MIN_RAM_GB" ]; then
    echo -e "${RED}❌ Not enough RAM for ${ENGINE} (need ${MIN_RAM_GB}GB+)${NC}"
    exit 1
fi
if [ "$DISK_GB" -lt "$MIN_DISK_GB" ]; then
    echo -e "${RED}❌ Not enough free disk for ${ENGINE} (need ${MIN_DISK_GB}GB+)${NC}"
    exit 1
fi

# Warn on Intel Macs for heavy models
if [[ "$ENGINE" == "dia2" ]] && [[ "$(uname -m)" != "arm64" ]]; then
    echo -e "${YELLOW}⚠️  Dia2 on Intel Macs will run CPU-only and may be very slow.${NC}"
fi

# Check Homebrew
if ! command -v brew &> /dev/null; then
    echo -e "${YELLOW}⚠️  Homebrew not found. Installing...${NC}"
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi
echo -e "${GREEN}✅ Homebrew available${NC}"

# Install system dependencies
echo ""
echo -e "${BLUE}📦 Installing system dependencies...${NC}"
brew install ffmpeg --quiet 2>/dev/null || true
brew install espeak-ng --quiet 2>/dev/null || true
brew install uv --quiet 2>/dev/null || true
echo -e "${GREEN}✅ ffmpeg installed${NC}"

# Create installation directory
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# Create virtual environment
echo ""
echo -e "${BLUE}🐍 Setting up Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi
source venv/bin/activate

# Install hear-me
echo -e "${BLUE}📥 Installing hear-me...${NC}"
pip install --upgrade pip --quiet

if [ -f "$ROOT_DIR/pyproject.toml" ]; then
    echo -e "${BLUE}📦 Installing from local source: $ROOT_DIR${NC}"
    pip install -e "$ROOT_DIR" --quiet
    # Optional: install with local extras handled per-engine below
else
    # Fallback to PyPI (once published) or error
    echo -e "${YELLOW}⚠️  Installing from PyPI (if available)...${NC}"
    pip install hear-me --quiet 2>/dev/null || { echo -e "${RED}❌ Could not install 'hear-me'. Run this script from within the repo.${NC}"; exit 1; }
fi

# Verify hear-me core deps (retry install if missing)
echo -e "${BLUE}🧪 Verifying hear-me core dependencies...${NC}"
if ! python - <<'PY'
import importlib.util
import sys

req = ["mcp", "pydantic", "pathspec"]
missing = [r for r in req if importlib.util.find_spec(r) is None]
if missing:
    print("Missing:", ",".join(missing))
    sys.exit(1)
print("hearme core deps OK")
PY
then
    echo -e "${YELLOW}⚠️  hear-me deps missing, reinstalling...${NC}"
    pip install -e "$ROOT_DIR" --quiet
    python - <<'PY'
import importlib.util
import sys
req = ["mcp", "pydantic", "pathspec"]
missing = [r for r in req if importlib.util.find_spec(r) is None]
if missing:
    print("Missing:", ",".join(missing))
    sys.exit(1)
print("hearme core deps OK")
PY
fi

# Install TTS engine
echo ""
echo -e "${BLUE}🔊 Installing $ENGINE engine...${NC}"
case $ENGINE in
    dia2)
        echo -e "${YELLOW}⚠️  Installing Dia2 runtime (uv + repo clone)...${NC}"
        DIA2_DIR="${INSTALL_DIR}/engines/dia2"
        mkdir -p "$(dirname "$DIA2_DIR")"
        if [ -d "$DIA2_DIR/.git" ]; then
            git -C "$DIA2_DIR" pull --rebase --quiet || true
        else
            git clone https://github.com/nari-labs/dia2 "$DIA2_DIR"
        fi
        echo -e "${YELLOW}⏳ Syncing Dia2 dependencies with uv...${NC}"
        (cd "$DIA2_DIR" && env -u VIRTUAL_ENV uv sync)
        echo -e "${YELLOW}🧪 Verifying Dia2 runtime dependencies (torch)...${NC}"
        if ! (cd "$DIA2_DIR" && env -u VIRTUAL_ENV uv run python - <<'PY'
import importlib, sys
req = ["torch", "transformers", "safetensors", "soundfile", "numpy"]
missing = [r for r in req if importlib.util.find_spec(r) is None]
if missing:
    print("Missing:", ",".join(missing))
    sys.exit(1)
print("dia2 deps OK")
PY
        ); then
            echo -e "${YELLOW}⚠️  Dia2 dependency check failed, retrying uv sync...${NC}"
            (cd "$DIA2_DIR" && env -u VIRTUAL_ENV uv sync)
            (cd "$DIA2_DIR" && env -u VIRTUAL_ENV uv run python - <<'PY'
import importlib, sys
req = ["torch", "transformers", "safetensors", "soundfile", "numpy"]
missing = [r for r in req if importlib.util.find_spec(r) is None]
if missing:
    print("Missing:", ",".join(missing))
    sys.exit(1)
print("dia2 deps OK")
PY
            ) || { echo -e "${RED}❌ Dia2 dependencies not installed (missing required libs).${NC}"; exit 1; }
        fi
        
        # Pre-download model weights via CLI (this will also validate runtime)
        echo -e "${YELLOW}⏳ Pre-downloading Dia2-2B model (this may take a while)...${NC}"
        DIA2_CACHE_DIR="${HF_HOME:-$HOME/.cache/huggingface}/hub/models--nari-labs--Dia2-2B"
        if [ -d "$DIA2_CACHE_DIR" ]; then
            echo -e "${GREEN}✅ Dia2 model cache found, skipping download${NC}"
        else
            echo "[S1] Hello. [S2] This is a Dia2 install check." > "$DIA2_DIR/install-check.txt"
            for attempt in 1 2; do
                if (cd "$DIA2_DIR" && env -u VIRTUAL_ENV uv run -m dia2.cli --hf nari-labs/Dia2-2B --input install-check.txt install-check.wav); then
                    DIA2_CLI_OK=1
                    break
                fi
                echo -e "${YELLOW}⚠️  Dia2 download attempt ${attempt} failed, retrying...${NC}"
            done
        fi
        
        echo -e "${GREEN}✅ Dia2 installed (multi-speaker)${NC}"
        ;;
    kokoro)
        pip install kokoro --quiet
        
        # Pre-download
        echo -e "${YELLOW}⏳ Pre-downloading Kokoro model...${NC}"
        python3 "$ROOT_DIR/scripts/download_models.py" --engine kokoro
        
        echo -e "${GREEN}✅ Kokoro installed${NC}"
        ;;
    piper)
        pip install piper-tts --quiet
        
        # Pre-download
        echo -e "${YELLOW}⏳ Pre-downloading Piper voice...${NC}"
        python3 "$ROOT_DIR/scripts/download_models.py" --engine piper
        
        echo -e "${GREEN}✅ Piper installed${NC}"
        ;;
    *)
        echo -e "${RED}❌ Unknown engine: $ENGINE${NC}"
        exit 1
        ;;
esac

# Generate MCP config
echo ""
echo -e "${BLUE}⚙️  Generating MCP configuration...${NC}"

MCP_CONFIG=$(cat <<EOF
{
  "mcpServers": {
    "hear-me": {
      "command": "${INSTALL_DIR}/venv/bin/python",
      "args": ["-m", "hearme"]
    }
  }
}
EOF
)

echo "$MCP_CONFIG" > "$INSTALL_DIR/mcp-config.json"
echo -e "${GREEN}✅ MCP config saved to: ${INSTALL_DIR}/mcp-config.json${NC}"

# Generate application config (to set default engine)
APP_CONFIG=$(cat <<EOF
{
  "hear-me": {
    "audio": {
      "engine": "${ENGINE}"
    },
    "installation": {
      "dia2_repo_dir": "${INSTALL_DIR}/engines/dia2"
    }
  }
}
EOF
)
echo "${APP_CONFIG}" > "${INSTALL_DIR}/config.json"
echo -e "${GREEN}✅ Default engine set to: ${ENGINE}${NC}"

# Test installation
echo ""
echo -e "${BLUE}🧪 Verifying installation compatibility...${NC}"
python -c "from hearme import __version__; print(f'hear-me v{__version__}')" 2>/dev/null

if python -m hearme.troubleshoot; then
    echo -e "${GREEN}✅ System checks passed${NC}"
else
    echo -e "${RED}❌ System checks failed. See errors above.${NC}"
    exit 1
fi

# Verify Dia2 importability if selected
if [ "$ENGINE" = "dia2" ]; then
    echo ""
    echo -e "${BLUE}🧪 Verifying Dia2 CLI runtime...${NC}"
    (cd "${INSTALL_DIR}/engines/dia2" && env -u VIRTUAL_ENV uv run -m dia2.cli --help >/dev/null) || true
fi

# Smoke test: render a short sample with the selected engine
echo ""
if [ "$SKIP_SMOKE_TEST" -eq 1 ]; then
    echo -e "${YELLOW}⚠️  Skipping smoke test (per flag)${NC}"
elif [ "$ENGINE" = "dia2" ] && [ "${DIA2_CLI_OK:-0}" = "1" ]; then
    echo -e "${GREEN}✅ Dia2 CLI smoke test already completed${NC}"
else
    echo -e "${BLUE}🧪 Rendering a short audio sample with ${ENGINE}...${NC}"
    HEARME_ENGINE="$ENGINE" HEARME_OUT="$INSTALL_DIR/install-test.wav" python - <<'PY'
import os
from hearme.renderer import render_audio

engine = os.environ.get("HEARME_ENGINE")
output = os.environ.get("HEARME_OUT")
script = [
    {"speaker": "narrator", "text": "Install check. Audio synthesis is working."},
]
result = render_audio(script=script, output_path=output, engine_name=engine)
if not result.success:
    raise SystemExit(result.error or "Render failed")
print("✅ Audio sample created:", result.output_path)
PY
fi

echo -e "${GREEN}✅ hear-me ready!${NC}"

# Print next steps
echo ""
echo "=================================="
echo -e "${GREEN}✅ Installation Complete!${NC}"
echo "=================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Add to your MCP client config:"
echo -e "   ${YELLOW}cat ${INSTALL_DIR}/mcp-config.json${NC}"
echo ""
echo "2. Or copy this to your Claude/agent settings:"
echo -e "${BLUE}$MCP_CONFIG${NC}"
echo ""
echo "3. Test with your agent:"
echo "   \"Create an audio overview of this README\""
echo ""
