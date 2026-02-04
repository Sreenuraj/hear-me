"""
hear-me Audio Renderer

Renders audio from agent-generated scripts using the engine abstraction.
Handles multi-speaker synthesis, voice mapping, and audio concatenation.
"""

from __future__ import annotations

import io
import logging
import wave
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from hearme.engines import get_engine, AudioEngine
from hearme.engines.base import AudioFormat, SynthesisResult, SynthesisSegment
from hearme.config import load_config

logger = logging.getLogger(__name__)


@dataclass
class ScriptSegment:
    """A segment in an audio script."""
    speaker: str
    text: str
    pause_after: float = 0.5  # seconds


@dataclass
class RenderResult:
    """Result of audio rendering."""
    success: bool
    output_path: str | None = None
    duration_seconds: float = 0.0
    segment_count: int = 0
    engine_used: str | None = None
    format: AudioFormat = "wav"
    error: str | None = None
    
    def model_dump(self) -> dict:
        return {
            "success": self.success,
            "output_path": self.output_path,
            "duration_seconds": round(self.duration_seconds, 2),
            "segment_count": self.segment_count,
            "engine_used": self.engine_used,
            "format": self.format,
            "error": self.error,
        }


def parse_script(script: list[dict]) -> list[ScriptSegment]:
    """
    Parse a script into segments.
    
    Args:
        script: List of {speaker, text, pause_after?} dicts
    
    Returns:
        List of ScriptSegment objects
    """
    segments = []
    
    for item in script:
        if not isinstance(item, dict):
            continue
        
        speaker = item.get("speaker", "narrator")
        text = item.get("text", "")
        pause = item.get("pause_after", 0.5)
        
        if text.strip():
            segments.append(ScriptSegment(
                speaker=speaker,
                text=text.strip(),
                pause_after=pause,
            ))
    
    return segments


def validate_script(segments: list[ScriptSegment]) -> tuple[bool, str | None]:
    """Validate a parsed script."""
    if not segments:
        return False, "Script is empty"
    
    total_chars = sum(len(s.text) for s in segments)
    if total_chars > 100000:  # ~20 minutes of audio
        return False, f"Script too long ({total_chars} chars). Maximum is 100,000."
    
    return True, None


def concatenate_wav(segments: list[SynthesisSegment], sample_rate: int = 24000) -> bytes:
    """
    Concatenate WAV audio segments.
    
    Args:
        segments: List of synthesis segments with audio data
        sample_rate: Sample rate for output
    
    Returns:
        Combined WAV audio as bytes
    """
    if not segments:
        return b""
    
    all_frames = []
    
    for seg in segments:
        if not seg.audio_data:
            continue
        
        try:
            # Read WAV data
            buffer = io.BytesIO(seg.audio_data)
            with wave.open(buffer, 'rb') as wav:
                frames = wav.readframes(wav.getnframes())
                all_frames.append(frames)
        except Exception as e:
            logger.warning(f"Failed to read segment audio: {e}")
            continue
    
    if not all_frames:
        return b""
    
    # Write combined WAV
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(all_frames))
    
    return output.getvalue()


def _chunk_segments(
    segments: list[dict],
    max_chars: int,
) -> list[list[dict]]:
    """Chunk script segments by character count."""
    if max_chars <= 0:
        return [segments]

    chunks: list[list[dict]] = []
    current: list[dict] = []
    current_chars = 0

    for seg in segments:
        text = seg.get("text", "")
        seg_len = len(text)
        if current and current_chars + seg_len > max_chars:
            chunks.append(current)
            current = [seg]
            current_chars = seg_len
        else:
            current.append(seg)
            current_chars += seg_len

    if current:
        chunks.append(current)

    return chunks


def render_audio(
    script: list[dict],
    output_path: str = ".hear-me/hear-me.audio.wav",
    voice_map: dict[str, str] | None = None,
    engine_name: str | None = None,
    format: AudioFormat = "wav",
) -> RenderResult:
    """
    Render audio from an agent-generated script.
    
    BULLETPROOF RESOURCE MANAGEMENT:
    - Engine models load only when needed
    - Models unload immediately after render (even on error)
    - Memory freed automatically via try/finally
    
    Args:
        script: List of {speaker, text} segments
        output_path: Where to save the audio file
        voice_map: Speaker name to voice ID mapping
        engine_name: Specific engine to use, or None for best available
        format: Output audio format
    
    Returns:
        RenderResult with success status and metadata
    """
    # Parse and validate script
    segments = parse_script(script)
    valid, error = validate_script(segments)
    
    if not valid:
        return RenderResult(success=False, error=error)
    
    # Get engine
    engine = get_engine(engine_name)
    if not engine:
        return RenderResult(
            success=False,
            error=f"No audio engine available. Install kokoro: pip install kokoro"
        )
    
    if not engine.is_available():
        return RenderResult(
            success=False,
            error=f"Engine '{engine.name}' is not available"
        )
    
    logger.info(f"Rendering {len(segments)} segments with {engine.name} engine")
    
    # Convert to format expected by engine
    script_dicts = [{"speaker": s.speaker, "text": s.text} for s in segments]
    total_chars = sum(len(s["text"]) for s in script_dicts)
    
    # =========================================================================
    # BULLETPROOF: Use context manager for guaranteed cleanup
    # =========================================================================
    try:
        # Load engine (models into memory)
        engine.load()
        logger.info(f"Engine {engine.name} loaded")
        
        # Synthesize (chunked for Dia2)
        if engine.name == "dia2":
            config = load_config()
            max_chars = getattr(config.audio, "max_chars_per_chunk", 2000)
            chunks = _chunk_segments(script_dicts, max_chars) if total_chars > max_chars else [script_dicts]

            all_segments: list[SynthesisSegment] = []
            total_duration = 0.0
            sample_rate = 24000

            for chunk in chunks:
                result = engine.synthesize_multi(
                    segments=chunk,
                    voice_map=voice_map,
                    format=format,
                )
                if not result.success:
                    return RenderResult(
                        success=False,
                        error=result.error,
                        engine_used=engine.name,
                    )

                sample_rate = result.sample_rate or sample_rate
                total_duration += result.duration_seconds

                if result.segments:
                    all_segments.extend(result.segments)
                elif result.audio_data:
                    all_segments.append(
                        SynthesisSegment(
                            speaker="chunk",
                            text="",
                            audio_data=result.audio_data,
                            duration_seconds=result.duration_seconds,
                            sample_rate=sample_rate,
                        )
                    )

            result = SynthesisResult(
                success=True,
                audio_data=None,
                duration_seconds=total_duration,
                format="wav",
                sample_rate=sample_rate,
                segments=all_segments,
            )
        else:
            result = engine.synthesize_multi(
                segments=script_dicts,
                voice_map=voice_map,
                format=format,
            )
        
        if not result.success:
            return RenderResult(
                success=False,
                error=result.error,
                engine_used=engine.name,
            )
        
        # Concatenate audio properly
        if result.segments:
            audio_data = concatenate_wav(result.segments, result.sample_rate)
        else:
            audio_data = result.audio_data or b""
        
        # Ensure output directory exists (fallback to user home if not writable)
        output_file = Path(output_path)
        if not output_file.is_absolute():
            output_file = Path.cwd() / output_file
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback_dir = Path.home() / ".hear-me"
            fallback_dir.mkdir(parents=True, exist_ok=True)
            output_file = fallback_dir / output_file.name
        
        # Write output file
        output_file.write_bytes(audio_data)
        logger.info(f"Audio saved to {output_file}")
        
        return RenderResult(
            success=True,
            output_path=str(output_file.absolute()),
            duration_seconds=result.duration_seconds,
            segment_count=len(segments),
            engine_used=engine.name,
            format="wav",
        )
        
    except Exception as e:
        logger.error(f"Render failed: {e}")
        return RenderResult(
            success=False,
            error=f"Render failed: {e}",
            engine_used=engine.name if engine else None,
        )
        
    finally:
        # =====================================================================
        # GUARANTEED CLEANUP: Always unload, even on error
        # =====================================================================
        if engine and engine.is_loaded():
            engine.unload()
            logger.info(f"Engine {engine.name} unloaded - memory freed")
