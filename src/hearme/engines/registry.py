"""
hear-me Engine Registry

Manages available audio engines and provides fallback selection.
"""

from __future__ import annotations

import logging
from typing import Type

from hearme.engines.base import AudioEngine, BaseEngine, EngineCapabilities

logger = logging.getLogger(__name__)


class EngineRegistry:
    """Registry of available audio engines."""
    
    _engines: dict[str, Type[BaseEngine]] = {}
    _instances: dict[str, BaseEngine] = {}
    _fallback_order: list[str] = []
    
    @classmethod
    def register(cls, engine_class: Type[BaseEngine], priority: int = 50) -> None:
        """
        Register an engine class.
        
        Args:
            engine_class: The engine class to register
            priority: Lower number = higher priority for fallback
        """
        name = engine_class.__name__.lower().replace("engine", "")
        cls._engines[name] = engine_class
        
        # Update fallback order
        if name not in cls._fallback_order:
            cls._fallback_order.append(name)
            cls._fallback_order.sort(key=lambda n: priority)
    
    @classmethod
    def get(cls, name: str) -> BaseEngine | None:
        """
        Get an engine instance by name.
        
        Args:
            name: Engine name (e.g., 'kokoro', 'mock')
        
        Returns:
            Engine instance or None if not found
        """
        name = name.lower()
        
        # Return cached instance
        if name in cls._instances:
            return cls._instances[name]
        
        # Create new instance
        if name in cls._engines:
            try:
                instance = cls._engines[name]()
                cls._instances[name] = instance
                return instance
            except Exception as e:
                logger.warning(f"Failed to create engine {name}: {e}")
                return None
        
        return None
    
    @classmethod
    def get_available(cls) -> list[str]:
        """Get list of available engine names."""
        available = []
        
        for name in cls._engines:
            engine = cls.get(name)
            if engine and engine.is_available():
                available.append(name)
        
        return available
    
    @classmethod
    def get_best_available(cls) -> BaseEngine | None:
        """
        Get the best available engine based on fallback order.
        
        Returns the first engine that is available, in priority order.
        """
        for name in cls._fallback_order:
            engine = cls.get(name)
            if engine and engine.is_available():
                logger.info(f"Selected engine: {name}")
                return engine
        
        return None
    
    @classmethod
    def list_all(cls) -> list[EngineCapabilities]:
        """List capabilities of all registered engines."""
        result = []
        
        for name in cls._engines:
            engine = cls.get(name)
            if engine:
                result.append(engine.capabilities)
        
        return result
    
    @classmethod
    def clear(cls) -> None:
        """Clear registry (for testing)."""
        cls._engines.clear()
        cls._instances.clear()
        cls._fallback_order.clear()


def get_engine(name: str | None = None) -> BaseEngine | None:
    """
    Get an audio engine by name or get the best available.
    
    Args:
        name: Engine name, or None for best available
    
    Returns:
        Engine instance or None
    """
    if name:
        return EngineRegistry.get(name)
    return EngineRegistry.get_best_available()


def list_engines() -> list[EngineCapabilities]:
    """List all registered engines and their capabilities."""
    return EngineRegistry.list_all()


def register_default_engines() -> None:
    """
    Register the default set of engines.
    
    Priority order (lower = higher priority):
    - Dia2 (10): Best quality, multi-speaker
    - Kokoro (30): Good quality, single speaker
    - Piper (50): Fast, lightweight
    - Mock (100): Development only
    """
    # Import engines here to avoid circular imports
    from hearme.engines.mock import MockEngine
    
    # Register in priority order (lower = higher priority)
    EngineRegistry.register(MockEngine, priority=100)  # Lowest priority
    
    # Try to import optional engines
    try:
        from hearme.engines.dia2 import Dia2Engine
        EngineRegistry.register(Dia2Engine, priority=10)  # Highest priority
    except ImportError:
        logger.debug("Dia2 engine not available")
    
    try:
        from hearme.engines.kokoro import KokoroEngine
        EngineRegistry.register(KokoroEngine, priority=30)
    except ImportError:
        logger.debug("Kokoro engine not available")
    
    try:
        from hearme.engines.piper import PiperEngine
        EngineRegistry.register(PiperEngine, priority=50)
    except ImportError:
        logger.debug("Piper engine not available")


# Auto-register on import
register_default_engines()

