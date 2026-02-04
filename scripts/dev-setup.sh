#!/bin/bash
# hear-me Development Setup
# Run this script to set up your development environment

set -e

echo "🎙️ hear-me Development Setup"
echo "============================"
echo ""

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION+ required (found $PYTHON_VERSION)"
    exit 1
fi
echo "✅ Python $PYTHON_VERSION"

# Create virtual environment if not exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source .venv/bin/activate

# Install package in editable mode with dev dependencies
echo "📥 Installing hear-me in development mode..."
pip install -e ".[dev]" --quiet

# Verify installation
echo ""
echo "🧪 Verifying installation..."
python -c "from hearme import __version__; print(f'hear-me v{__version__} installed')"

echo ""
echo "✅ Development setup complete!"
echo ""
echo "Next steps:"
echo "  source .venv/bin/activate    # Activate environment"
echo "  python -m hearme             # Run the MCP server"
echo "  pytest                       # Run tests"
echo ""
