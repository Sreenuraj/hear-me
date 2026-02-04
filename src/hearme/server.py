"""
HEARME MCP Server

Main server implementation using FastMCP. Exposes 6 core tools:
1. check_prerequisites - Detect platform and dependencies
2. scan_workspace - Find documentation files
3. analyze_documents - Parse document structure
4. propose_audio_plan - Suggest audio generation plan
5. prepare_audio_context - Create LLM-ready narration context
6. render_audio - Generate audio from script
"""

from mcp.server.fastmcp import FastMCP

from hearme.config import load_config
from hearme.prerequisites import check_all_prerequisites
from hearme.scanner import scan_workspace as do_scan_workspace
from hearme.analyzer import analyze_documents as do_analyze_documents
from hearme.context import prepare_audio_context as do_prepare_context
from hearme.planner import propose_audio_plan as do_propose_plan

# Initialize FastMCP server
mcp = FastMCP(
    "hearme",
    description="Replace your README.md with a hearme.mp3 - Transform documentation into conversational audio"
)


# =============================================================================
# Tool 1: check_prerequisites
# =============================================================================

@mcp.tool()
async def check_prerequisites() -> dict:
    """
    Check system prerequisites for HEARME.
    
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
    """
    # Analyze documents first
    analysis = do_analyze_documents(documents, root)
    
    # Prepare context
    context = do_prepare_context(analysis.documents, mode=mode, plan=plan)
    return context.model_dump()


# =============================================================================
# Tool 6: render_audio
# =============================================================================

@mcp.tool()
async def render_audio(
    script: list[dict],
    output_path: str = ".hearme/hearme.audio.wav",
    voice_map: dict | None = None,
    engine: str | None = None,
    persist: bool = True,
    root: str = "."
) -> dict:
    """
    Render audio from an agent-generated script.
    
    Converts script segments into audio using the configured engine.
    Supports multi-speaker synthesis with voice mapping.
    
    Args:
        script: List of {speaker, text} segments
        output_path: Where to save the audio file
        voice_map: Speaker name to voice ID mapping
        engine: Which engine to use (None for best available)
        persist: Whether to save script and manifest files
        root: Project root directory
    
    Example script:
        [
            {"speaker": "narrator", "text": "Welcome to this project..."},
            {"speaker": "peer", "text": "What does it do?"}
        ]
    """
    from hearme.renderer import render_audio as do_render
    from hearme.output import persist_outputs, get_output_path
    
    # Resolve output path
    if output_path == ".hearme/hearme.audio.wav":
        output_path = get_output_path(root)
    
    # Render audio
    result = do_render(
        script=script,
        output_path=output_path,
        voice_map=voice_map,
        engine_name=engine,
    )
    
    if not result.success:
        return result.model_dump()
    
    # Persist outputs if requested
    if persist:
        persist_result = persist_outputs(
            audio_path=result.output_path,
            script=script,
            duration_seconds=result.duration_seconds,
            engine_used=result.engine_used,
            root=root,
        )
        return {
            **result.model_dump(),
            **persist_result,
        }
    
    return result.model_dump()


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
    from hearme.engines.registry import EngineRegistry
    
    cleaned = []
    
    for name in EngineRegistry._instances:
        engine = EngineRegistry._instances[name]
        if hasattr(engine, 'is_loaded') and engine.is_loaded():
            engine.unload()
            cleaned.append(name)
    
    return {
        "success": True,
        "cleaned_engines": cleaned,
        "message": f"Cleaned {len(cleaned)} engine(s). Memory freed."
    }


# =============================================================================
# Tool 8: resource_status (Monitor resource usage)
# =============================================================================

@mcp.tool()
async def resource_status() -> dict:
    """
    Check current resource status of HEARME.
    
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
# Server runner
# =============================================================================

def run_server():
    """Run the HEARME MCP server."""
    # Load configuration
    config = load_config()
    
    # Log startup info
    print(f"HEARME MCP Server v0.1.0")
    print(f"Engine: {config.audio.engine}")
    print(f"Privacy: allow_network={config.privacy.allow_network}")
    
    # Run the server
    mcp.run()


if __name__ == "__main__":
    run_server()
