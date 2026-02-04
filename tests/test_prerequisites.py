"""
Tests for HEARME prerequisite detection system.
"""

import pytest
from hearme.prerequisites import (
    detect_platform,
    check_python_version,
    check_command_exists,
    check_all_prerequisites,
    PrerequisiteReport,
)


class TestPlatformDetection:
    """Tests for platform detection."""
    
    def test_detect_platform_returns_tuple(self):
        """Platform detection should return (platform, name) tuple."""
        platform, name = detect_platform()
        assert platform in ("darwin", "linux", "windows")
        assert isinstance(name, str)
        assert len(name) > 0


class TestPythonVersion:
    """Tests for Python version checking."""
    
    def test_check_python_version_returns_tuple(self):
        """Python check should return (version, ok) tuple."""
        version, ok = check_python_version()
        assert isinstance(version, str)
        assert isinstance(ok, bool)
    
    def test_python_version_format(self):
        """Version should be in X.Y.Z format."""
        version, _ = check_python_version()
        parts = version.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)
    
    def test_current_python_is_ok(self):
        """Current Python (running tests) should be >= 3.10."""
        _, ok = check_python_version()
        assert ok, "Tests require Python 3.10+"


class TestCommandExists:
    """Tests for system command detection."""
    
    def test_existing_command(self):
        """Check a command that should exist (python)."""
        status = check_command_exists("python3")
        assert status.installed
        assert status.path is not None
    
    def test_nonexistent_command(self):
        """Check a command that definitely doesn't exist."""
        status = check_command_exists("nonexistent_command_xyz")
        assert not status.installed
        assert status.install_hint is not None


class TestPrerequisiteReport:
    """Tests for complete prerequisite check."""
    
    def test_full_report_structure(self):
        """Full prerequisite check should return complete report."""
        report = check_all_prerequisites()
        
        assert isinstance(report, PrerequisiteReport)
        assert report.platform in ("darwin", "linux", "windows")
        assert isinstance(report.python_version, str)
        assert isinstance(report.python_ok, bool)
        assert isinstance(report.audio_engines, dict)
        assert isinstance(report.system_deps, dict)
        assert isinstance(report.ready, bool)
        assert isinstance(report.missing, list)
    
    def test_report_serialization(self):
        """Report should serialize to dict for JSON output."""
        report = check_all_prerequisites()
        data = report.model_dump()
        
        assert isinstance(data, dict)
        assert "platform" in data
        assert "audio_engines" in data
        assert "system_deps" in data
        assert "ready" in data
    
    def test_audio_engines_checked(self):
        """All expected audio engines should be checked."""
        report = check_all_prerequisites()
        
        expected_engines = ["vibevoice", "dia2", "chattts", "kokoro", "piper", "xtts"]
        for engine in expected_engines:
            assert engine in report.audio_engines
    
    def test_system_deps_checked(self):
        """Critical system deps should be checked."""
        report = check_all_prerequisites()
        
        assert "ffmpeg" in report.system_deps
        assert "espeak-ng" in report.system_deps
