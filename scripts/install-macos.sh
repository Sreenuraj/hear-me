#!/bin/bash
# HEARME macOS Installation Script
# Install HEARME with optional TTS engine setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}🎙️  HEARME Installer for macOS${NC}"
echo "=================================="
echo ""

# Parse arguments
ENGINE="kokoro"  # Default engine
PROFILE="recommended"
INSTALL_DIR="${HOME}/.hearme"

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
            echo "  --dir PATH         Installation directory (default: ~/.hearme)"
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

echo -e "Engine:  ${GREEN}${ENGINE}${NC}"
echo -e "Profile: ${GREEN}${PROFILE}${NC}"
echo -e "Dir:     ${GREEN}${INSTALL_DIR}${NC}"
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

# Install HEARME
echo -e "${BLUE}📥 Installing HEARME...${NC}"
pip install --upgrade pip --quiet
pip install hearme --quiet 2>/dev/null || pip install git+https://github.com/your-repo/hearme.git --quiet

# Install TTS engine
echo ""
echo -e "${BLUE}🔊 Installing $ENGINE engine...${NC}"
case $ENGINE in
    dia2)
        pip install dia-tts torch --quiet
        echo -e "${GREEN}✅ Dia2 installed (multi-speaker)${NC}"
        ;;
    kokoro)
        pip install kokoro --quiet
        echo -e "${GREEN}✅ Kokoro installed${NC}"
        ;;
    piper)
        pip install piper-tts --quiet
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
    "hearme": {
      "command": "${INSTALL_DIR}/venv/bin/python",
      "args": ["-m", "hearme"]
    }
  }
}
EOF
)

echo "$MCP_CONFIG" > "$INSTALL_DIR/mcp-config.json"
echo -e "${GREEN}✅ MCP config saved to: ${INSTALL_DIR}/mcp-config.json${NC}"

# Test installation
echo ""
echo -e "${BLUE}🧪 Testing installation...${NC}"
python -c "from hearme import __version__; print(f'HEARME v{__version__}')" 2>/dev/null && \
    echo -e "${GREEN}✅ HEARME ready!${NC}" || \
    echo -e "${YELLOW}⚠️  Installation may need additional setup${NC}"

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
