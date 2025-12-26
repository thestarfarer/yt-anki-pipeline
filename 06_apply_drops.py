#!/usr/bin/env python3
"""Add clip IDs to drops.txt"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from common import get_stream_dir

def main():
    if len(sys.argv) < 2:
        print("Usage: 06_apply_drops.py <clip_id> [clip_id ...]")
        print("       06_apply_drops.py --comment 'reason' <clip_id> [clip_id ...]")
        sys.exit(1)
    
    stream_dir = get_stream_dir()
    drops_file = os.path.join(stream_dir, "drops.txt")
    
    args = sys.argv[1:]
    comment = None
    
    # Check for --comment flag
    if args[0] == "--comment" and len(args) > 2:
        comment = args[1]
        args = args[2:]
    
    # Parse IDs
    ids = []
    for arg in args:
        if arg.isdigit():
            ids.append(int(arg))
        else:
            print(f"Skipping invalid ID: {arg}")
    
    if not ids:
        print("No valid IDs provided")
        sys.exit(1)
    
    # Append to drops.txt
    with open(drops_file, "a") as f:
        if comment:
            f.write(f"\n# {comment}\n")
        for cid in ids:
            f.write(f"{cid}\n")
    
    print(f"Added {len(ids)} IDs to drops.txt")

if __name__ == "__main__":
    main()
