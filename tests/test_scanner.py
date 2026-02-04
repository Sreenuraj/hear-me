"""
Tests for hear-me workspace scanner.
"""

import pytest
from pathlib import Path
from hear-me.scanner import (
    scan_workspace,
    classify_document,
    is_documentation_file,
    ScanResult,
    DocumentInfo,
)


class TestDocumentClassification:
    """Tests for document type classification."""
    
    def test_readme_classification(self, tmp_path):
        """README files should be classified correctly."""
        readme = tmp_path / "README.md"
        readme.touch()
        assert classify_document(readme) == "readme"
    
    def test_contributing_classification(self, tmp_path):
        """CONTRIBUTING files should be classified correctly."""
        contrib = tmp_path / "CONTRIBUTING.md"
        contrib.touch()
        assert classify_document(contrib) == "contributing"
    
    def test_architecture_classification(self, tmp_path):
        """Architecture docs should be classified correctly."""
        arch = tmp_path / "ARCHITECTURE.md"
        arch.touch()
        assert classify_document(arch) == "architecture"
    
    def test_unknown_classification(self, tmp_path):
        """Unknown docs should be classified as 'other'."""
        other = tmp_path / "random.md"
        other.touch()
        assert classify_document(other) == "other"


class TestDocumentDetection:
    """Tests for documentation file detection."""
    
    def test_markdown_in_docs_dir(self, tmp_path):
        """Markdown in docs directory should be documentation."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        doc = docs_dir / "guide.md"
        doc.touch()
        assert is_documentation_file(doc)
    
    def test_readme_is_doc(self, tmp_path):
        """README files are documentation."""
        readme = tmp_path / "README.md"
        readme.touch()
        assert is_documentation_file(readme)
    
    def test_code_file_not_doc(self, tmp_path):
        """Code files are not documentation."""
        code = tmp_path / "main.py"
        code.touch()
        assert not is_documentation_file(code)


class TestWorkspaceScan:
    """Tests for workspace scanning."""
    
    def test_scan_empty_directory(self, tmp_path):
        """Scanning empty directory returns empty result."""
        result = scan_workspace(str(tmp_path))
        assert isinstance(result, ScanResult)
        assert len(result.documents) == 0
    
    def test_scan_finds_readme(self, tmp_path):
        """Scanner finds README in root."""
        readme = tmp_path / "README.md"
        readme.write_text("# Test Project\n\nThis is a test.")
        
        result = scan_workspace(str(tmp_path))
        assert len(result.documents) == 1
        assert result.documents[0].name == "README.md"
        assert result.documents[0].doc_type == "readme"
    
    def test_scan_finds_docs_directory(self, tmp_path):
        """Scanner finds docs in /docs directory."""
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        
        guide = docs_dir / "guide.md"
        guide.write_text("# Guide\n\nSome content.")
        
        result = scan_workspace(str(tmp_path))
        assert any(d.path == "docs/guide.md" for d in result.documents)
    
    def test_scan_priority_order(self, tmp_path):
        """Documents should be ordered by priority."""
        # Create multiple docs
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "CONTRIBUTING.md").write_text("# Contributing")
        
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "api.md").write_text("# API")
        
        result = scan_workspace(str(tmp_path))
        
        # README should be first (priority 1)
        assert result.documents[0].doc_type == "readme"
    
    def test_scan_respects_gitignore(self, tmp_path):
        """Scanner should respect .gitignore patterns."""
        # Create gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("ignored.md\n")
        
        # Create docs
        docs = tmp_path / "docs"
        docs.mkdir()
        (docs / "included.md").write_text("# Included")
        (docs / "ignored.md").write_text("# Ignored")
        
        result = scan_workspace(str(tmp_path))
        
        paths = [d.path for d in result.documents]
        assert "docs/included.md" in paths
        assert "docs/ignored.md" not in paths
