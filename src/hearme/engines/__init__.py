"""
HEARME Audio Engines

Engine abstraction layer for text-to-speech synthesis.
"""

from hearme.engines.base import AudioEngine, EngineCapabilities, SynthesisResult
from hearme.engines.registry import get_engine, list_engines, EngineRegistry

__all__ = [
    "AudioEngine",
    "EngineCapabilities", 
    "SynthesisResult",
    "get_engine",
    "list_engines",
    "EngineRegistry",
]
