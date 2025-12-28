# YouTube → Anki Pipeline

Turn hours of YouTube into bite-sized listening comprehension cards.

Built this to learn Indonesian from VTuber streams. VAD finds the speech, Gemini transcribes it, you get an Anki deck with audio clips and transcriptions. Works for any language Gemini supports.

## The Pipeline

```
YouTube video
    ↓
01_download.sh      # Fetch video, extract audio
    ↓
02_vad.py           # Voice activity detection (Silero) → find speech segments
    ↓
03_extract.py       # Cut individual clips
    ↓
04_transcribe.py    # Batch transcription (Gemini)
    ↓
05_clean.py         # Auto-drop pure English / garbage
    ↓
06_apply_drops.py   # Manual review drops
    ↓
07_verify.py        # Re-check transcriptions (catches Gemini hallucinations)
    ↓
08_build_deck.py    # Build .apkg
    ↓
Anki deck with audio + transcriptions
```

## Quick Start

```bash
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"

# Download
./01_download.sh my-video-2025-01 "https://youtube.com/watch?v=..."

# Process
cd streams/my-video-2025-01
../../02_vad.py
../../03_extract.py
../../04_transcribe.py
../../05_clean.py
../../07_verify.py
../../08_build_deck.py
```

For members-only content, set `YT_COOKIES` to your cookies file path.

## Requirements

- Python 3.10+
- ffmpeg
- yt-dlp
- Gemini API key

## Configuration

Environment variables:
- `GEMINI_API_KEY` — Required
- `GEMINI_MODEL` — Model to use (default: gemini-2.0-flash)
- `TARGET_LANGUAGE` — Language to transcribe (default: Indonesian)
- `YT_COOKIES` — Path to cookies file for members-only content

Or edit `lib/config.py` for VAD params, batch sizes, rate limits.

## Manual Review

After transcription, review and mark bad clips:

```bash
# View transcriptions
python3 -c "import json; [print(f\"{t['clip_id']:04d}|{t['original']}|{t['english']}\") for t in json.load(open('transcriptions_cleaned.json'))['transcriptions']]"

# Drop specific clips
../../06_apply_drops.py --comment "garbage" 123 456 789
```

### drops.txt Format

```
# Comments with #
# One clip ID per line

# Pure English
43
45

# Noise/fragments  
17
```

## Verification

**This step matters.** Gemini is good at transcribing long audio, but not great with timestamps. When VAD cuts mid-sentence, Gemini often transcribes the *full* sentence anyway—even the parts that aren't in the clip. These phantom fragments can be up to 50% of your output.

The verification pass re-checks each clip individually and catches these hallucinations:

```bash
../../07_verify.py
# Or loop until done:
# while true; do ../../07_verify.py; sleep 180; done
```

Rate-limited and resumable.

## Other Languages

```bash
export TARGET_LANGUAGE="Japanese"
```

The pipeline uses this in prompts and deck metadata.

**Tuning tips:**

- `05_clean.py` drops clips where `original == english` (pure English). May need adjustment for Latin-script languages.
- VAD params in `lib/config.py`: lower `min_silence_duration_ms` for faster speech, adjust `speech_pad_ms` for tonal languages.

**Tested:**
- Indonesian ✓
- Japanese (should work)
- Korean (should work)

## Structure

```
├── 01_download.sh      # Fetch video, extract audio
├── 02_vad.py           # Voice activity detection (Silero)
├── 03_extract.py       # Cut batch audio + individual clips
├── 04_transcribe.py    # Batch transcription (Gemini)
├── 05_clean.py         # Auto-drop pure English clips
├── 06_apply_drops.py   # Manual drops
├── 07_verify.py        # Re-check transcriptions (critical)
├── 08_build_deck.py    # Build .apkg
├── lib/
│   ├── config.py       # Settings
│   └── common.py       # Utilities
├── streams/            # Per-video data
└── docs/
    └── REFERENCE.md    # Detailed docs
```

## License

MIT
