"""
HEARME Document Analyzer

Parses document structure and extracts metadata for audio preparation.
Does NOT summarize or interpret content - that's the LLM's job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal


SectionType = Literal[
    "heading",
    "paragraph", 
    "code_block",
    "table",
    "list",
    "blockquote",
    "link_reference",
]


@dataclass
class Section:
    """A section of a document."""
    type: SectionType
    content: str
    level: int = 0  # For headings
    language: str | None = None  # For code blocks
    line_start: int = 0
    line_end: int = 0
    
    def model_dump(self) -> dict:
        return {
            "type": self.type,
            "content": self.content[:200] + "..." if len(self.content) > 200 else self.content,
            "level": self.level,
            "language": self.language,
            "lines": [self.line_start, self.line_end],
        }


@dataclass
class DocumentStructure:
    """Parsed structure of a document."""
    path: str
    title: str | None
    sections: list[Section] = field(default_factory=list)
    headings: list[str] = field(default_factory=list)
    word_count: int = 0
    has_code: bool = False
    has_tables: bool = False
    signals: list[str] = field(default_factory=list)
    
    def model_dump(self) -> dict:
        return {
            "path": self.path,
            "title": self.title,
            "sections": [s.model_dump() for s in self.sections],
            "headings": self.headings,
            "word_count": self.word_count,
            "has_code": self.has_code,
            "has_tables": self.has_tables,
            "signals": self.signals,
        }


@dataclass
class AnalysisResult:
    """Result of document analysis."""
    documents: list[DocumentStructure] = field(default_factory=list)
    total_words: int = 0
    
    def model_dump(self) -> dict:
        return {
            "documents": [d.model_dump() for d in self.documents],
            "document_count": len(self.documents),
            "total_words": self.total_words,
        }


# Patterns for signal extraction
SIGNAL_PATTERNS = {
    "installation": r"\b(install|setup|getting started|quick start)\b",
    "api": r"\b(api|endpoint|request|response|method)\b",
    "architecture": r"\b(architecture|design|component|module|layer)\b",
    "config": r"\b(config|configuration|settings|options|environment)\b",
    "deployment": r"\b(deploy|docker|kubernetes|container|production)\b",
    "testing": r"\b(test|testing|spec|coverage|unit test)\b",
    "contributing": r"\b(contribut|pull request|issue|fork)\b",
}


def parse_markdown(content: str, path: str) -> DocumentStructure:
    """
    Parse Markdown content into structured sections.
    
    Args:
        content: Raw markdown content
        path: File path for reference
    
    Returns:
        DocumentStructure with parsed sections
    """
    lines = content.split("\n")
    sections: list[Section] = []
    headings: list[str] = []
    title: str | None = None
    
    has_code = False
    has_tables = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        
        # Heading
        if line.startswith("#"):
            match = re.match(r"^(#+)\s+(.+)$", line)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                headings.append(heading_text)
                
                if title is None and level == 1:
                    title = heading_text
                
                sections.append(Section(
                    type="heading",
                    content=heading_text,
                    level=level,
                    line_start=line_num,
                    line_end=line_num,
                ))
            i += 1
            continue
        
        # Code block
        if line.startswith("```"):
            has_code = True
            language = line[3:].strip() or None
            code_lines = [line]
            start_line = line_num
            i += 1
            
            while i < len(lines) and not lines[i].startswith("```"):
                code_lines.append(lines[i])
                i += 1
            
            if i < len(lines):
                code_lines.append(lines[i])
                i += 1
            
            sections.append(Section(
                type="code_block",
                content="\n".join(code_lines),
                language=language,
                line_start=start_line,
                line_end=i,
            ))
            continue
        
        # Table (simple detection)
        if "|" in line and line.strip().startswith("|"):
            has_tables = True
            table_lines = [line]
            start_line = line_num
            i += 1
            
            while i < len(lines) and "|" in lines[i]:
                table_lines.append(lines[i])
                i += 1
            
            sections.append(Section(
                type="table",
                content="\n".join(table_lines),
                line_start=start_line,
                line_end=i,
            ))
            continue
        
        # List
        if re.match(r"^(\s*[-*+]|\s*\d+\.)\s+", line):
            list_lines = [line]
            start_line = line_num
            i += 1
            
            while i < len(lines) and (
                re.match(r"^(\s*[-*+]|\s*\d+\.)\s+", lines[i]) or
                (lines[i].startswith("  ") and lines[i].strip())
            ):
                list_lines.append(lines[i])
                i += 1
            
            sections.append(Section(
                type="list",
                content="\n".join(list_lines),
                line_start=start_line,
                line_end=i,
            ))
            continue
        
        # Blockquote
        if line.startswith(">"):
            quote_lines = [line]
            start_line = line_num
            i += 1
            
            while i < len(lines) and (lines[i].startswith(">") or lines[i].strip() == ""):
                if lines[i].strip() == "" and (i + 1 >= len(lines) or not lines[i + 1].startswith(">")):
                    break
                quote_lines.append(lines[i])
                i += 1
            
            sections.append(Section(
                type="blockquote",
                content="\n".join(quote_lines),
                line_start=start_line,
                line_end=i,
            ))
            continue
        
        # Paragraph (non-empty lines)
        if line.strip():
            para_lines = [line]
            start_line = line_num
            i += 1
            
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "```", "|", ">", "-", "*", "+")):
                para_lines.append(lines[i])
                i += 1
            
            sections.append(Section(
                type="paragraph",
                content="\n".join(para_lines),
                line_start=start_line,
                line_end=i,
            ))
            continue
        
        i += 1
    
    # Extract signals
    signals = extract_signals(content)
    
    # Count words (excluding code blocks)
    text_content = " ".join(
        s.content for s in sections 
        if s.type not in ("code_block", "table")
    )
    word_count = len(text_content.split())
    
    return DocumentStructure(
        path=path,
        title=title,
        sections=sections,
        headings=headings,
        word_count=word_count,
        has_code=has_code,
        has_tables=has_tables,
        signals=signals,
    )


def extract_signals(content: str) -> list[str]:
    """Extract topic signals from content."""
    content_lower = content.lower()
    signals = []
    
    for signal, pattern in SIGNAL_PATTERNS.items():
        if re.search(pattern, content_lower, re.IGNORECASE):
            signals.append(signal)
    
    return signals


def analyze_documents(paths: list[str], root: str = ".") -> AnalysisResult:
    """
    Analyze multiple documents.
    
    Args:
        paths: List of document paths (relative to root)
        root: Root directory
    
    Returns:
        AnalysisResult with all parsed documents
    """
    root_path = Path(root).resolve()
    documents: list[DocumentStructure] = []
    total_words = 0
    
    for path in paths:
        full_path = root_path / path
        
        if not full_path.exists():
            continue
        
        try:
            content = full_path.read_text(encoding="utf-8")
        except Exception:
            continue
        
        structure = parse_markdown(content, path)
        documents.append(structure)
        total_words += structure.word_count
    
    return AnalysisResult(
        documents=documents,
        total_words=total_words,
    )
