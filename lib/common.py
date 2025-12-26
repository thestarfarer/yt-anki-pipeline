"""Shared utilities for anki pipeline"""

import os
import sys
import json

def get_stream_dir():
    """Get stream directory from --stream arg or cwd"""
    # Check for --stream argument
    for i, arg in enumerate(sys.argv):
        if arg == "--stream" and i + 1 < len(sys.argv):
            from lib.config import get_stream_dir as gsd
            return gsd(sys.argv[i + 1])
    
    # Otherwise use cwd if it looks like a stream dir
    cwd = os.getcwd()
    if os.path.exists(os.path.join(cwd, "stream.json")):
        return cwd
    
    # Check parent
    parent = os.path.dirname(cwd)
    if os.path.exists(os.path.join(parent, "stream.json")):
        return parent
    
    print("Error: Run from stream directory or use --stream <id>", file=sys.stderr)
    sys.exit(1)

def load_stream_meta(stream_dir):
    """Load stream.json metadata"""
    path = os.path.join(stream_dir, "stream.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def load_drops(stream_dir):
    """Load drop IDs from drops.txt"""
    path = os.path.join(stream_dir, "drops.txt")
    drops = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                line = line.split("#")[0].strip()  # Remove comments
                if line.isdigit():
                    drops.add(int(line))
    return drops

def to_mmss(secs):
    """Convert seconds to MM:SS with proper rounding"""
    total = round(secs)
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"
