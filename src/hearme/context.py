"""
hear-me Audio Context Preparer

Transforms document structure into LLM-ready context for audio narration.
Handles non-speakable elements and generates speaker hints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from hearme.analyzer import DocumentStructure, Section


LengthMode = Literal["overview", "balanced", "thorough", "agent-decided"]


# Estimated words per minute for speech
WORDS_PER_MINUTE = 150

# Target durations by mode (in minutes)
TARGET_DURATION = {
    "overview": 3,
    "balanced": 8,
    "thorough": 15,
    "agent-decided": 10,
}

# Target word counts by mode
TARGET_WORDS = {mode: minutes * WORDS_PER_MINUTE for mode, minutes in TARGET_DURATION.items()}


@dataclass
class SpeakerHint:
    """Hint for multi-speaker allocation."""
    section_index: int
    suggested_speaker: str
    reason: str


@dataclass
class TransformedSection:
    """A section transformed for audio."""
    type: str
    content: str
    speakable: bool
    speaker_hint: str | None = None
    original_type: str | None = None


@dataclass 
class AudioContext:
    """LLM-ready context for audio generation."""
    document_path: str
    title: str | None
    sections: list[TransformedSection] = field(default_factory=list)
    speaker_hints: list[SpeakerHint] = field(default_factory=list)
    estimated_words: int = 0
    estimated_duration_minutes: float = 0.0
    mode: LengthMode = "balanced"
    
    def model_dump(self) -> dict:
        return {
            "document_path": self.document_path,
            "title": self.title,
            "sections": [
                {
                    "type": s.type,
                    "content": s.content,
                    "speakable": s.speakable,
                    "speaker_hint": s.speaker_hint,
                }
                for s in self.sections
            ],
            "speaker_hints": [
                {
                    "section_index": h.section_index,
                    "suggested_speaker": h.suggested_speaker,
                    "reason": h.reason,
                }
                for h in self.speaker_hints
            ],
            "estimated_words": self.estimated_words,
            "estimated_duration_minutes": round(self.estimated_duration_minutes, 1),
            "mode": self.mode,
        }


@dataclass
class PreparedContext:
    """Complete prepared context for audio generation."""
    documents: list[AudioContext] = field(default_factory=list)
    total_words: int = 0
    total_duration_minutes: float = 0.0
    mode: LengthMode = "balanced"
    
    def model_dump(self) -> dict:
        return {
            "documents": [d.model_dump() for d in self.documents],
            "total_words": self.total_words,
            "total_duration_minutes": round(self.total_duration_minutes, 1),
            "mode": self.mode,
        }


def transform_section(section: Section) -> TransformedSection:
    """
    Transform a section for spoken narration.
    
    - Code blocks → mention that code exists
    - Tables → describe the table structure
    - Everything else → keep mostly as-is
    """
    if section.type == "code_block":
        lang = section.language or "code"
        line_count = section.content.count("\n")
        return TransformedSection(
            type="code_mention",
            content=f"[There is a {lang} code block here with approximately {line_count} lines]",
            speakable=True,
            original_type="code_block",
        )
    
    if section.type == "table":
        rows = section.content.count("\n")
        return TransformedSection(
            type="table_mention",
            content=f"[There is a table here with approximately {rows} rows]",
            speakable=True,
            original_type="table",
        )
    
    if section.type == "heading":
        return TransformedSection(
            type="heading",
            content=section.content,
            speakable=True,
            speaker_hint="narrator" if section.level == 1 else None,
        )
    
    if section.type == "list":
        # Convert list to more natural format
        items = []
        for line in section.content.split("\n"):
            # Strip list markers
            cleaned = line.lstrip(" -•*+0123456789.")
            if cleaned.strip():
                items.append(cleaned.strip())
        
        return TransformedSection(
            type="list",
            content="; ".join(items) if len(items) <= 5 else f"{'; '.join(items[:3])}; and {len(items) - 3} more items",
            speakable=True,
            original_type="list",
        )
    
    if section.type == "blockquote":
        # Clean blockquote markers
        content = section.content.replace(">", "").strip()
        return TransformedSection(
            type="quote",
            content=content,
            speakable=True,
            original_type="blockquote",
        )
    
    # Paragraph - keep as is
    return TransformedSection(
        type="paragraph",
        content=section.content,
        speakable=True,
    )


def generate_speaker_hints(sections: list[TransformedSection]) -> list[SpeakerHint]:
    """
    Generate hints for multi-speaker allocation.
    
    Suggests alternating speakers for better engagement.
    """
    hints: list[SpeakerHint] = []
    
    current_speaker = "narrator"
    topic_count = 0
    
    for i, section in enumerate(sections):
        if section.type == "heading":
            topic_count += 1
            
            # Alternate speakers on major sections
            if topic_count % 3 == 0:
                hints.append(SpeakerHint(
                    section_index=i,
                    suggested_speaker="peer",
                    reason="Topic shift - suggest peer voice for variety",
                ))
                current_speaker = "peer"
            else:
                current_speaker = "narrator"
        
        elif section.type in ("code_mention", "table_mention"):
            # Technical content could be explained by peer
            if current_speaker == "narrator":
                hints.append(SpeakerHint(
                    section_index=i,
                    suggested_speaker="peer",
                    reason="Technical content - peer can explain",
                ))
    
    return hints


def apply_length_constraints(
    sections: list[TransformedSection],
    mode: LengthMode
) -> list[TransformedSection]:
    """
    Apply length constraints based on mode.
    
    - overview: Focus on headings and first paragraphs
    - balanced: Include most content, summarize long sections
    - thorough: Include everything
    """
    if mode == "thorough" or mode == "agent-decided":
        return sections
    
    target_words = TARGET_WORDS.get(mode, TARGET_WORDS["balanced"])
    
    result: list[TransformedSection] = []
    word_count = 0
    
    for section in sections:
        section_words = len(section.content.split())
        
        # Always include headings
        if section.type == "heading":
            result.append(section)
            word_count += section_words
            continue
        
        # Check if we're over budget
        if word_count + section_words > target_words:
            if mode == "overview":
                # Skip non-essential sections in overview
                if section.type in ("code_mention", "table_mention", "quote"):
                    continue
                
                # Truncate long paragraphs
                if section_words > 50:
                    truncated = " ".join(section.content.split()[:30]) + "..."
                    result.append(TransformedSection(
                        type=section.type,
                        content=truncated,
                        speakable=section.speakable,
                        original_type=section.original_type,
                    ))
                    word_count += 30
                    continue
            
            # balanced mode - include but maybe truncate
            if section_words > 100:
                truncated = " ".join(section.content.split()[:50]) + "..."
                result.append(TransformedSection(
                    type=section.type,
                    content=truncated,
                    speakable=section.speakable,
                    original_type=section.original_type,
                ))
                word_count += 50
                continue
        
        result.append(section)
        word_count += section_words
        
        # Stop if way over budget for overview
        if mode == "overview" and word_count > target_words * 1.5:
            break
    
    return result


def prepare_document_context(
    doc: DocumentStructure,
    mode: LengthMode = "balanced"
) -> AudioContext:
    """
    Prepare a single document for audio generation.
    """
    # Transform sections
    transformed = [transform_section(s) for s in doc.sections]
    
    # Apply length constraints
    constrained = apply_length_constraints(transformed, mode)
    
    # Generate speaker hints
    hints = generate_speaker_hints(constrained)
    
    # Calculate estimates
    word_count = sum(len(s.content.split()) for s in constrained)
    duration = word_count / WORDS_PER_MINUTE
    
    return AudioContext(
        document_path=doc.path,
        title=doc.title,
        sections=constrained,
        speaker_hints=hints,
        estimated_words=word_count,
        estimated_duration_minutes=duration,
        mode=mode,
    )


def prepare_audio_context(
    documents: list[DocumentStructure],
    mode: LengthMode = "balanced",
    plan: dict | None = None
) -> PreparedContext:
    """
    Prepare all documents for audio generation.
    
    Args:
        documents: Analyzed document structures
        mode: Length mode (overview/balanced/thorough)
        plan: Optional audio plan with custom settings
    
    Returns:
        PreparedContext with all documents ready for LLM
    """
    contexts: list[AudioContext] = []
    total_words = 0
    
    for doc in documents:
        ctx = prepare_document_context(doc, mode)
        contexts.append(ctx)
        total_words += ctx.estimated_words
    
    total_duration = total_words / WORDS_PER_MINUTE
    
    return PreparedContext(
        documents=contexts,
        total_words=total_words,
        total_duration_minutes=total_duration,
        mode=mode,
    )
