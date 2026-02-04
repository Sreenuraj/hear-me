"""
hear-me Output Manager

Manages output file persistence and metadata generation.
Creates the .hear-me/ directory structure with audio, scripts, and metadata.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class OutputManifest:
    """Manifest of generated outputs."""
    version: str = "1.0"
    created_at: str = ""
    audio_file: str | None = None
    script_file: str | None = None
    duration_seconds: float = 0.0
    engine_used: str | None = None
    segment_count: int = 0
    documents_used: list[str] = field(default_factory=list)
    
    def model_dump(self) -> dict:
        return {
            "version": self.version,
            "created_at": self.created_at,
            "audio_file": self.audio_file,
            "script_file": self.script_file,
            "duration_seconds": round(self.duration_seconds, 2),
            "engine_used": self.engine_used,
            "segment_count": self.segment_count,
            "documents_used": self.documents_used,
        }


def ensure_hearme_directory(root: str = ".") -> Path:
    """
    Ensure .hear-me directory exists.
    
    Args:
        root: Project root directory
    
    Returns:
        Path to .hear-me directory
    """
    hearme_dir = Path(root) / ".hear-me"
    hearme_dir.mkdir(parents=True, exist_ok=True)
    return hearme_dir


def save_script(
    script: list[dict],
    root: str = ".",
    filename: str = "script"
) -> tuple[str | None, str | None]:
    """
    Save script to both JSON and plain text formats.
    
    Args:
        script: List of {speaker, text} segments
        root: Project root directory
        filename: Base filename (without extension)
    
    Returns:
        Tuple of (json_path, txt_path)
    """
    hearme_dir = ensure_hearme_directory(root)
    
    json_path = hearme_dir / f"{filename}.json"
    txt_path = hearme_dir / f"{filename}.txt"
    
    try:
        # Save JSON
        with open(json_path, "w") as f:
            json.dump(script, f, indent=2)
        
        # Save plain text (for easy reading)
        with open(txt_path, "w") as f:
            for seg in script:
                speaker = seg.get("speaker", "narrator")
                text = seg.get("text", "")
                f.write(f"[{speaker.upper()}]\n{text}\n\n")
        
        return str(json_path), str(txt_path)
        
    except Exception as e:
        logger.error(f"Failed to save script: {e}")
        return None, None


def save_manifest(
    manifest: OutputManifest,
    root: str = "."
) -> str | None:
    """
    Save output manifest.
    
    Args:
        manifest: OutputManifest to save
        root: Project root directory
    
    Returns:
        Path to manifest file or None on error
    """
    hearme_dir = ensure_hearme_directory(root)
    manifest_path = hearme_dir / "manifest.json"
    
    try:
        with open(manifest_path, "w") as f:
            json.dump(manifest.model_dump(), f, indent=2)
        
        return str(manifest_path)
        
    except Exception as e:
        logger.error(f"Failed to save manifest: {e}")
        return None


def persist_outputs(
    audio_path: str | None,
    script: list[dict],
    duration_seconds: float = 0.0,
    engine_used: str | None = None,
    documents_used: list[str] | None = None,
    root: str = "."
) -> dict:
    """
    Persist all outputs and create manifest.
    
    Args:
        audio_path: Path to rendered audio file
        script: The script that was rendered
        duration_seconds: Audio duration
        engine_used: Name of TTS engine used
        documents_used: List of source documents
        root: Project root directory
    
    Returns:
        Dict with paths to all saved files
    """
    result = {
        "success": True,
        "audio_file": audio_path,
        "script_json": None,
        "script_txt": None,
        "manifest": None,
    }
    
    # Save script
    json_path, txt_path = save_script(script, root)
    result["script_json"] = json_path
    result["script_txt"] = txt_path
    
    # Create and save manifest
    manifest = OutputManifest(
        created_at=datetime.now().isoformat(),
        audio_file=audio_path,
        script_file=json_path,
        duration_seconds=duration_seconds,
        engine_used=engine_used,
        segment_count=len(script),
        documents_used=documents_used or [],
    )
    
    manifest_path = save_manifest(manifest, root)
    result["manifest"] = manifest_path
    
    return result


def get_output_path(root: str = ".", filename: str = "hear-me.audio") -> str:
    """
    Get the default output path for audio.
    
    Args:
        root: Project root directory
        filename: Audio filename (without extension)
    
    Returns:
        Full path for audio output
    """
    hearme_dir = ensure_hearme_directory(root)
    return str(hearme_dir / f"{filename}.wav")
