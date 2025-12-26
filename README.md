# anki-pipeline

Build listening comprehension Anki decks from YouTube videos.

VAD → batch transcribe → verify → Anki deck.

## What It Does

1. Downloads video, extracts audio
2. Runs voice activity detection to find speech segments
3. Batch-transcribes segments via Gemini API
4. Optionally verifies transcriptions
5. Builds an Anki deck with audio clips + transcriptions

Originally built for Indonesian VTuber streams, but works for any language Gemini supports.

## Requirements

- Python 3.10+
- ffmpeg
- yt-dlp
- Gemini API key

```bash
pip install -r requirements.txt
```

## Quick Start

```bash
# Set API key
export GEMINI_API_KEY="your-key-here"

# Download (for members-only content, add cookies path)
./01_download.sh my-video-2025-01 "https://youtube.com/watch?v=..."

# Process
cd streams/my-video-2025-01
../../02_vad.py        # Voice activity detection
../../03_extract.py    # Cut clips
../../04_transcribe.py # Transcribe
../../05_clean.py      # Auto-clean
../../08_build_deck.py # Build deck
```

## Structure

```
anki-pipeline/
├── 01_download.sh      # Fetch video, extract audio
├── 02_vad.py           # Voice activity detection (Silero)
├── 03_extract.py       # Cut batch audio + individual clips
├── 04_transcribe.py    # Batch transcription (Gemini)
├── 05_clean.py         # Auto-drop pure English clips
├── 06_apply_drops.py   # Manual drops
├── 07_verify.py        # Verify transcriptions (optional)
├── 08_build_deck.py    # Build .apkg
├── lib/
│   ├── config.py       # Settings
│   └── common.py       # Utilities
├── streams/            # Per-video data
└── docs/
    └── REFERENCE.md    # Detailed docs
```

## Configuration

Environment variables:
- `GEMINI_API_KEY` - Required
- `GEMINI_MODEL` - Model to use (default: gemini-2.0-flash)
- `TARGET_LANGUAGE` - Language to transcribe (default: Indonesian)
- `YT_COOKIES` - Path to cookies file for members-only content

Or edit `lib/config.py` for VAD params, batch sizes, rate limits.

## Manual Review

After transcription, review and mark bad clips:

```bash
# View transcriptions
python3 -c "import json; [print(f\"{t['clip_id']:04d}|{t['original']}|{t['english']}\") for t in json.load(open('transcriptions_cleaned.json'))['transcriptions']]"

# Drop specific clips
../../06_apply_drops.py --comment "garbage" 123 456 789
```

## Verification (Optional)

For higher quality, run verification pass:

```bash
../../07_verify.py
# Or loop until done:
# while true; do ../../07_verify.py; sleep 180; done
```

This sends each clip to Gemini for correction. Rate-limited and resumable.

## drops.txt Format

```
# Comments with #
# One clip ID per line

# Pure English
43
45

# Noise/fragments  
17
```

## Adapting for Other Languages

Set `TARGET_LANGUAGE` env var or edit `lib/config.py`:

```bash
export TARGET_LANGUAGE="Japanese"
```

The pipeline will automatically use this in prompts and deck metadata.

### Additional Tuning

**Cleaning Rules (`05_clean.py`):**
- The default drops clips where `original == english` (pure English)
- May need adjustment for Latin-script languages
- Add exceptions for catchphrases you want to keep

**VAD Parameters (`lib/config.py`):**
- `min_silence_duration_ms`: Lower for faster speech
- `min_speech_duration_ms`: Adjust for typical utterance length
- `speech_pad_ms`: May need more padding for tonal languages

### Languages Tested

- Indonesian ✓
- Japanese (should work, untested)
- Korean (should work, untested)

PRs welcome for language-specific configs.

## License

MIT
