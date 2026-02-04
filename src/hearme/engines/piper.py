"""
HEARME Piper Audio Engine

Lightweight, fast TTS using Piper (ONNX-based).
Ultra-low resource usage for fallback on constrained systems.

Note: Piper must be installed separately:
    pip install piper-tts

Piper is very lightweight and runs efficiently on CPU.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path

from hearme.engines.base import (
    BaseEngine,
    EngineCapabilities,
    VoiceInfo,
    SynthesisResult,
    AudioFormat,
)

logger = logging.getLogger(__name__)


class PiperEngine(BaseEngine):
    """
    Piper TTS engine - lightweight, fast ONNX synthesis.
    
    Best for resource-constrained systems or as final fallback.
    """
    
    def __init__(self):
        self._piper = None
        self._voice = None
        self._available = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        return "piper"
    
    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            name="piper",
            multi_speaker=False,
            max_speakers=1,
            supports_streaming=False,
            requires_gpu=False,
            model_size_mb=50,  # Very small
            quality_rating=2,
        )
    
    def is_available(self) -> bool:
        """Check if Piper is installed."""
        if self._available is not None:
            return self._available
        
        try:
            import piper
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available
    
    def load(self) -> None:
        """Load Piper voice model."""
        if self._loaded:
            return
        
        if not self.is_available():
            raise RuntimeError("Piper not installed. Run: pip install piper-tts")
        
        try:
            from piper import PiperVoice
            
            # Use default English voice
            # Piper downloads voice models on first use
            logger.info("Loading Piper voice model...")
            self._voice = PiperVoice.load("en_US-amy-medium")
            self._loaded = True
            logger.info("Piper loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Piper: {e}")
            raise
    
    def unload(self) -> None:
        """Unload Piper to free memory."""
        if self._voice is not None:
            del self._voice
            self._voice = None
            logger.info("Piper unloaded - memory freed")
        
        self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if voice is loaded."""
        return self._loaded
    
    def list_voices(self) -> list[VoiceInfo]:
        """List Piper voices."""
        return [
            VoiceInfo(id="en_US-amy-medium", name="Amy (US English)", language="en", gender="female"),
            VoiceInfo(id="en_US-ryan-medium", name="Ryan (US English)", language="en", gender="male"),
            VoiceInfo(id="en_GB-alba-medium", name="Alba (UK English)", language="en", gender="female"),
        ]
    
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "wav",
    ) -> SynthesisResult:
        """Synthesize speech using Piper."""
        if not self._loaded:
            self.load()
        
        try:
            import wave
            import io
            
            # Synthesize to bytes
            buffer = io.BytesIO()
            
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(22050)  # Piper default
                
                for audio_bytes in self._voice.synthesize_stream_raw(text):
                    wav.writeframes(audio_bytes)
            
            audio_data = buffer.getvalue()
            
            # Estimate duration (Piper doesn't provide it directly)
            # Rough estimate: 150 words per minute
            word_count = len(text.split())
            duration = max(0.5, word_count / 150 * 60)
            
            return SynthesisResult(
                success=True,
                audio_data=audio_data,
                duration_seconds=duration,
                format="wav",
                sample_rate=22050,
            )
            
        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            return SynthesisResult(
                success=False,
                error=str(e)
            )
