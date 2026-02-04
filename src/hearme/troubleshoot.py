"""
hear-me Troubleshooting Tool

Self-diagnosis utility to verify system health and engine status.
"""

import platform
import sys
import shutil
import logging
from dataclasses import dataclass
from typing import List, Dict, Any

from hearme.engines.registry import EngineRegistry, get_engine
from hearme.prerequisites import check_all_prerequisites

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    check: str
    status: str  # "PASS", "FAIL", "WARN"
    message: str
    details: Dict[str, Any] | None = None


def check_python_environment() -> DiagnosticResult:
    """Check Python environment."""
    version = sys.version_info
    valid = version >= (3, 10)
    
    return DiagnosticResult(
        check="python_version",
        status="PASS" if valid else "FAIL",
        message=f"Python {version.major}.{version.minor}.{version.micro}",
        details={
            "executable": sys.executable,
            "platform": platform.platform(),
            "architecture": platform.machine()
        }
    )


def check_dependencies() -> DiagnosticResult:
    """Check external dependencies."""
    ffmpeg = shutil.which("ffmpeg")
    
    return DiagnosticResult(
        check="dependencies",
        status="PASS" if ffmpeg else "WARN",
        message="ffmpeg found" if ffmpeg else "ffmpeg not found (audio processing may fail)",
        details={"ffmpeg_path": ffmpeg}
    )


def verify_engines() -> List[DiagnosticResult]:
    """Verify all registered engines."""
    results = []
    
    # Try loading critical engines
    engines_to_check = ["kokoro", "dia2", "piper"]
    
    for name in engines_to_check:
        engine = get_engine(name)
        
        if not engine:
            results.append(DiagnosticResult(
                check=f"engine_{name}",
                status="WARN",
                message=f"Engine '{name}' not installed/registered",
            ))
            continue
            
        try:
            available = engine.is_available()
            if available:
                # Basic load test
                status = "PASS"
                msg = f"Engine '{name}' available"
                
                # Check hardware acceleration if applicable
                if name == "dia2":
                    try:
                        import torch
                        if torch.backends.mps.is_available():
                            msg += " (MPS accelerated)"
                        elif torch.cuda.is_available():
                            msg += " (CUDA accelerated)"
                        else:
                            msg += " (CPU only)"
                    except Exception:
                        msg += " (acceleration unknown; torch not in hear-me venv)"
            else:
                status = "WARN"
                msg = f"Engine '{name}' installed but not available (missing deps?)"
                
            results.append(DiagnosticResult(
                check=f"engine_{name}",
                status=status,
                message=msg,
                details=engine.capabilities.model_dump()
            ))
            
        except Exception as e:
            results.append(DiagnosticResult(
                check=f"engine_{name}",
                status="FAIL",
                message=f"Engine check failed: {str(e)}",
            ))
            
    return results


def run_diagnostics() -> Dict[str, Any]:
    """Run full suite of diagnostics."""
    diagnostics = []
    
    # System checks
    diagnostics.append(check_python_environment())
    diagnostics.append(check_dependencies())
    
    # Engine checks
    diagnostics.extend(verify_engines())
    
    # Summary
    passed = len([d for d in diagnostics if d.status == "PASS"])
    warnings = len([d for d in diagnostics if d.status == "WARN"])
    failures = len([d for d in diagnostics if d.status == "FAIL"])
    
    return {
        "summary": {
            "total": len(diagnostics),
            "passed": passed,
            "warnings": warnings,
            "failures": failures,
            "healthy": failures == 0
        },
        "details": [
            {
                "check": d.check,
                "status": d.status,
                "message": d.message,
                "details": d.details
            }
            for d in diagnostics
        ]
    }


if __name__ == "__main__":
    import json
    results = run_diagnostics()
    print(json.dumps(results, indent=2))
    
    # Exit with error if any checks failed
    if not results["summary"]["healthy"]:
        # Allow warnings but fail on failures
        if results["summary"]["failures"] > 0:
            sys.exit(1)
    sys.exit(0)
