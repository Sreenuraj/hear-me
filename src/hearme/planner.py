"""
hear-me Audio Plan Proposer

Suggests audio generation strategy based on document analysis.
Proposes speaker assignments, document ordering, and duration estimates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from hearme.analyzer import DocumentStructure
from hearme.scanner import DocumentInfo


AudioMode = Literal[
    "explainer",      # Single narrator explaining
    "discussion",     # Multi-speaker conversation
    "narrative",      # Story-like walkthrough
    "tour",           # Interactive tour style
    "agent-decided",  # Let the agent choose
]


@dataclass
class SpeakerAssignment:
    """Assignment of a speaker to content."""
    speaker: str
    voice_style: str
    content_types: list[str]
    description: str


@dataclass
class DocumentOrder:
    """Ordering of a document in the audio."""
    path: str
    order: int
    reason: str
    estimated_duration_minutes: float


@dataclass
class Ambiguity:
    """An ambiguity that needs agent resolution."""
    type: str
    description: str
    options: list[str]
    default: str


@dataclass
class AudioPlan:
    """Proposed audio generation plan."""
    mode: AudioMode
    mode_reason: str
    
    documents: list[DocumentOrder] = field(default_factory=list)
    speakers: list[SpeakerAssignment] = field(default_factory=list)
    ambiguities: list[Ambiguity] = field(default_factory=list)
    
    estimated_duration_minutes: float = 0.0
    estimated_word_count: int = 0
    
    def model_dump(self) -> dict:
        return {
            "mode": self.mode,
            "mode_reason": self.mode_reason,
            "documents": [
                {
                    "path": d.path,
                    "order": d.order,
                    "reason": d.reason,
                    "estimated_duration_minutes": round(d.estimated_duration_minutes, 1),
                }
                for d in self.documents
            ],
            "speakers": [
                {
                    "speaker": s.speaker,
                    "voice_style": s.voice_style,
                    "content_types": s.content_types,
                    "description": s.description,
                }
                for s in self.speakers
            ],
            "ambiguities": [
                {
                    "type": a.type,
                    "description": a.description,
                    "options": a.options,
                    "default": a.default,
                }
                for a in self.ambiguities
            ],
            "estimated_duration_minutes": round(self.estimated_duration_minutes, 1),
            "estimated_word_count": self.estimated_word_count,
        }


# Default speaker configurations by mode
SPEAKER_CONFIGS = {
    "explainer": [
        SpeakerAssignment(
            speaker="narrator",
            voice_style="professional",
            content_types=["all"],
            description="Single authoritative voice explaining the project",
        ),
    ],
    "discussion": [
        SpeakerAssignment(
            speaker="host",
            voice_style="warm",
            content_types=["introduction", "transitions", "summary"],
            description="Primary voice guiding the conversation",
        ),
        SpeakerAssignment(
            speaker="expert",
            voice_style="technical",
            content_types=["technical", "code", "architecture"],
            description="Technical expert explaining implementation details",
        ),
    ],
    "narrative": [
        SpeakerAssignment(
            speaker="storyteller",
            voice_style="engaging",
            content_types=["all"],
            description="Engaging narrator telling the project's story",
        ),
    ],
    "tour": [
        SpeakerAssignment(
            speaker="guide",
            voice_style="friendly",
            content_types=["navigation", "descriptions"],
            description="Friendly guide showing around the codebase",
        ),
        SpeakerAssignment(
            speaker="visitor",
            voice_style="curious",
            content_types=["questions"],
            description="Curious visitor asking clarifying questions",
        ),
    ],
}


def suggest_mode(documents: list[DocumentStructure]) -> tuple[AudioMode, str]:
    """
    Suggest the best audio mode based on document characteristics.
    """
    total_words = sum(d.word_count for d in documents)
    has_code = any(d.has_code for d in documents)
    has_architecture = any("architecture" in d.signals for d in documents)
    doc_count = len(documents)
    
    # Simple heuristics for mode selection
    if doc_count == 1 and total_words < 500:
        return "explainer", "Single short document - straightforward explanation works best"
    
    if has_architecture or has_code:
        return "discussion", "Technical content detected - discussion format helps explain complexity"
    
    if doc_count > 3:
        return "tour", "Multiple documents - tour format helps navigate the content"
    
    return "discussion", "Default choice for engaging multi-speaker content"


def order_documents(
    documents: list[DocumentInfo] | list[DocumentStructure],
    structures: list[DocumentStructure] | None = None
) -> list[DocumentOrder]:
    """
    Order documents for audio generation.
    
    Priority:
    1. README (introduction)
    2. Architecture (big picture)
    3. Guides (how-to)
    4. Everything else
    """
    # Map structures by path if provided
    struct_map = {}
    if structures:
        struct_map = {s.path: s for s in structures}
    
    ordered: list[DocumentOrder] = []
    
    # Sort by priority if DocumentInfo, otherwise use signals
    if documents and hasattr(documents[0], 'priority'):
        docs_sorted = sorted(documents, key=lambda d: d.priority)
    else:
        docs_sorted = documents
    
    for i, doc in enumerate(docs_sorted):
        path = doc.path if hasattr(doc, 'path') else str(doc)
        
        # Estimate duration
        if path in struct_map:
            word_count = struct_map[path].word_count
        elif hasattr(doc, 'size'):
            word_count = doc.size // 5  # Rough estimate
        else:
            word_count = 500
        
        duration = word_count / 150  # words per minute
        
        # Determine reason
        if hasattr(doc, 'doc_type'):
            reason = f"Priority {doc.priority}: {doc.doc_type} document"
        else:
            reason = f"Document {i + 1}"
        
        ordered.append(DocumentOrder(
            path=path,
            order=i + 1,
            reason=reason,
            estimated_duration_minutes=duration,
        ))
    
    return ordered


def identify_ambiguities(documents: list[DocumentStructure]) -> list[Ambiguity]:
    """
    Identify ambiguities that need agent resolution.
    """
    ambiguities: list[Ambiguity] = []
    
    # Check for multiple README-like files
    readmes = [d for d in documents if d.title and "readme" in d.path.lower()]
    if len(readmes) > 1:
        ambiguities.append(Ambiguity(
            type="multiple_readmes",
            description="Multiple README files detected",
            options=[d.path for d in readmes],
            default=readmes[0].path,
        ))
    
    # Check for very long content
    total_words = sum(d.word_count for d in documents)
    if total_words > 5000:
        ambiguities.append(Ambiguity(
            type="long_content",
            description=f"Content is long ({total_words} words). Consider using 'overview' mode or selecting fewer documents.",
            options=["overview", "balanced", "thorough"],
            default="balanced",
        ))
    
    # Check for code-heavy content
    code_heavy = [d for d in documents if d.has_code and d.word_count < 200]
    if code_heavy:
        ambiguities.append(Ambiguity(
            type="code_heavy",
            description="Some documents are mostly code with little explanation",
            options=["skip_code_docs", "include_all", "summarize"],
            default="summarize",
        ))
    
    return ambiguities


def propose_audio_plan(
    documents: list[DocumentInfo] | list[DocumentStructure],
    structures: list[DocumentStructure] | None = None,
    mode: AudioMode = "agent-decided",
    length: str = "balanced",
    force_single_speaker: bool = False,
) -> AudioPlan:
    """
    Propose an audio generation plan.
    
    Args:
        documents: Document info from scanner or structures from analyzer
        structures: Optional pre-analyzed structures
        mode: Requested audio mode (or agent-decided)
        length: Content depth level
    
    Returns:
        AudioPlan with suggested strategy
    """
    # Get structures if not provided
    if structures is None:
        if documents and hasattr(documents[0], 'sections'):
            structures = documents
        else:
            structures = []
    
    # Suggest mode if not specified
    if mode == "agent-decided":
        mode, mode_reason = suggest_mode(structures)
    else:
        mode_reason = f"Mode '{mode}' was explicitly requested"

    if force_single_speaker:
        mode = "explainer"
        mode_reason = "Single-speaker engine detected - forcing explainer mode"
    
    # Order documents
    ordered = order_documents(documents, structures)
    
    # Get speaker configuration
    if force_single_speaker:
        speakers = SPEAKER_CONFIGS["explainer"]
    else:
        speakers = SPEAKER_CONFIGS.get(mode, SPEAKER_CONFIGS["discussion"])
    
    # Identify ambiguities
    ambiguities = identify_ambiguities(structures)
    
    # Calculate estimates
    total_duration = sum(d.estimated_duration_minutes for d in ordered)
    total_words = int(total_duration * 150)
    
    return AudioPlan(
        mode=mode,
        mode_reason=mode_reason,
        documents=ordered,
        speakers=speakers,
        ambiguities=ambiguities,
        estimated_duration_minutes=total_duration,
        estimated_word_count=total_words,
    )
