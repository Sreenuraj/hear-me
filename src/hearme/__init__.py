"""
hear-me MCP - Replace your README.md with a hear-me.mp3

A Model Context Protocol server that transforms project documentation
into natural, conversational audio files.
"""

__version__ = "0.1.0"
__author__ = "hear-me Contributors"


def main():
    """Entry point for the hear-me command."""
    from hearme.server import run_server
    run_server()
