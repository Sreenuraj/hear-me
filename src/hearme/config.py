"""
HEARME Configuration System

Handles loading, validation, and defaults for HEARME configuration.
Supports hearme.json in workspace or ~/.hearme/config.json for global settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class AudioConfig(BaseModel):
    """Audio engine configuration."""
    engine: str = Field(default="kokoro", description="Primary TTS engine")
    fallback_engine: str | None = Field(default="piper", description="Fallback engine")
    voices: str | Literal["auto"] = Field(default="auto", description="Voice selection")
    format: Literal["mp3", "wav"] = Field(default="mp3", description="Output format")


class DefaultsConfig(BaseModel):
    """Default settings for audio generation."""
    mode: str = Field(default="agent-decided", description="Default audio mode")
    length: Literal["overview", "balanced", "thorough", "agent-decided"] = Field(
        default="balanced",
        description="Default content depth"
    )


class OutputConfig(BaseModel):
    """Output file settings."""
    dir: str = Field(default=".hearme", description="Output directory")


class PrivacyConfig(BaseModel):
    """Privacy settings - local-first by default."""
    allow_network: bool = Field(
        default=False,
        description="Allow network access (e.g., for model downloads)"
    )


class InstallationConfig(BaseModel):
    """Installation paths."""
    models_dir: str = Field(default="~/.hearme/models", description="Model storage path")
    venv_path: str = Field(default="~/.hearme/venv", description="Virtual environment path")


class HearmeConfig(BaseModel):
    """Root configuration for HEARME."""
    audio: AudioConfig = Field(default_factory=AudioConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    installation: InstallationConfig = Field(default_factory=InstallationConfig)


class Config(BaseModel):
    """Top-level config wrapper."""
    hearme: HearmeConfig = Field(default_factory=HearmeConfig)


def find_config_file() -> Path | None:
    """
    Find configuration file in priority order:
    1. ./hearme.json (workspace)
    2. ~/.hearme/config.json (user global)
    3. None (use defaults)
    """
    # Check workspace first
    workspace_config = Path("hearme.json")
    if workspace_config.exists():
        return workspace_config
    
    # Check user home
    home_config = Path.home() / ".hearme" / "config.json"
    if home_config.exists():
        return home_config
    
    return None


def load_config() -> HearmeConfig:
    """
    Load HEARME configuration.
    
    Returns defaults if no config file found.
    """
    config_path = find_config_file()
    
    if config_path is None:
        # Return defaults
        return HearmeConfig()
    
    try:
        with open(config_path) as f:
            data = json.load(f)
        
        # Handle both {"hearme": {...}} and flat format
        if "hearme" in data:
            config = Config.model_validate(data)
            return config.hearme
        else:
            return HearmeConfig.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        print(f"Warning: Failed to load config from {config_path}: {e}")
        print("Using default configuration.")
        return HearmeConfig()


def save_config(config: HearmeConfig, path: Path | None = None) -> Path:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save
        path: Target path (defaults to ./hearme.json)
    
    Returns:
        Path where config was saved
    """
    if path is None:
        path = Path("hearme.json")
    
    wrapped = Config(hearme=config)
    
    with open(path, "w") as f:
        json.dump(wrapped.model_dump(), f, indent=2)
    
    return path
