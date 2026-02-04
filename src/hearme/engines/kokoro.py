"""
hear-me Kokoro Audio Engine

Lightweight, CPU-friendly TTS using Kokoro.
Good quality single-speaker synthesis without GPU requirements.

Note: Kokoro must be installed separately:
    pip install kokoro>=0.9.0

For Apple Silicon (M1/M2/M3), Kokoro uses Metal acceleration automatically.
"""

from __future__ import annotations

import logging
from pathlib import Path

from hearme.engines.base import (
    BaseEngine,
    EngineCapabilities,
    VoiceInfo,
    SynthesisResult,
    AudioFormat,
)

logger = logging.getLogger(__name__)


class KokoroEngine(BaseEngine):
    """Kokoro TTS engine - lightweight, CPU-friendly."""
    
    def __init__(self):
        self._kokoro = None
        self._model = None
        self._voices = None
        self._available = None
    
    @property
    def name(self) -> str:
        return "kokoro"
    
    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            name="kokoro",
            multi_speaker=False,  # Single speaker per synthesis
            max_speakers=1,
            supports_streaming=False,
            requires_gpu=False,
            model_size_mb=300,  # Approximate
            quality_rating=3,
        )
    
    def _ensure_loaded(self) -> bool:
        """Ensure Kokoro is loaded and ready."""
        if self._model is not None:
            return True
        
        try:
            import kokoro
            self._kokoro = kokoro
            
            # Load default model
            # Kokoro auto-downloads on first use
            self._model = kokoro.KModel()
            
            logger.info("Kokoro engine loaded successfully")
            return True
            
        except ImportError:
            logger.warning("Kokoro not installed. Install with: pip install kokoro")
            return False
        except Exception as e:
            logger.error(f"Failed to load Kokoro: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Kokoro is available."""
        if self._available is not None:
            return self._available
        
        try:
            import kokoro
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available
    
    def list_voices(self) -> list[VoiceInfo]:
        """List Kokoro voices."""
        # Kokoro default voices
        return [
            VoiceInfo(id="af", name="American Female", language="en", gender="female"),
            VoiceInfo(id="am", name="American Male", language="en", gender="male"),
            VoiceInfo(id="bf", name="British Female", language="en", gender="female"),
            VoiceInfo(id="bm", name="British Male", language="en", gender="male"),
        ]
    
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """
        Synthesize speech using Kokoro.
        
        Args:
            text: Text to synthesize
            voice: Voice ID (af, am, bf, bm)
            format: Output format (mp3 or wav)
        """
        if not self._ensure_loaded():
            return SynthesisResult(
                success=False,
                error="Kokoro engine not available"
            )
        
        try:
            # Default voice
            voice = voice or "af"
            
            # Generate audio
            audio, sample_rate = self._kokoro.generate(
                text=text,
                voice=voice,
            )
            
            import numpy as np
            import io
            import wave
            
            # Convert to WAV bytes
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                
                # Convert float audio to int16
                audio_int = (audio * 32767).astype(np.int16)
                wav.writeframes(audio_int.tobytes())
            
            audio_data = buffer.getvalue()
            duration = len(audio) / sample_rate
            
            return SynthesisResult(
                success=True,
                audio_data=audio_data,
                duration_seconds=duration,
                format="wav",  # Kokoro outputs WAV
                sample_rate=sample_rate,
            )
            
        except Exception as e:
            logger.error(f"Kokoro synthesis failed: {e}")
            return SynthesisResult(
                success=False,
                error=str(e)
            )
