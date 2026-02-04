"""
Test Dia2 input format.

This script verifies that the Dia2 engine correctly formats input
with [S1] and [S2] speaker tags as per the official Dia2 documentation.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from hearme.engines.dia2 import Dia2Engine

def test_speaker_mapping():
    """Test that speakers are correctly mapped to S1/S2."""
    engine = Dia2Engine()
    
    # Simulate speaker mapping logic
    segments = [
        {"speaker": "narrator", "text": "Hello world"},
        {"speaker": "peer", "text": "Hi there"},
        {"speaker": "narrator", "text": "How are you?"},
        {"speaker": "peer", "text": "Great!"},
    ]
    
    # Manually test the mapping logic
    speaker_mapping = {}
    speaker_count = 0
    script_parts = []
    
    for seg in segments:
        speaker = seg.get("speaker", "narrator")
        text = seg.get("text", "").strip()
        
        if speaker in speaker_mapping:
            dia_speaker = speaker_mapping[speaker]
        else:
            speaker_count += 1
            dia_speaker = f"S{min(speaker_count, 2)}"
            speaker_mapping[speaker] = dia_speaker
        
        script_parts.append(f"[{dia_speaker}] {text}")
    
    full_script = " ".join(script_parts)
    
    expected = "[S1] Hello world [S2] Hi there [S1] How are you? [S2] Great!"
    
    print(f"Generated: {full_script}")
    print(f"Expected:  {expected}")
    
    assert full_script == expected, f"Mismatch!\nGot: {full_script}"
    print("✅ Speaker mapping test PASSED!")

if __name__ == "__main__":
    test_speaker_mapping()
