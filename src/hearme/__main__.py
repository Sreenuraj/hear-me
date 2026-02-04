"""
hear-me MCP - Command-line entry point.

Usage:
    python -m hearme
    python -m hearme cleanup
"""

import sys

from hearme import main
from hearme.cleanup import cli_cleanup

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        raise SystemExit(cli_cleanup())
    main()
