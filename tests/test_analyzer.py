"""
Tests for hear-me document analyzer.
"""

import pytest
from hearme.analyzer import (
    parse_markdown,
    analyze_documents,
    extract_signals,
    DocumentStructure,
)


class TestMarkdownParsing:
    """Tests for Markdown parsing."""
    
    def test_parse_title(self):
        """Parse H1 as title."""
        content = "# My Project\n\nSome content."
        result = parse_markdown(content, "test.md")
        assert result.title == "My Project"
    
    def test_parse_headings(self):
        """Parse all headings."""
        content = """# Title
        
## Section 1

### Subsection

## Section 2
"""
        result = parse_markdown(content, "test.md")
        assert "Title" in result.headings
        assert "Section 1" in result.headings
        assert "Section 2" in result.headings
    
    def test_detect_code_blocks(self):
        """Detect presence of code blocks."""
        content = """# Project

```python
def hello():
    print("Hello")
```
"""
        result = parse_markdown(content, "test.md")
        assert result.has_code
    
    def test_detect_tables(self):
        """Detect presence of tables."""
        content = """# Features

| Feature | Status |
|---------|--------|
| API     | Done   |
"""
        result = parse_markdown(content, "test.md")
        assert result.has_tables
    
    def test_word_count_excludes_code(self):
        """Word count should exclude code blocks."""
        content = """# Project

This is the description with ten words in total here.

```python
def this_code_has_many_words_that_should_not_count():
    pass
```
"""
        result = parse_markdown(content, "test.md")
        # Should not include code block words
        assert result.word_count < 50


class TestSignalExtraction:
    """Tests for topic signal extraction."""
    
    def test_detect_installation_signal(self):
        """Detect installation-related content."""
        content = "## Installation\n\nTo install this package..."
        signals = extract_signals(content)
        assert "installation" in signals
    
    def test_detect_api_signal(self):
        """Detect API-related content."""
        content = "## API Reference\n\nThe main endpoint is..."
        signals = extract_signals(content)
        assert "api" in signals
    
    def test_detect_architecture_signal(self):
        """Detect architecture-related content."""
        content = "## Architecture\n\nThe system has three components..."
        signals = extract_signals(content)
        assert "architecture" in signals


class TestDocumentAnalysis:
    """Tests for multi-document analysis."""
    
    def test_analyze_multiple_documents(self, tmp_path):
        """Analyze multiple documents."""
        (tmp_path / "README.md").write_text("# Project\n\nDescription here.")
        (tmp_path / "GUIDE.md").write_text("# Guide\n\nHow to use.")
        
        result = analyze_documents(
            ["README.md", "GUIDE.md"],
            root=str(tmp_path)
        )
        
        assert len(result.documents) == 2
        assert result.total_words > 0
    
    def test_skip_missing_documents(self, tmp_path):
        """Skip documents that don't exist."""
        (tmp_path / "README.md").write_text("# Project")
        
        result = analyze_documents(
            ["README.md", "NONEXISTENT.md"],
            root=str(tmp_path)
        )
        
        assert len(result.documents) == 1
