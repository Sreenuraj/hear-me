"""
hear-me MCP Server

Main server implementation using FastMCP. Exposes 6 core tools:
1. check_prerequisites - Detect platform and dependencies
2. scan_workspace - Find documentation files
3. analyze_documents - Parse document structure
4. propose_audio_plan - Suggest audio generation plan
5. prepare_audio_context - Create LLM-ready narration context
6. render_audio - Generate audio from script
"""

# =============================================================================
# CRITICAL: Suppress stdout pollution BEFORE any imports
# HuggingFace Hub, tqdm, and other libraries write to stdout by default,
# which corrupts the MCP JSON-RPC protocol. This MUST be at the very top.
# =============================================================================
import os
import sys
import warnings

# Suppress HuggingFace Hub progress bars and warnings
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["HF_HUB_DISABLE_IMPLICIT_TOKEN"] = "1"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Disable tqdm progress bars globally
os.environ["TQDM_DISABLE"] = "1"

# Suppress common library warnings that might go to stdout
warnings.filterwarnings("ignore", message=".*unauthenticated requests.*")
warnings.filterwarnings("ignore", category=UserWarning)

# Force tqdm to use stderr if it somehow still runs
try:
    import tqdm
    tqdm.tqdm = lambda *args, **kwargs: iter(args[0]) if args else iter([])
except ImportError:
    pass

from mcp.server.fastmcp import FastMCP

from hearme.config import load_config
from hearme.cleanup import cleanup_resources as do_cleanup_resources
from hearme.prerequisites import check_all_prerequisites
from hearme.scanner import scan_workspace as do_scan_workspace
from hearme.analyzer import analyze_documents as do_analyze_documents
from hearme.context import prepare_audio_context as do_prepare_context
from hearme.planner import propose_audio_plan as do_propose_plan

# Initialize FastMCP server
# Initialize FastMCP server
mcp = FastMCP("hear-me")


# =============================================================================
# Tool 1: check_prerequisites
# =============================================================================

@mcp.tool()
async def check_prerequisites() -> dict:
    """
    Check system prerequisites for hear-me.
    
    Detects:
    - Platform (macOS/Linux/Windows)
    - Python version
    - Audio engine availability (VibeVoice, Kokoro, etc.)
    - System dependencies (ffmpeg, espeak-ng)
    
    Returns a report with installation guidance if prerequisites are missing.
    """
    report = check_all_prerequisites()
    return report.model_dump()


# =============================================================================
# Tool 2: scan_workspace
# =============================================================================

@mcp.tool()
async def scan_workspace(path: str = ".") -> dict:
    """
    Scan workspace for documentation files.
    
    Detects README, ARCHITECTURE, CONTRIBUTING, and other docs.
    Returns file paths with metadata (size, type, priority).
    
    Args:
        path: Root path to scan (defaults to current directory)
    """
    result = do_scan_workspace(path)
    return result.model_dump()


# =============================================================================
# Tool 3: analyze_documents
# =============================================================================

@mcp.tool()
async def analyze_documents(documents: list[str], root: str = ".") -> dict:
    """
    Analyze document structure for audio preparation.
    
    Parses headings, sections, and extracts signals.
    Does NOT summarize or interpret content.
    
    Args:
        documents: List of document paths to analyze
        root: Root directory for resolving paths
    
    Note:
        If you already have explicit document paths, you can call this
        directly and skip scan_workspace.
    """
    result = do_analyze_documents(documents, root)
    return result.model_dump()


# =============================================================================
# Tool 3b: analyze_provided_documents (alias for explicit doc lists)
# =============================================================================

@mcp.tool()
async def analyze_provided_documents(documents: list[str], root: str = ".") -> dict:
    """
    Analyze explicitly provided document paths.
    
    Use this when you already have a list of docs and want to skip scanning.
    """
    result = do_analyze_documents(documents, root)
    return result.model_dump()


# =============================================================================
# Tool 4: propose_audio_plan
# =============================================================================

@mcp.tool()
async def propose_audio_plan(
    documents: list[str],
    mode: str = "agent-decided",
    length: str = "balanced",
    root: str = "."
) -> dict:
    """
    Propose an audio generation plan.
    
    Suggests document ordering, speaker assignments, and identifies
    ambiguities that need agent resolution.
    
    Args:
        documents: Documents to include in the audio
        mode: Audio mode (explainer, discussion, narrative, tour, agent-decided)
        length: Depth level (overview, balanced, thorough)
        root: Root directory for resolving paths
    
    Note:
        If documents are explicitly provided, you can skip scan_workspace.
    """
    # Analyze documents first to get structure
    analysis = do_analyze_documents(documents, root)
    
    # Generate plan
    plan = do_propose_plan(
        documents=analysis.documents,
        structures=analysis.documents,
        mode=mode,
        length=length,
    )
    return plan.model_dump()


# =============================================================================
# Tool 5: prepare_audio_context
# =============================================================================

@mcp.tool()
async def prepare_audio_context(
    documents: list[str],
    mode: str = "balanced",
    root: str = ".",
    plan: dict | None = None
) -> dict:
    """
    Prepare LLM-ready context for audio narration.
    
    Transforms document content into a format optimized for
    spoken explanation. Handles non-speakable elements appropriately.
    
    Args:
        documents: Documents to prepare
        mode: Length mode (overview, balanced, thorough)
        root: Root directory for resolving paths
        plan: Optional audio plan from propose_audio_plan
    
    Note:
        If documents are explicitly provided, you can skip scan_workspace.
    """
    # Analyze documents first
    analysis = do_analyze_documents(documents, root)

    # Auto-adjust length for very large inputs when mode not explicitly set
    effective_mode = mode
    if mode == "balanced" and analysis.total_words > 3000:
        effective_mode = "overview"
    
    # Prepare context
    context = do_prepare_context(analysis.documents, mode=effective_mode, plan=plan)
    return context.model_dump()


# =============================================================================
# Tool 6: render_audio
# =============================================================================

@mcp.tool()
async def render_audio(
    script: list[dict],
    output_path: str = ".hear-me/hear-me.audio.wav",
    voice_map: dict | None = None,
    engine: str | None = None,
    persist: bool = True,
    root: str = ".",
    cleanup: bool = True,
) -> dict:
    """
    Render audio from an agent-generated script.
    
    Converts script segments into audio using the configured engine.
    Supports multi-speaker synthesis with voice mapping.
    
    Args:
        script: List of {speaker, text} segments
        output_path: Where to save the audio file
        voice_map: Speaker name to voice ID mapping
        engine: Which engine to use (None uses configured default)
        persist: Whether to save script and manifest files
        root: Project root directory
        cleanup: Whether to cleanup engine resources after render
    
    Example script:
        [
            {"speaker": "narrator", "text": "Welcome to this project..."},
            {"speaker": "peer", "text": "What does it do?"}
        ]
    """
    from hearme.renderer import render_audio as do_render
    from hearme.output import persist_outputs, get_output_path
    
    # Resolve output path
    if root == ".":
        root = os.getcwd()
    if output_path == ".hear-me/hear-me.audio.wav":
        output_path = get_output_path(root)
    else:
        # If relative, resolve against root
        from pathlib import Path
        path = Path(output_path)
        if not path.is_absolute():
            output_path = str(Path(root) / path)
    
    # Use configured default engine if not provided
    if engine is None:
        config = load_config()
        engine = config.audio.engine

    # Render audio
    result = do_render(
        script=script,
        output_path=output_path,
        voice_map=voice_map,
        engine_name=engine,
    )
    
    if not result.success:
        response = result.model_dump()
        if cleanup:
            do_cleanup_resources()
        if os.environ.get("HEARME_AUTOSHUTDOWN") == "1":
            import threading
            threading.Timer(0.5, lambda: os._exit(0)).start()
        return response
    
    # Persist outputs if requested
    if persist:
        # If output is inside a .hear-me folder, persist next to it
        from pathlib import Path
        output_parent = Path(output_path).parent
        if output_parent.name == ".hear-me":
            persist_root = str(output_parent.parent)
        else:
            persist_root = root

        persist_result = persist_outputs(
            audio_path=result.output_path,
            script=script,
            duration_seconds=result.duration_seconds,
            engine_used=result.engine_used,
            root=persist_root,
        )
        response = {
            **result.model_dump(),
            **persist_result,
        }
    else:
        response = result.model_dump()

    # Cleanup resources after render if requested
    if cleanup:
        do_cleanup_resources()

    # Optional auto-shutdown for one-shot usage
    if os.environ.get("HEARME_AUTOSHUTDOWN") == "1":
        import threading
        threading.Timer(0.5, lambda: os._exit(0)).start()

    return response


# =============================================================================
# Tool 7: cleanup_resources (BULLETPROOF RESOURCE MANAGEMENT)
# =============================================================================

@mcp.tool()
async def cleanup_resources() -> dict:
    """
    Force cleanup of all loaded TTS engine resources.
    
    Use this to immediately free memory after audio generation,
    or if you suspect resources weren't properly cleaned up.
    
    This is a safety net - normally resources are cleaned automatically
    after each render_audio call.
    """
    return do_cleanup_resources()


# =============================================================================
# Tool 8: resource_status (Monitor resource usage)
# =============================================================================

@mcp.tool()
async def resource_status() -> dict:
    """
    Check current resource status of hear-me.
    
    Returns which engines are loaded and their memory estimates.
    Useful for debugging or verifying cleanup worked.
    """
    from hearme.engines.registry import EngineRegistry
    
    engines_status = []
    
    for name in EngineRegistry._engines:
        engine = EngineRegistry.get(name)
        if engine:
            loaded = engine.is_loaded() if hasattr(engine, 'is_loaded') else False
            engines_status.append({
                "name": name,
                "loaded": loaded,
                "available": engine.is_available(),
                "memory_mb": engine.capabilities.model_size_mb if loaded else 0,
            })
    
    total_memory = sum(e["memory_mb"] for e in engines_status)
    
    return {
        "engines": engines_status,
        "total_memory_mb": total_memory,
        "status": "clean" if total_memory == 0 else "models_loaded"
    }


# =============================================================================
# Tool 9: troubleshoot_hear-me (Self-diagnosis)
# =============================================================================

@mcp.tool()
async def troubleshoot_hearme() -> dict:
    """
    Run self-diagnosis to identify setup issues.
    
    Checks:
    - Python version and environment
    - Required dependencies (ffmpeg)
    - Installed engines and their status
    
    Use this if you encounter errors or missing engines.
    """
    from hearme.troubleshoot import run_diagnostics
    return run_diagnostics()


# =============================================================================
# Server runner
# =============================================================================

def run_server():
    """Run the hear-me MCP server."""
    # Load configuration
    config = load_config()
    
    # Log startup info
    # Logging to stderr to avoid breaking JSON-RPC on stdout
    import sys
    print(f"hear-me MCP Server v0.1.0", file=sys.stderr)
    print(f"Engine: {config.audio.engine}", file=sys.stderr)
    print(f"Privacy: allow_network={config.privacy.allow_network}", file=sys.stderr)
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    run_server()
