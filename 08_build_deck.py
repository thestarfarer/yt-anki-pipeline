#!/usr/bin/env python3
"""Build Anki deck from verified/cleaned transcriptions"""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "lib"))
from config import TARGET_LANGUAGE
from common import get_stream_dir, load_drops, load_stream_meta

import genanki

MODEL_ID = 1607392319
DECK_ID = 2059400110

def main():
    stream_dir = get_stream_dir()
    os.chdir(stream_dir)
    
    meta = load_stream_meta(stream_dir)
    stream_id = meta.get("id", os.path.basename(stream_dir))
    deck_name = meta.get("title", stream_id)
    
    drops = load_drops(stream_dir)
    print(f"Loaded {len(drops)} drop IDs from drops.txt")
    
    # Find best input - prefer verified data
    if os.path.exists("verification_results.json"):
        with open("verification_results.json") as f:
            verified = json.load(f)
        print(f"Using verification results ({len(verified)} clips)")
        
        # Load base transcriptions for fallback
        if os.path.exists("transcriptions_cleaned.json"):
            with open("transcriptions_cleaned.json") as f:
                data = json.load(f)
            trans = data if isinstance(data, list) else data["transcriptions"]
        else:
            with open("transcriptions.json") as f:
                data = json.load(f)
            trans = data if isinstance(data, list) else data["transcriptions"]
        trans_map = {t["clip_id"]: t for t in trans}
        
        # Build cards ONLY from verified clips
        cards_source = []
        for v in verified:
            cid = v["clip_id"]
            if cid in drops:
                continue
            orig_t = trans_map.get(cid, {})
            original = v["corrected_original"] if v["corrected_original"] else orig_t.get("original", "")
            english = v["corrected_english"] if v["corrected_english"] else orig_t.get("english", "")
            if original and english:
                cards_source.append({"clip_id": cid, "original": original, "english": english})
    else:
        # No verification - use raw transcriptions
        if os.path.exists("transcriptions_cleaned.json"):
            input_file = "transcriptions_cleaned.json"
        else:
            input_file = "transcriptions.json"
        
        with open(input_file) as f:
            data = json.load(f)
        trans = data if isinstance(data, list) else data["transcriptions"]
        print(f"No verification results, using {input_file} ({len(trans)} clips)")
        
        cards_source = []
        for t in trans:
            if t["clip_id"] not in drops:
                cards_source.append({
                    "clip_id": t["clip_id"],
                    "original": t["original"],
                    "english": t["english"]
                })
    
    model = genanki.Model(
        MODEL_ID,
        f'{TARGET_LANGUAGE} Listening',
        fields=[
            {'name': 'Audio'},
            {'name': 'Original'},
            {'name': 'English'},
        ],
        templates=[
            {
                'name': 'Listen → Translate',
                'qfmt': '{{Audio}}<br><br><i>What did they say?</i>',
                'afmt': '{{FrontSide}}<hr id="answer"><b>{{Original}}</b><br><br>{{English}}',
            },
        ],
        css='''
        .card {
            font-family: arial;
            font-size: 20px;
            text-align: center;
            color: black;
            background-color: white;
        }
        '''
    )
    
    deck = genanki.Deck(DECK_ID, deck_name)
    media_files = []
    
    for card in cards_source:
        cid = card["clip_id"]
        audio_file = f"clip_{cid:04d}.m4a"
        audio_path = os.path.join("clips", audio_file)
        
        if os.path.exists(audio_path):
            media_files.append(audio_path)
            note = genanki.Note(
                model=model,
                fields=[f"[sound:{audio_file}]", card["original"], card["english"]]
            )
            deck.add_note(note)
    
    output_file = f"{stream_id}.apkg"
    package = genanki.Package(deck)
    package.media_files = media_files
    package.write_to_file(output_file)
    
    print(f"\nCreated: {output_file}")
    print(f"Cards: {len(deck.notes)}")
    print(f"Dropped: {len(drops)}")
    print(f"Media files: {len(media_files)}")

if __name__ == "__main__":
    main()
