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
        --help)
            echo "Usage: ./install-macos.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --engine ENGINE    TTS engine: dia2, kokoro, piper (default: kokoro)"
            echo "  --profile PROFILE  Installation profile: minimal, recommended, full"
            echo "  --dir PATH         Installation directory (default: ~/.hear-me)"
            echo ""
            echo "Engines:"
            echo "  dia2     NotebookLM-like multi-speaker (requires ~2GB RAM)"
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
# Install hear-me
echo -e "${BLUE}📥 Installing hear-me...${NC}"
pip install --upgrade pip --quiet

if [ -f "$ROOT_DIR/pyproject.toml" ]; then
    echo -e "${BLUE}📦 Installing from local source: $ROOT_DIR${NC}"
    pip install -e "$ROOT_DIR" --quiet
    # Also install dev dependencies for local dev
    pip install -e "$ROOT_DIR[dev]" --quiet
else
    # Fallback to PyPI (once published) or error
    echo -e "${YELLOW}⚠️  Installing from PyPI (if available)...${NC}"
    pip install hear-me --quiet 2>/dev/null || { echo -e "${RED}❌ Could not install 'hear-me'. Run this script from within the repo.${NC}"; exit 1; }
fi

# Install TTS engine
echo ""
echo -e "${BLUE}🔊 Installing $ENGINE engine...${NC}"
case $ENGINE in
    dia2)
        # Dia2 (vendored)
        echo -e "${YELLOW}⚠️  Installing Dia2 dependencies (large download)...${NC}"
        # Install with [dia2] extra, forcing upgrade to match requirements
        pip install -e "$ROOT_DIR[dia2]" --upgrade --quiet
        
        # Pre-download model weights
        echo -e "${YELLOW}⏳ Pre-downloading Dia2-2B model (this may take a while)...${NC}"
        python3 "$ROOT_DIR/scripts/download_models.py" --engine dia2
        
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
        echo -e "${YELLOW}⚠️  Unknown engine: $ENGINE, using mock${NC}"
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
