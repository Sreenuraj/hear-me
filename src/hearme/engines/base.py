"""
hear-me Audio Engine Base

Defines the AudioEngine protocol and related types.
All TTS engines must implement this interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable


AudioFormat = Literal["mp3", "wav"]


@dataclass
class EngineCapabilities:
    """Capabilities of an audio engine."""
    name: str
    multi_speaker: bool = False
    max_speakers: int = 1
    supports_streaming: bool = False
    requires_gpu: bool = False
    model_size_mb: int = 0
    quality_rating: int = 3  # 1-5 stars
    
    def model_dump(self) -> dict:
        return {
            "name": self.name,
            "multi_speaker": self.multi_speaker,
            "max_speakers": self.max_speakers,
            "supports_streaming": self.supports_streaming,
            "requires_gpu": self.requires_gpu,
            "model_size_mb": self.model_size_mb,
            "quality_rating": self.quality_rating,
        }


@dataclass
class VoiceInfo:
    """Information about an available voice."""
    id: str
    name: str
    language: str = "en"
    gender: str | None = None
    style: str | None = None


@dataclass
class SynthesisSegment:
    """A segment of synthesized audio."""
    speaker: str
    text: str
    audio_data: bytes
    duration_seconds: float
    sample_rate: int = 24000


@dataclass 
class SynthesisResult:
    """Result of audio synthesis."""
    success: bool
    audio_data: bytes | None = None
    duration_seconds: float = 0.0
    format: AudioFormat = "mp3"
    sample_rate: int = 24000
    segments: list[SynthesisSegment] = field(default_factory=list)
    error: str | None = None
    
    def model_dump(self) -> dict:
        return {
            "success": self.success,
            "duration_seconds": round(self.duration_seconds, 2),
            "format": self.format,
            "sample_rate": self.sample_rate,
            "segment_count": len(self.segments),
            "error": self.error,
        }


@runtime_checkable
class AudioEngine(Protocol):
    """Protocol for audio synthesis engines."""
    
    @property
    def name(self) -> str:
        """Engine name."""
        ...
    
    @property
    def capabilities(self) -> EngineCapabilities:
        """Engine capabilities."""
        ...
    
    def is_available(self) -> bool:
        """Check if engine is available (models loaded, deps installed)."""
        ...
    
    def list_voices(self) -> list[VoiceInfo]:
        """List available voices."""
        ...
    
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """
        Synthesize speech from text.
        
        Args:
            text: Text to synthesize
            voice: Voice ID to use (None for default)
            format: Output audio format
        
        Returns:
            SynthesisResult with audio data
        """
        ...
    
    def synthesize_multi(
        self,
        segments: list[dict],
        voice_map: dict[str, str] | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """
        Synthesize multi-speaker audio.
        
        Args:
            segments: List of {speaker, text} dicts
            voice_map: Mapping of speaker names to voice IDs
            format: Output audio format
        
        Returns:
            SynthesisResult with concatenated audio
        """
        ...


class BaseEngine(ABC):
    """Abstract base class for audio engines."""
    
    _loaded: bool = False
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name."""
        pass
    
    @property
    @abstractmethod
    def capabilities(self) -> EngineCapabilities:
        """Engine capabilities."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if engine is available."""
        pass
    
    @abstractmethod
    def list_voices(self) -> list[VoiceInfo]:
        """List available voices."""
        pass
    
    # =========================================================================
    # Lifecycle Methods - BULLETPROOF RESOURCE MANAGEMENT
    # =========================================================================
    
    def is_loaded(self) -> bool:
        """Check if engine models are currently loaded in memory."""
        return self._loaded
    
    def load(self) -> None:
        """
        Load TTS models into memory.
        
        Called automatically before synthesis.
        Override in subclasses to load actual models.
        """
        self._loaded = True
    
    def unload(self) -> None:
        """
        Unload TTS models from memory.
        
        Called automatically after synthesis completes.
        Override in subclasses to properly cleanup resources.
        """
        self._loaded = False
    
    def __enter__(self):
        """Context manager support for auto-cleanup."""
        self.load()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Ensure cleanup on context exit, even on error."""
        self.unload()
        return False
    
    # =========================================================================
    # Synthesis Methods
    # =========================================================================
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """Synthesize single-speaker audio."""
        pass
    
    def synthesize_multi(
        self,
        segments: list[dict],
        voice_map: dict[str, str] | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """
        Default multi-speaker implementation.
        
        Engines without native multi-speaker support use this fallback
        which synthesizes each segment separately and concatenates.
        """
        if not segments:
            return SynthesisResult(success=False, error="No segments provided")
        
        all_audio = []
        total_duration = 0.0
        result_segments = []
        
        voice_map = voice_map or {}
        default_voice = None
        
        for seg in segments:
            speaker = seg.get("speaker", "narrator")
            text = seg.get("text", "")
            
            if not text.strip():
                continue
            
            voice = voice_map.get(speaker, default_voice)
            result = self.synthesize(text, voice=voice, format=format)
            
            if not result.success:
                return SynthesisResult(
                    success=False,
                    error=f"Failed to synthesize segment for {speaker}: {result.error}"
                )
            
            all_audio.append(result.audio_data)
            total_duration += result.duration_seconds
            
            result_segments.append(SynthesisSegment(
                speaker=speaker,
                text=text,
                audio_data=result.audio_data,
                duration_seconds=result.duration_seconds,
                sample_rate=result.sample_rate,
            ))
        
        # Concatenate audio (simple for now - proper concat in renderer)
        combined = b"".join(all_audio) if all_audio else b""
        
        return SynthesisResult(
            success=True,
            audio_data=combined,
            duration_seconds=total_duration,
            format=format,
            segments=result_segments,
        )
