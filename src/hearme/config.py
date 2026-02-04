"""
hear-me Configuration System

Handles loading, validation, and defaults for hear-me configuration.
Supports hear-me.json in workspace or ~/.hear-me/config.json for global settings.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class AudioConfig(BaseModel):
    """Audio engine configuration."""
    engine: str = Field(default="kokoro", description="Primary TTS engine")
    fallback_engine: str | None = Field(default="piper", description="Fallback engine")
    voices: str | Literal["auto"] = Field(default="auto", description="Voice selection")
    format: Literal["mp3", "wav"] = Field(default="mp3", description="Output format")
    max_chars_per_chunk: int = Field(
        default=2000,
        description="Chunk size for long renders (prevents timeouts)",
    )


class DefaultsConfig(BaseModel):
    """Default settings for audio generation."""
    mode: str = Field(default="agent-decided", description="Default audio mode")
    length: Literal["overview", "balanced", "thorough", "agent-decided"] = Field(
        default="balanced",
        description="Default content depth"
    )


class OutputConfig(BaseModel):
    """Output file settings."""
    dir: str = Field(default=".hear-me", description="Output directory")


class PrivacyConfig(BaseModel):
    """Privacy settings - local-first by default."""
    allow_network: bool = Field(
        default=False,
        description="Allow network access (e.g., for model downloads)"
    )


class InstallationConfig(BaseModel):
    """Installation paths."""
    models_dir: str = Field(default="~/.hear-me/models", description="Model storage path")
    venv_path: str = Field(default="~/.hear-me/venv", description="Virtual environment path")
    dia2_repo_dir: str = Field(
        default="~/.hear-me/engines/dia2",
        description="Dia2 repo path for uv-based runtime",
    )


class HearmeConfig(BaseModel):
    """Root configuration for hear-me."""
    audio: AudioConfig = Field(default_factory=AudioConfig)
    defaults: DefaultsConfig = Field(default_factory=DefaultsConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    installation: InstallationConfig = Field(default_factory=InstallationConfig)


class Config(BaseModel):
    """Top-level config wrapper."""
    model_config = ConfigDict(populate_by_name=True)
    hearme: HearmeConfig = Field(default_factory=HearmeConfig, alias="hear-me")


def find_config_file() -> Path | None:
    """
    Find configuration file in priority order:
    1. ./hear-me.json (workspace)
    2. ~/.hear-me/config.json (user global)
    3. None (use defaults)
    """
    # Check workspace first
    workspace_config = Path("hear-me.json")
    if workspace_config.exists():
        return workspace_config
    
    # Check user home
    home_config = Path.home() / ".hear-me" / "config.json"
    if home_config.exists():
        return home_config
    
    return None


def load_config() -> HearmeConfig:
    """
    Load hear-me configuration.
    
    Returns defaults if no config file found.
    """
    config_path = find_config_file()
    
    if config_path is None:
        # Return defaults
        return HearmeConfig()
    
    try:
        with open(config_path) as f:
            data = json.load(f)
        
        # Handle both {"hear-me": {...}} and flat format
        if "hear-me" in data:
            config = Config.model_validate(data)
            return config.hearme
        else:
            return HearmeConfig.model_validate(data)
    except (json.JSONDecodeError, Exception) as e:
        import sys
        print(f"Warning: Failed to load config from {config_path}: {e}", file=sys.stderr)
        print("Using default configuration.", file=sys.stderr)
        return HearmeConfig()


def save_config(config: HearmeConfig, path: Path | None = None) -> Path:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save
        path: Target path (defaults to ./hear-me.json)
    
    Returns:
        Path where config was saved
    """
    if path is None:
        path = Path("hear-me.json")
    
    wrapped = Config(hearme=config)
    
    with open(path, "w") as f:
        json.dump(wrapped.model_dump(), f, indent=2)
    
    return path
