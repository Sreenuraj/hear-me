"""
HEARME Dia2 Audio Engine

High-quality multi-speaker conversational TTS using Nari Labs Dia2.
Produces NotebookLM-like two-host conversations.

Note: Dia2 must be installed separately:
    pip install dia-tts

For Apple Silicon (M1/M2/M3), Dia2 uses MPS acceleration automatically.
"""

from __future__ import annotations

import logging
from typing import Any

from hearme.engines.base import (
    BaseEngine,
    EngineCapabilities,
    VoiceInfo,
    SynthesisResult,
    SynthesisSegment,
    AudioFormat,
)

logger = logging.getLogger(__name__)


class Dia2Engine(BaseEngine):
    """
    Dia2 TTS engine - NotebookLM-like multi-speaker conversations.
    
    Supports two speakers [S1] and [S2] for natural dialogue.
    """
    
    def __init__(self):
        self._dia = None
        self._model = None
        self._available = None
        self._loaded = False
    
    @property
    def name(self) -> str:
        return "dia2"
    
    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            name="dia2",
            multi_speaker=True,
            max_speakers=2,
            supports_streaming=True,
            requires_gpu=False,  # Works on CPU, faster with GPU/MPS
            model_size_mb=2000,  # ~2GB
            quality_rating=4,
        )
    
    def is_available(self) -> bool:
        """Check if Dia2 is installed."""
        if self._available is not None:
            return self._available
        
        try:
            import dia
            self._available = True
        except ImportError:
            self._available = False
        
        return self._available
    
    def load(self) -> None:
        """Load Dia2 model into memory."""
        if self._loaded:
            return
        
        if not self.is_available():
            raise RuntimeError("Dia2 not installed. Run: pip install dia-tts")
        
        try:
            import dia
            import torch
            
            # Detect device (MPS for Apple Silicon, CUDA for NVIDIA, else CPU)
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
            
            logger.info(f"Loading Dia2 model on {device}...")
            self._model = dia.Dia.from_pretrained("nari-labs/Dia-1.6B")
            self._model.to(device)
            self._loaded = True
            logger.info(f"Dia2 loaded successfully on {device}")
            
        except Exception as e:
            logger.error(f"Failed to load Dia2: {e}")
            raise
    
    def unload(self) -> None:
        """Unload Dia2 model to free memory."""
        if self._model is not None:
            import gc
            import torch
            
            del self._model
            self._model = None
            
            # Force garbage collection
            gc.collect()
            
            # Clear GPU/MPS cache if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif torch.backends.mps.is_available():
                torch.mps.empty_cache()
            
            logger.info("Dia2 model unloaded - memory freed")
        
        self._loaded = False
    
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._loaded
    
    def list_voices(self) -> list[VoiceInfo]:
        """List Dia2 voices (speakers)."""
        return [
            VoiceInfo(id="S1", name="Speaker 1 (Host)", gender="neutral"),
            VoiceInfo(id="S2", name="Speaker 2 (Co-host)", gender="neutral"),
        ]
    
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "wav",
    ) -> SynthesisResult:
        """
        Synthesize single-speaker audio.
        
        For Dia2, wraps text with speaker tag.
        """
        if not self._loaded:
            self.load()
        
        voice = voice or "S1"
        script = f"[{voice}] {text}"
        
        return self._generate(script)
    
    def synthesize_multi(
        self,
        segments: list[dict],
        voice_map: dict[str, str] | None = None,
        format: AudioFormat = "wav",
    ) -> SynthesisResult:
        """
        Synthesize multi-speaker conversation.
        
        Dia2 natively supports [S1] and [S2] tags.
        """
        if not self._loaded:
            self.load()
        
        if not segments:
            return SynthesisResult(success=False, error="No segments provided")
        
        # Map speakers to S1/S2
        voice_map = voice_map or {}
        speaker_mapping = {}
        speaker_count = 0
        
        # Build Dia2 script with [S1]/[S2] tags
        script_parts = []
        
        for seg in segments:
            speaker = seg.get("speaker", "narrator")
            text = seg.get("text", "").strip()
            
            if not text:
                continue
            
            # Map speaker to S1 or S2
            if speaker in voice_map:
                dia_speaker = voice_map[speaker]
            elif speaker in speaker_mapping:
                dia_speaker = speaker_mapping[speaker]
            else:
                speaker_count += 1
                dia_speaker = f"S{min(speaker_count, 2)}"
                speaker_mapping[speaker] = dia_speaker
            
            script_parts.append(f"[{dia_speaker}] {text}")
        
        full_script = " ".join(script_parts)
        
        return self._generate(full_script)
    
    def _generate(self, script: str) -> SynthesisResult:
        """Generate audio from Dia2 script."""
        try:
            import numpy as np
            import io
            import wave
            
            # Generate audio
            audio = self._model.generate(script)
            
            # Convert to WAV bytes
            sample_rate = 24000  # Dia2 default
            
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
                
                # Convert float audio to int16
                if isinstance(audio, np.ndarray):
                    audio_int = (audio * 32767).astype(np.int16)
                else:
                    audio_int = (np.array(audio) * 32767).astype(np.int16)
                
                wav.writeframes(audio_int.tobytes())
            
            audio_data = buffer.getvalue()
            duration = len(audio_int) / sample_rate
            
            return SynthesisResult(
                success=True,
                audio_data=audio_data,
                duration_seconds=duration,
                format="wav",
                sample_rate=sample_rate,
            )
            
        except Exception as e:
            logger.error(f"Dia2 synthesis failed: {e}")
            return SynthesisResult(
                success=False,
                error=str(e)
            )
