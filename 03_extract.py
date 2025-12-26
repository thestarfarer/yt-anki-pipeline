#!/usr/bin/env python3
"""Extract batch audio and individual clips from segments"""

import json
import os
import sys
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from config import BATCH_SIZE, EDGE_PADDING
from common import get_stream_dir

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    if not os.path.exists("segments.json"):
        print("Error: segments.json not found. Run 02_vad.py first.")
        sys.exit(1)
    
    with open("segments.json") as f:
        segments = json.load(f)["segments"]
    
    print(f"Segments: {len(segments)}")
    print(f"Batch size: {BATCH_SIZE}")
    
    # Create batch audio for transcription
    os.makedirs("batch_audio", exist_ok=True)
    num_batches = (len(segments) + BATCH_SIZE - 1) // BATCH_SIZE
    
    print(f"\nExtracting {num_batches} batch audio files...")
    for batch_idx in range(num_batches):
        batch_segs = segments[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        
        audio_start = max(0, batch_segs[0]["start"] - EDGE_PADDING)
        audio_end = batch_segs[-1]["end"] + EDGE_PADDING
        duration = audio_end - audio_start
        
        output = f"batch_audio/batch_{batch_idx:02d}.m4a"
        cmd = [
            "ffmpeg", "-y", "-ss", str(audio_start), "-i", "stream.m4a",
            "-t", str(duration), "-c:a", "aac", "-b:a", "128k", output
        ]
        subprocess.run(cmd, capture_output=True)
        print(f"  [{batch_idx+1}/{num_batches}] {output}")
    
    # Create individual clips
    os.makedirs("clips", exist_ok=True)
    print(f"\nExtracting {len(segments)} individual clips...")
    
    for i, seg in enumerate(segments):
        output = f"clips/clip_{i:04d}.m4a"
        cmd = [
            "ffmpeg", "-y", "-ss", str(seg["start"]), "-i", "stream.m4a",
            "-t", str(seg["duration"]), "-c:a", "aac", "-b:a", "128k", output
        ]
        subprocess.run(cmd, capture_output=True)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(segments)}")
    
    print(f"\nDone.")
    print(f"Batch audio: batch_audio/ ({num_batches} files)")
    print(f"Clips: clips/ ({len(segments)} files)")
    print(f"\nNext: ../../04_transcribe.py")

if __name__ == "__main__":
    main()
