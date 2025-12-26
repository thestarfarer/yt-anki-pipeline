#!/usr/bin/env python3
"""Batch transcription with Gemini"""

import json
import os
import sys
import time
import glob

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from config import GEMINI_MODEL, BATCH_SIZE, EDGE_PADDING, MAX_RETRIES, TARGET_LANGUAGE, get_api_key
from common import get_stream_dir, to_mmss

from google import genai
from google.genai import types
import typing_extensions as typing

sys.stdout.reconfigure(line_buffering=True)

class ClipTranscription(typing.TypedDict):
    start: str
    end: str
    original: str
    english: str

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    if not os.path.exists("segments.json"):
        print("Error: segments.json not found")
        sys.exit(1)
    
    with open("segments.json") as f:
        segments = json.load(f)["segments"]
    
    batch_files = sorted(glob.glob("batch_audio/batch_*.m4a"))
    if not batch_files:
        print("Error: No batch audio files. Run 03_extract.py first.")
        sys.exit(1)
    
    print(f"Segments: {len(segments)}")
    print(f"Batches: {len(batch_files)}")
    
    client = genai.Client(api_key=get_api_key())
    
    # Resume support
    output_file = "transcriptions.json"
    if os.path.exists(output_file):
        with open(output_file) as f:
            existing = json.load(f)
        all_transcriptions = existing.get("transcriptions", [])
        done_batches = set(t.get("batch_idx") for t in all_transcriptions if "batch_idx" in t)
        print(f"Resuming: {len(done_batches)} batches done")
    else:
        all_transcriptions = []
        done_batches = set()
    
    for batch_idx, batch_file in enumerate(batch_files):
        if batch_idx in done_batches:
            continue
        
        batch_segs = segments[batch_idx * BATCH_SIZE : (batch_idx + 1) * BATCH_SIZE]
        if not batch_segs:
            continue
        
        # Calculate relative timestamps
        audio_start = max(0, batch_segs[0]["start"] - EDGE_PADDING)
        rel_timestamps = []
        for seg in batch_segs:
            rel_start = seg["start"] - audio_start
            rel_end = seg["end"] - audio_start
            rel_timestamps.append(f"{to_mmss(rel_start)}-{to_mmss(rel_end)}")
        
        prompt = f"""You are transcribing {TARGET_LANGUAGE} audio clips.

The audio contains multiple speech segments at these timestamps:
{chr(10).join(rel_timestamps)}

For each segment, provide:
- start: timestamp MM:SS from the start of this audio
- end: timestamp MM:SS from the start of this audio
- original: exact transcription in {TARGET_LANGUAGE} (include any English/Japanese words as spoken)
- english: natural English translation

Return exactly {len(batch_segs)} transcriptions in chronological order.
"""
        
        for attempt in range(MAX_RETRIES):
            try:
                audio_file = client.files.upload(file=batch_file)
                
                result = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[types.Content(parts=[
                        types.Part.from_uri(file_uri=audio_file.uri, mime_type="audio/mp4"),
                        types.Part.from_text(text=prompt),
                    ])],
                    config={"response_mime_type": "application/json", "response_schema": list[ClipTranscription]},
                )
                
                batch_results = json.loads(result.text)
                
                # Add metadata
                for i, (tr, seg) in enumerate(zip(batch_results, batch_segs)):
                    clip_id = batch_idx * BATCH_SIZE + i
                    tr["clip_id"] = clip_id
                    tr["batch_idx"] = batch_idx
                    tr["absolute_start"] = seg["start"]
                    tr["absolute_end"] = seg["end"]
                
                all_transcriptions.extend(batch_results)
                
                try:
                    client.files.delete(name=audio_file.name)
                except:
                    pass
                
                print(f"[{batch_idx+1}/{len(batch_files)}] ✓ {len(batch_results)} clips")
                break
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    print(f"\n[{batch_idx+1}/{len(batch_files)}] Rate limited. Saving progress...")
                    with open(output_file, "w") as f:
                        json.dump({"transcriptions": all_transcriptions}, f, indent=2, ensure_ascii=False)
                    print(f"Saved {len(all_transcriptions)} transcriptions. Resume later.")
                    sys.exit(1)
                
                if attempt < MAX_RETRIES - 1:
                    print(f"[{batch_idx+1}/{len(batch_files)}] Retry {attempt+1}...")
                    time.sleep(2 ** attempt)
                else:
                    print(f"[{batch_idx+1}/{len(batch_files)}] ✗ Failed: {error_str[:60]}")
        
        # Incremental save
        with open(output_file, "w") as f:
            json.dump({"transcriptions": all_transcriptions}, f, indent=2, ensure_ascii=False)
    
    print(f"\nDone. Total: {len(all_transcriptions)} transcriptions")
    print(f"Output: {output_file}")
    print(f"\nNext: ../../05_clean.py")

if __name__ == "__main__":
    main()
