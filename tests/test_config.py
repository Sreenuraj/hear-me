"""
Tests for HEARME configuration system.
"""

import json
import pytest
from pathlib import Path

from hearme.config import (
    HearmeConfig,
    AudioConfig,
    PrivacyConfig,
    load_config,
    save_config,
)


class TestDefaultConfig:
    """Tests for default configuration values."""
    
    def test_default_audio_engine(self):
        """Default engine should be kokoro (lightweight fallback)."""
        config = HearmeConfig()
        assert config.audio.engine == "kokoro"
    
    def test_default_privacy_is_local(self):
        """Privacy should be local-first by default."""
        config = HearmeConfig()
        assert config.privacy.allow_network is False
    
    def test_default_format(self):
        """Default audio format should be mp3."""
        config = HearmeConfig()
        assert config.audio.format == "mp3"
    
    def test_default_length(self):
        """Default length should be balanced."""
        config = HearmeConfig()
        assert config.defaults.length == "balanced"


class TestConfigSerialization:
    """Tests for config serialization."""
    
    def test_config_to_dict(self):
        """Config should serialize to dict."""
        config = HearmeConfig()
        data = config.model_dump()
        
        assert isinstance(data, dict)
        assert "audio" in data
        assert "privacy" in data
        assert "output" in data
    
    def test_config_roundtrip(self, tmp_path):
        """Config should roundtrip through save/load."""
        config = HearmeConfig(
            audio=AudioConfig(engine="vibevoice"),
            privacy=PrivacyConfig(allow_network=True)
        )
        
        # Save to temp file
        config_path = tmp_path / "hearme.json"
        save_config(config, config_path)
        
        # Verify file exists and has content
        assert config_path.exists()
        with open(config_path) as f:
            data = json.load(f)
        
        assert data["hearme"]["audio"]["engine"] == "vibevoice"
        assert data["hearme"]["privacy"]["allow_network"] is True


class TestConfigValidation:
    """Tests for config validation."""
    
    def test_invalid_format_rejected(self):
        """Invalid audio format should be rejected."""
        with pytest.raises(Exception):
            AudioConfig(format="invalid")
    
    def test_invalid_length_rejected(self):
        """Invalid length value should be rejected."""
        from hearme.config import DefaultsConfig
        with pytest.raises(Exception):
            DefaultsConfig(length="invalid")
