#!/usr/bin/env python3
"""Pass 1: Auto-clean transcriptions (drop pure English)"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from common import get_stream_dir

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    with open("transcriptions.json") as f:
        data = json.load(f)
    
    transcriptions = data if isinstance(data, list) else data["transcriptions"]
    print(f"Input: {len(transcriptions)} clips")
    
    kept = []
    dropped_english = 0
    
    for t in transcriptions:
        orig = t["original"].strip().lower()
        eng = t["english"].strip().lower()
        
        if orig == eng:
            # Pure English - drop it
            dropped_english += 1
        else:
            kept.append(t)
    
    output = {"transcriptions": kept}
    with open("transcriptions_cleaned.json", "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Dropped: {dropped_english} pure English")
    print(f"Kept: {len(kept)}")
    print(f"Output: transcriptions_cleaned.json")
    print(f"\nNext: Review output, add bad clip IDs to drops.txt")
    print(f"Then: ../../07_verify.py (optional) or ../../08_build_deck.py")

if __name__ == "__main__":
    main()
