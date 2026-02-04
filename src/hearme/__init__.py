"""
HEARME MCP - Replace your README.md with a hearme.mp3

A Model Context Protocol server that transforms project documentation
into natural, conversational audio files.
"""

__version__ = "0.1.0"
__author__ = "HEARME Contributors"


def main():
    """Entry point for the hearme command."""
    from hearme.server import run_server
    run_server()
