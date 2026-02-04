#!/usr/bin/env python3
"""
Model Download Utility for hear-me

Pre-downloads model weights during installation to prevent runtime timeouts.
"""
import argparse
import sys
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS = {
    "dia2": {
        "repo_id": "nari-labs/Dia2-2B",
        "filenames": [
            "config.json", 
            "model.safetensors", 
            "dia2_assets.json",
            "tokenizer.json",         # Likely present or needed if tokenizer loading logic changes
            "tokenizer_config.json"
        ]
    },
    "kokoro": {
        "repo_id": "hexgrad/Kokoro-82M",
        "filenames": ["kokoro-v0_19.onnx", "voices.json"]
    },
    "piper": {
        "voice": "en_US-amy-medium"
    }
}

def download_dia2():
    print("⏳ Checking Dia2 model cache (nari-labs/Dia2-2B)...")
    try:
        from huggingface_hub import snapshot_download
        snapshot_download(
            repo_id=MODELS["dia2"]["repo_id"],
            allow_patterns=["*.json", "*.safetensors", "*.model"],
            resume_download=True
        )
        print("✅ Dia2 model ready.")
        return True
    except ImportError:
        print("❌ huggingface_hub not installed. Run: pip install huggingface_hub")
        return False
    except Exception as e:
        print(f"❌ Failed to download Dia2: {e}")
        return False

def download_kokoro():
    print("⏳ Checking Kokoro model cache...")
    try:
        import kokoro
        print("   Triggering Kokoro model download (if missing)...")
        # Initialize KModel to trigger download of kokoro-v0_19.onnx and voices.json
        kokoro.KModel() 
        print("✅ Kokoro model ready.")
        return True
    except ImportError:
        print("❌ kokoro package not installed.")
        return False
    except Exception as e:
        print(f"❌ Failed to download Kokoro: {e}")
        return False

def download_piper():
    print("⏳ Checking Piper voice cache (en_US-amy-medium)...")
    try:
        from piper import PiperVoice
        # Piper python wrapper usually expects a path or downloads if configured.
        # However, standard pip 'piper-tts' might not have auto-download for 'load("name")' 
        # depending on the version. hear-me's engine assumes it does.
        # We will attempt to load it.
        try:
            # We assume the user's piper integration handles 'load' by name
            # If not, this might fail, but it's worth a try if the engine code does it.
            # Looking at engine code: PiperVoice.load("en_US-amy-medium")
            # If this is the 'piper-tts' pypi package, it might need 'piper-phonemize' etc.
            print("   Triggering Piper voice download...")
            PiperVoice.load("en_US-amy-medium")
            print("✅ Piper voice ready.")
            return True
        except Exception as e:
             # Some piper versions don't download automatically.
             print(f"⚠️  Piper auto-download might not be supported or failed: {e}")
             print("   Skipping pre-download. It will be attempted at runtime.")
             return True # nondestructive failure
             
    except ImportError:
        print("❌ piper-tts package not installed.")
        return False

def main():
    parser = argparse.ArgumentParser(description="Download hear-me models")
    parser.add_argument("--engine", required=True, choices=["dia2", "kokoro", "piper"], help="Engine to download models for")
    args = parser.parse_args()

    success = True
    if args.engine == "dia2":
        success = download_dia2()
    elif args.engine == "kokoro":
        success = download_kokoro()
    elif args.engine == "piper":
        success = download_piper()
    
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
