"""
Tests for HEARME audio engines.
"""

import pytest
from hearme.engines.base import (
    EngineCapabilities,
    SynthesisResult,
    VoiceInfo,
)
from hearme.engines.mock import MockEngine
from hearme.engines.registry import EngineRegistry, get_engine


class TestEngineCapabilities:
    """Tests for EngineCapabilities."""
    
    def test_capabilities_serialization(self):
        """Capabilities should serialize to dict."""
        caps = EngineCapabilities(
            name="test",
            multi_speaker=True,
            max_speakers=4,
        )
        data = caps.model_dump()
        assert data["name"] == "test"
        assert data["multi_speaker"] is True
        assert data["max_speakers"] == 4


class TestMockEngine:
    """Tests for MockEngine."""
    
    def test_mock_is_available(self):
        """Mock engine should always be available."""
        engine = MockEngine()
        assert engine.is_available()
    
    def test_mock_name(self):
        """Mock engine should report correct name."""
        engine = MockEngine()
        assert engine.name == "mock"
    
    def test_mock_capabilities(self):
        """Mock engine should report capabilities."""
        engine = MockEngine()
        caps = engine.capabilities
        assert caps.multi_speaker is True
        assert caps.requires_gpu is False
    
    def test_mock_list_voices(self):
        """Mock engine should list voices."""
        engine = MockEngine()
        voices = engine.list_voices()
        assert len(voices) > 0
        assert all(isinstance(v, VoiceInfo) for v in voices)
    
    def test_mock_synthesize(self):
        """Mock engine should generate placeholder audio."""
        engine = MockEngine()
        result = engine.synthesize("Hello, this is a test.")
        
        assert result.success
        assert result.audio_data is not None
        assert len(result.audio_data) > 0
        assert result.duration_seconds > 0
    
    def test_mock_synthesize_multi(self):
        """Mock engine should handle multi-speaker synthesis."""
        engine = MockEngine()
        segments = [
            {"speaker": "narrator", "text": "Welcome to the project."},
            {"speaker": "expert", "text": "Let me explain how it works."},
        ]
        
        result = engine.synthesize_multi(segments)
        
        assert result.success
        assert len(result.segments) == 2


class TestEngineRegistry:
    """Tests for EngineRegistry."""
    
    def test_get_mock_engine(self):
        """Should be able to get mock engine."""
        engine = get_engine("mock")
        assert engine is not None
        assert engine.name == "mock"
    
    def test_get_best_available(self):
        """Should return an engine when getting best available."""
        engine = get_engine()
        assert engine is not None
        assert engine.is_available()
    
    def test_nonexistent_engine_returns_none(self):
        """Requesting unknown engine should return None."""
        engine = get_engine("nonexistent_engine_xyz")
        assert engine is None


class TestEngineLifecycle:
    """Tests for bulletproof resource management."""
    
    def test_engine_starts_unloaded(self):
        """Engine should not be loaded initially."""
        engine = MockEngine()
        assert not engine.is_loaded()
    
    def test_load_sets_loaded_flag(self):
        """Load should set the loaded flag."""
        engine = MockEngine()
        engine.load()
        assert engine.is_loaded()
    
    def test_unload_clears_loaded_flag(self):
        """Unload should clear the loaded flag."""
        engine = MockEngine()
        engine.load()
        engine.unload()
        assert not engine.is_loaded()
    
    def test_context_manager_auto_cleanup(self):
        """Context manager should auto-unload on exit."""
        engine = MockEngine()
        
        with engine:
            assert engine.is_loaded()
        
        assert not engine.is_loaded()
    
    def test_context_manager_cleanup_on_error(self):
        """Context manager should cleanup even on error."""
        engine = MockEngine()
        
        try:
            with engine:
                assert engine.is_loaded()
                raise ValueError("Simulated error")
        except ValueError:
            pass
        
        assert not engine.is_loaded()
