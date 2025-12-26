#!/usr/bin/env python3
"""Parallel verification with rate limiting, incremental saves, resume"""

import json
import time
import sys
import os

# Add lib to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from config import GEMINI_MODEL, RPM_LIMIT, WORKERS, MAX_RETRIES, TARGET_LANGUAGE, get_api_key
from common import get_stream_dir

from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock, Event
from google import genai
from google.genai import types
import typing_extensions as typing

sys.stdout.reconfigure(line_buffering=True)

class Verification(typing.TypedDict):
    original: bool
    english: bool
    corrected_original: str
    corrected_english: str
    notes: str

class RateLimiter:
    def __init__(self, rpm):
        self.interval = 60.0 / rpm
        self.lock = Lock()
        self.last_request = 0
    
    def acquire(self):
        with self.lock:
            now = time.time()
            wait = self.last_request + self.interval - now
            if wait > 0:
                time.sleep(wait)
            self.last_request = time.time()

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    client = genai.Client(api_key=get_api_key())
    results_lock = Lock()
    abort_event = Event()
    rate_limiter = RateLimiter(RPM_LIMIT)
    all_results = {}
    
    # Find input file
    if os.path.exists("transcriptions_cleaned.json"):
        input_file = "transcriptions_cleaned.json"
    else:
        input_file = "transcriptions.json"
    
    output_file = "verification_results.json"
    
    def save_results():
        with results_lock:
            sorted_results = [all_results[cid] for cid in sorted(all_results.keys())]
            with open(output_file, "w") as f:
                json.dump(sorted_results, f, indent=2, ensure_ascii=False)
    
    def verify_clip(t):
        clip_id = t["clip_id"]
        clip_file = f"clips/clip_{clip_id:04d}.m4a"
        
        if abort_event.is_set():
            return clip_id, None, "aborted"
        
        for attempt in range(MAX_RETRIES):
            try:
                rate_limiter.acquire()
                
                if abort_event.is_set():
                    return clip_id, None, "aborted"
                
                audio_file = client.files.upload(file=clip_file)
                
                prompt = f"""Listen to this {TARGET_LANGUAGE} audio clip.

Previous transcription:
Original: {t["original"]}
English: {t["english"]}

Verify the transcription accuracy:
- original: true if transcription matches audio, false if not
- english: true if translation is accurate, false if not  
- corrected_original: provide correction if original is false, empty string if true
- corrected_english: provide correction if english is false, empty string if true
- notes: any observations (speaker unclear, background noise, etc)

Include any English/Japanese words exactly as spoken."""

                result = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=[types.Content(parts=[
                        types.Part.from_uri(file_uri=audio_file.uri, mime_type="audio/mp4"),
                        types.Part.from_text(text=prompt),
                    ])],
                    config={"response_mime_type": "application/json", "response_schema": Verification},
                )
                
                v = json.loads(result.text)
                v["clip_id"] = clip_id
                
                try:
                    client.files.delete(name=audio_file.name)
                except:
                    pass
                
                return clip_id, v, None
                
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                    abort_event.set()
                    return clip_id, None, "rate_limit"
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)
                else:
                    return clip_id, None, error_str
        
        return clip_id, None, "Max retries exceeded"
    
    # Load transcriptions
    with open(input_file) as f:
        data = json.load(f)
    transcriptions = data if isinstance(data, list) else data["transcriptions"]
    expected_ids = set(t["clip_id"] for t in transcriptions)
    print(f"Input: {input_file} ({len(transcriptions)} clips)", flush=True)
    
    # Resume from existing
    if os.path.exists(output_file):
        with open(output_file) as f:
            existing = json.load(f)
        all_results = {r["clip_id"]: r for r in existing if "error" not in r}
        print(f"Resuming: {len(all_results)} already verified", flush=True)
    
    done_ids = set(all_results.keys())
    todo = [t for t in transcriptions if t["clip_id"] not in done_ids]
    
    if not todo:
        print("All clips already verified!", flush=True)
        return
    
    print(f"Verifying {len(todo)} remaining clips ({WORKERS} workers, {RPM_LIMIT} RPM)...\n", flush=True)
    
    start_time = time.time()
    verified_this_run = 0
    errors_this_run = 0
    rate_limited = False
    
    with ThreadPoolExecutor(max_workers=WORKERS) as executor:
        futures = {executor.submit(verify_clip, t): t["clip_id"] for t in todo}
        
        for future in as_completed(futures):
            clip_id, v, error = future.result()
            
            if error == "rate_limit":
                print(f"\n[{clip_id:04d}] RATE LIMITED - aborting", flush=True)
                rate_limited = True
                for f in futures:
                    f.cancel()
                break
            elif error == "aborted":
                continue
            elif error:
                print(f"[{clip_id:04d}] ERROR: {error[:80]}", flush=True)
                errors_this_run += 1
            else:
                with results_lock:
                    all_results[clip_id] = v
                
                save_results()
                verified_this_run += 1
                
                status = "✓" if v["original"] and v["english"] else "✗"
                line = f"[{clip_id:04d}] {status}"
                if v["corrected_original"]:
                    line += f" → {v['corrected_original'][:40]}..."
                print(line, flush=True)
    
    elapsed = time.time() - start_time
    total_done = len(all_results)
    remaining = len(expected_ids) - total_done
    corrections = len([r for r in all_results.values() if not (r["original"] and r["english"])])
    
    print(f"\n=== Run complete in {elapsed:.1f}s ===", flush=True)
    if rate_limited:
        print("Aborted: quota exhausted", flush=True)
    print(f"Verified this run: {verified_this_run}", flush=True)
    print(f"Errors this run: {errors_this_run}", flush=True)
    print(f"Total verified: {total_done}/{len(expected_ids)}", flush=True)
    print(f"Remaining: {remaining}", flush=True)
    print(f"Corrections flagged: {corrections}", flush=True)
    
    if remaining > 0:
        print(f"\nRun again when quota resets.", flush=True)
        sys.exit(1)
    else:
        print(f"\nNext: ../../08_build_deck.py", flush=True)

if __name__ == "__main__":
    main()
