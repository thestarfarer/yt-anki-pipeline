"""Shared configuration for anki pipeline"""

import os

# Language
TARGET_LANGUAGE = os.environ.get("TARGET_LANGUAGE", "Indonesian")

# API
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.0-flash")

def get_api_key():
    """Get API key from env or file"""
    if "GEMINI_API_KEY" in os.environ:
        return os.environ["GEMINI_API_KEY"]
    
    key_path = os.environ.get("GEMINI_KEY_PATH", os.path.expanduser("~/.gemini_key"))
    if os.path.exists(key_path):
        return open(key_path).read().strip()
    
    raise ValueError("Set GEMINI_API_KEY env var or create ~/.gemini_key")

# VAD parameters (Silero 6.2.0)
VAD_PARAMS = {
    "min_silence_duration_ms": 300,
    "speech_pad_ms": 50,
    "min_speech_duration_ms": 800,
    "post_pad_s": 0.25,  # Added to start/end of each segment
}

# Transcription
BATCH_SIZE = 20
EDGE_PADDING = 0.5

# Verification
RPM_LIMIT = 20
WORKERS = 10
MAX_RETRIES = 3

# Paths - auto-detect from script location
def _get_pipeline_root():
    """Find pipeline root from this file's location"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PIPELINE_ROOT = os.environ.get("PIPELINE_ROOT", _get_pipeline_root())
STREAMS_DIR = os.path.join(PIPELINE_ROOT, "streams")

def get_stream_dir(stream_id):
    return os.path.join(STREAMS_DIR, stream_id)
