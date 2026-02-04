"""
hear-me Mock Audio Engine

A mock engine for development and testing.
Returns placeholder/silent audio without requiring any TTS dependencies.
"""

from __future__ import annotations

import struct
import wave
import io

from hearme.engines.base import (
    BaseEngine,
    EngineCapabilities,
    VoiceInfo,
    SynthesisResult,
    AudioFormat,
)


class MockEngine(BaseEngine):
    """Mock audio engine for testing."""
    
    @property
    def name(self) -> str:
        return "mock"
    
    @property
    def capabilities(self) -> EngineCapabilities:
        return EngineCapabilities(
            name="mock",
            multi_speaker=True,
            max_speakers=10,
            supports_streaming=False,
            requires_gpu=False,
            model_size_mb=0,
            quality_rating=1,
        )
    
    def is_available(self) -> bool:
        """Mock engine is always available."""
        return True
    
    def list_voices(self) -> list[VoiceInfo]:
        """Return mock voices."""
        return [
            VoiceInfo(id="narrator", name="Mock Narrator", gender="neutral"),
            VoiceInfo(id="host", name="Mock Host", gender="neutral"),
            VoiceInfo(id="expert", name="Mock Expert", gender="neutral"),
        ]
    
    def synthesize(
        self,
        text: str,
        voice: str | None = None,
        format: AudioFormat = "mp3",
    ) -> SynthesisResult:
        """
        Generate placeholder audio.
        
        Duration is estimated based on text length (150 words/minute).
        """
        # Estimate duration
        word_count = len(text.split())
        duration = word_count / 150 * 60  # seconds
        duration = max(0.5, duration)  # Minimum 0.5 seconds
        
        # Generate silent WAV
        sample_rate = 24000
        num_samples = int(sample_rate * duration)
        
        # Create WAV file in memory
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)  # 16-bit
            wav.setframerate(sample_rate)
            
            # Write silence (zeros)
            silence = struct.pack('<' + 'h' * num_samples, *([0] * num_samples))
            wav.writeframes(silence)
        
        audio_data = buffer.getvalue()
        
        # Note: For real implementation, we'd convert to MP3 if requested
        # For mock, we return WAV regardless (simpler)
        actual_format: AudioFormat = "wav"
        
        return SynthesisResult(
            success=True,
            audio_data=audio_data,
            duration_seconds=duration,
            format=actual_format,
            sample_rate=sample_rate,
        )
