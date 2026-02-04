"""
Tests for hear-me audio renderer.
"""

import pytest
from pathlib import Path
from hear-me.renderer import (
    parse_script,
    validate_script,
    render_audio,
    ScriptSegment,
    RenderResult,
)


class TestScriptParsing:
    """Tests for script parsing."""
    
    def test_parse_simple_script(self):
        """Parse a simple script."""
        script = [
            {"speaker": "narrator", "text": "Hello world."},
        ]
        segments = parse_script(script)
        assert len(segments) == 1
        assert segments[0].speaker == "narrator"
        assert segments[0].text == "Hello world."
    
    def test_parse_multi_speaker(self):
        """Parse multi-speaker script."""
        script = [
            {"speaker": "host", "text": "Welcome!"},
            {"speaker": "guest", "text": "Thanks for having me."},
        ]
        segments = parse_script(script)
        assert len(segments) == 2
        assert segments[0].speaker == "host"
        assert segments[1].speaker == "guest"
    
    def test_skip_empty_text(self):
        """Skip segments with empty text."""
        script = [
            {"speaker": "narrator", "text": "Hello"},
            {"speaker": "narrator", "text": ""},
            {"speaker": "narrator", "text": "World"},
        ]
        segments = parse_script(script)
        assert len(segments) == 2
    
    def test_default_speaker(self):
        """Use narrator as default speaker."""
        script = [{"text": "Hello world."}]
        segments = parse_script(script)
        assert segments[0].speaker == "narrator"


class TestScriptValidation:
    """Tests for script validation."""
    
    def test_empty_script_invalid(self):
        """Empty script should be invalid."""
        valid, error = validate_script([])
        assert not valid
        assert "empty" in error.lower()
    
    def test_valid_script(self):
        """Normal script should be valid."""
        segments = [ScriptSegment(speaker="narrator", text="Hello")]
        valid, error = validate_script(segments)
        assert valid
        assert error is None


class TestRendering:
    """Tests for audio rendering."""
    
    def test_render_with_mock_engine(self, tmp_path):
        """Render audio using mock engine."""
        script = [
            {"speaker": "narrator", "text": "This is a test."},
        ]
        output = tmp_path / "test.wav"
        
        result = render_audio(
            script=script,
            output_path=str(output),
            engine_name="mock",
        )
        
        assert result.success
        assert result.engine_used == "mock"
        assert output.exists()
    
    def test_render_multi_speaker(self, tmp_path):
        """Render multi-speaker audio."""
        script = [
            {"speaker": "host", "text": "Welcome to the show."},
            {"speaker": "guest", "text": "Great to be here."},
            {"speaker": "host", "text": "Tell us about your project."},
        ]
        output = tmp_path / "multi.wav"
        
        result = render_audio(
            script=script,
            output_path=str(output),
            engine_name="mock",
        )
        
        assert result.success
        assert result.segment_count == 3
    
    def test_render_creates_directory(self, tmp_path):
        """Render should create output directory if needed."""
        script = [{"speaker": "narrator", "text": "Hello"}]
        output = tmp_path / "subdir" / "test.wav"
        
        result = render_audio(
            script=script,
            output_path=str(output),
            engine_name="mock",
        )
        
        assert result.success
        assert output.exists()
