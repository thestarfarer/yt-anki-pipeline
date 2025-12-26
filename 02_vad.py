#!/usr/bin/env python3
"""VAD processing with Silero"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from config import VAD_PARAMS
from common import get_stream_dir

import torch
torch.set_num_threads(1)

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    if not os.path.exists("stream.m4a"):
        print("Error: stream.m4a not found")
        sys.exit(1)
    
    print("Loading Silero VAD...")
    model, utils = torch.hub.load(
        repo_or_dir='snakers4/silero-vad',
        model='silero_vad',
        force_reload=False
    )
    get_speech_timestamps, read_audio, _, _, _ = utils
    
    print("Reading audio...")
    wav = read_audio("stream.m4a", sampling_rate=16000)
    
    print("Running VAD...")
    speech_timestamps = get_speech_timestamps(
        wav,
        model,
        sampling_rate=16000,
        min_silence_duration_ms=VAD_PARAMS["min_silence_duration_ms"],
        speech_pad_ms=VAD_PARAMS["speech_pad_ms"],
        min_speech_duration_ms=VAD_PARAMS["min_speech_duration_ms"],
    )
    
    # Convert to seconds and add padding
    pad = VAD_PARAMS["post_pad_s"]
    segments = []
    for i, ts in enumerate(speech_timestamps):
        start = max(0, ts['start'] / 16000 - pad)
        end = ts['end'] / 16000 + pad
        segments.append({
            "segment_id": i,
            "start": round(start, 3),
            "end": round(end, 3),
            "duration": round(end - start, 3)
        })
    
    with open("segments.json", "w") as f:
        json.dump({"segments": segments}, f, indent=2)
    
    total_duration = sum(s["duration"] for s in segments)
    print(f"\nSegments: {len(segments)}")
    print(f"Total speech: {total_duration/60:.1f} min")
    print(f"Output: segments.json")
    print(f"\nNext: ../../03_extract.py")

if __name__ == "__main__":
    main()
