"""
hear-me Dia2 Audio Engine

High-quality multi-speaker conversational TTS using Nari Labs Dia2.
Produces NotebookLM-like two-host conversations.

Note: Dia2 must be installed separately (no vendored code):
    pip install "dia2 @ git+https://github.com/nari-labs/dia2"

For Apple Silicon (M1/M2/M3), Dia2 uses MPS acceleration automatically.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
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
        self._model = None
        self._gen_config = None
        self._available = None
        self._loaded = False
        self._use_cli = False
        self._repo_dir: Path | None = None
    
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
            import dia2  # noqa: F401
            self._available = True
            return self._available
        except ImportError:
            pass

        # Fallback to uv-based repo runtime
        repo = self._resolve_repo_dir()
        uv = shutil.which("uv")
        if repo and uv:
            self._available = True
        else:
            self._available = False
        
        return self._available

    def _resolve_repo_dir(self) -> Path | None:
        env = os.environ.get("HEARME_DIA2_HOME")
        if env:
            path = Path(env).expanduser().resolve()
            if (path / "pyproject.toml").exists():
                return path

        try:
            from hearme.config import load_config
            cfg = load_config()
            path = Path(cfg.installation.dia2_repo_dir).expanduser().resolve()
            if (path / "pyproject.toml").exists():
                return path
        except Exception:
            pass

        return None
    
    def load(self) -> None:
        """Load Dia2 model into memory."""
        if self._loaded:
            return
        
        if not self.is_available():
            raise RuntimeError("Dia2 engine not installed or repo not found.")
        
        try:
            # =========================================================
            # CRITICAL: Suppress stdout pollution for MCP compatibility
            # HuggingFace Hub warnings and tqdm progress bars write to
            # stdout by default, corrupting the JSON-RPC protocol.
            # =========================================================
            import os
            import sys
            
            # Suppress HuggingFace Hub progress bars and warnings
            os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
            os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
            os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
            
            # Configure tqdm to use stderr or disable entirely
            os.environ["TQDM_DISABLE"] = "1"  # Disable tqdm progress bars
            
            # Suppress transformers/huggingface logging warnings
            import warnings
            warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
            
            try:
                from dia2 import Dia2, GenerationConfig
                self._use_cli = False
            except Exception:
                self._use_cli = True
                self._repo_dir = self._resolve_repo_dir()
                if not self._repo_dir:
                    raise RuntimeError("Dia2 repo not found for uv runtime.")
                self._loaded = True
                logger.info("Dia2 CLI runtime ready")
                return
            import torch
            
            # Detect device (MPS for Apple Silicon, CUDA for NVIDIA, else CPU)
            if torch.backends.mps.is_available():
                device = "mps"
            elif torch.cuda.is_available():
                device = "cuda"
            else:
                device = "cpu"
            
            logger.info(f"Loading Dia2 model on {device}...")
            # Use official Nari Labs repo
            self._model = Dia2.from_repo("nari-labs/Dia2-2B", device=device)
            # Default generation + sampling config (tuned for conversational TTS)
            self._gen_config = GenerationConfig()
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
            
            # Close runtime if available
            if hasattr(self._model, 'close'):
                self._model.close()
            
            del self._model
            self._model = None
            self._gen_config = None
            self._repo_dir = None
            self._use_cli = False
            
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
            # NOTE: Dia2 only supports [S1] and [S2] tags
            # voice_map values like "en_US-amy-medium" are NOT used by Dia2
            # We map speakers based on order of first appearance:
            # - First unique speaker -> S1
            # - Second unique speaker -> S2
            # - All subsequent speakers alternate between S1/S2
            if speaker in speaker_mapping:
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
            if self._use_cli:
                repo = self._repo_dir or self._resolve_repo_dir()
                if not repo:
                    return SynthesisResult(success=False, error="Dia2 repo not configured")
                uv = shutil.which("uv")
                if not uv:
                    return SynthesisResult(success=False, error="uv not installed")

                with tempfile.TemporaryDirectory() as tmpdir:
                    tmpdir_path = Path(tmpdir)
                    input_path = tmpdir_path / "input.txt"
                    output_path = tmpdir_path / "output.wav"
                    input_path.write_text(script, encoding="utf-8")

                    cmd = [
                        uv, "run", "-m", "dia2.cli",
                        "--hf", "nari-labs/Dia2-2B",
                        "--input", str(input_path),
                        str(output_path),
                    ]
                    env = os.environ.copy()
                    env.pop("VIRTUAL_ENV", None)
                    subprocess.run(cmd, cwd=str(repo), check=True, env=env)

                    if not output_path.exists():
                        return SynthesisResult(success=False, error="Dia2 CLI did not create output")

                    import wave
                    audio_data = output_path.read_bytes()
                    with wave.open(str(output_path), "rb") as wav:
                        frames = wav.getnframes()
                        sample_rate = wav.getframerate()
                        duration = frames / float(sample_rate)

                    return SynthesisResult(
                        success=True,
                        audio_data=audio_data,
                        duration_seconds=duration,
                        format="wav",
                        sample_rate=sample_rate,
                    )

            import numpy as np
            import io
            import wave
            
            # Generate audio
            # Dia2 generate returns a GenerationResult object
            result = self._model.generate(
                script,
                config=self._gen_config,
                output_wav=None,
                verbose=False,
            )
            
            waveform = result.waveform  # Tensor [1, samples]
            sample_rate = result.sample_rate
            
            # Convert to numpy
            if hasattr(waveform, 'cpu'):
                audio = waveform.squeeze().detach().cpu().numpy()
            else:
                audio = waveform
            
            # Normalize float audio to int16
            audio_int = (audio * 32767).astype(np.int16)
            
            # Convert to WAV bytes
            buffer = io.BytesIO()
            with wave.open(buffer, 'wb') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.setframerate(sample_rate)
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
