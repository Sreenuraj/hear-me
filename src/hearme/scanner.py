"""
HEARME Workspace Scanner

Discovers and classifies documentation files in a project.
Respects .gitignore patterns and handles large repositories.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

import pathspec


# Document type classification
DocType = Literal[
    "readme",
    "architecture", 
    "contributing",
    "changelog",
    "license",
    "api",
    "guide",
    "other"
]


@dataclass
class DocumentInfo:
    """Information about a discovered document."""
    path: str
    name: str
    size: int
    doc_type: DocType
    priority: int  # Lower = higher priority for audio
    
    def model_dump(self) -> dict:
        return {
            "path": self.path,
            "name": self.name,
            "size": self.size,
            "doc_type": self.doc_type,
            "priority": self.priority,
        }


@dataclass
class ScanResult:
    """Result of workspace scan."""
    root: str
    documents: list[DocumentInfo] = field(default_factory=list)
    skipped: int = 0
    truncated: bool = False
    
    def model_dump(self) -> dict:
        return {
            "root": self.root,
            "documents": [d.model_dump() for d in self.documents],
            "document_count": len(self.documents),
            "skipped": self.skipped,
            "truncated": self.truncated,
        }


# Patterns for document detection
DOC_PATTERNS = {
    "readme": ["readme.md", "readme.txt", "readme.rst", "readme"],
    "architecture": ["architecture.md", "design.md", "adr/*.md"],
    "contributing": ["contributing.md", "contribute.md"],
    "changelog": ["changelog.md", "changes.md", "history.md", "releases.md"],
    "license": ["license", "license.md", "license.txt"],
    "api": ["api.md", "api-reference.md", "openapi.yaml", "swagger.yaml"],
    "guide": ["guide.md", "tutorial.md", "getting-started.md", "quickstart.md"],
}

# Priority order (lower = more important for audio)
DOC_PRIORITY = {
    "readme": 1,
    "architecture": 2,
    "guide": 3,
    "contributing": 4,
    "api": 5,
    "changelog": 6,
    "license": 7,
    "other": 10,
}

# Directories to scan for docs
DOC_DIRECTORIES = ["docs", "doc", "documentation", ".github"]

# Maximum files to scan before truncating
MAX_FILES = 100


def load_gitignore(root: Path) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from workspace root."""
    gitignore_path = root / ".gitignore"
    
    if not gitignore_path.exists():
        return None
    
    try:
        with open(gitignore_path) as f:
            patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitignore", patterns)
    except Exception:
        return None


def classify_document(path: Path) -> DocType:
    """Classify a document based on its name and location."""
    name = path.name.lower()
    
    for doc_type, patterns in DOC_PATTERNS.items():
        for pattern in patterns:
            if "/" in pattern:
                # Directory pattern
                if pattern.replace("*.md", "").rstrip("/") in str(path.parent).lower():
                    return doc_type
            elif name == pattern or name.startswith(pattern.replace(".md", "")):
                return doc_type
    
    return "other"


def is_documentation_file(path: Path) -> bool:
    """Check if a file is likely documentation."""
    name = path.name.lower()
    suffix = path.suffix.lower()
    
    # Known doc file names
    doc_names = ["readme", "contributing", "changelog", "architecture", 
                 "design", "api", "guide", "tutorial", "license", "history"]
    
    # Check by suffix
    if suffix in [".md", ".rst", ".txt"]:
        # Any markdown in docs directory
        if any(d in str(path.parent).lower() for d in DOC_DIRECTORIES):
            return True
        
        # Known doc names
        for doc_name in doc_names:
            if name.startswith(doc_name):
                return True
    
    # README without extension
    if name == "readme" or name == "license":
        return True
    
    return False


def scan_workspace(
    path: str = ".",
    include_all_markdown: bool = False,
    max_files: int = MAX_FILES
) -> ScanResult:
    """
    Scan workspace for documentation files.
    
    Args:
        path: Root path to scan
        include_all_markdown: If True, include all .md files in /docs
        max_files: Maximum number of files to return
    
    Returns:
        ScanResult with discovered documents
    """
    root = Path(path).resolve()
    
    if not root.exists():
        return ScanResult(root=str(root), documents=[], skipped=0)
    
    # Load gitignore
    gitignore = load_gitignore(root)
    
    documents: list[DocumentInfo] = []
    skipped = 0
    truncated = False
    
    # Always check root directory first
    for item in root.iterdir():
        if item.is_file() and is_documentation_file(item):
            doc_type = classify_document(item)
            documents.append(DocumentInfo(
                path=str(item.relative_to(root)),
                name=item.name,
                size=item.stat().st_size,
                doc_type=doc_type,
                priority=DOC_PRIORITY.get(doc_type, 10),
            ))
    
    # Scan doc directories
    for doc_dir_name in DOC_DIRECTORIES:
        doc_dir = root / doc_dir_name
        
        if not doc_dir.exists() or not doc_dir.is_dir():
            continue
        
        for item in doc_dir.rglob("*"):
            if not item.is_file():
                continue
            
            # Check gitignore
            rel_path = item.relative_to(root)
            if gitignore and gitignore.match_file(str(rel_path)):
                skipped += 1
                continue
            
            # Check if documentation
            if include_all_markdown and item.suffix.lower() == ".md":
                pass  # Include all markdown
            elif not is_documentation_file(item):
                continue
            
            # Check limits
            if len(documents) >= max_files:
                truncated = True
                break
            
            doc_type = classify_document(item)
            documents.append(DocumentInfo(
                path=str(rel_path),
                name=item.name,
                size=item.stat().st_size,
                doc_type=doc_type,
                priority=DOC_PRIORITY.get(doc_type, 10),
            ))
        
        if truncated:
            break
    
    # Sort by priority
    documents.sort(key=lambda d: (d.priority, d.path))
    
    return ScanResult(
        root=str(root),
        documents=documents,
        skipped=skipped,
        truncated=truncated,
    )
