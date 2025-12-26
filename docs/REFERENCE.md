# Audio Anki Pipeline - Reference

## Overview

This pipeline processes audio from YouTube videos (especially streams) into Anki decks for language learning. It uses:
- **Silero VAD** for voice activity detection
- **Gemini API** for transcription and verification
- **genanki** for deck building

## Pipeline Flow

```
01_download.sh   → stream_raw.mp4, stream.m4a
02_vad.py        → segments.json
03_extract.py    → batch_audio/, clips/
04_transcribe.py → transcriptions.json
05_clean.py      → transcriptions_cleaned.json
06_apply_drops.py → drops.txt (manual)
07_verify.py     → verification_results.json
08_build_deck.py → <stream-id>.apkg
```

---

## VAD Parameters

```python
# Silero VAD 6.2.0
min_silence_duration_ms = 300   # Min silence to split segments
speech_pad_ms = 50              # Padding around speech detection
min_speech_duration_ms = 800    # Ignore speech shorter than this
post_pad_s = 0.25               # Extra padding added to each segment
```

These are tuned for VTuber streams with background music. Adjust in `lib/config.py` if needed.

---

## Batch Transcription

Segments are grouped into batches of 20 for efficient API usage.

```python
BATCH_SIZE = 20
EDGE_PADDING = 0.5  # Extra audio at batch boundaries
```

**Batch audio format:**
- Single .m4a file spanning all segments in batch
- Includes 0.5s padding at start/end for context
- Timestamps in prompt are relative to batch audio start

**Prompt structure:**
```
Transcribe these audio segments:
[00:00-00:03] Segment 0
[00:05-00:08] Segment 1
...

Return JSON array with original transcription and English translation.
```

---

## Transcription Output

`transcriptions.json`:
```json
{
  "transcriptions": [
    {
      "clip_id": 0,
      "original": "Selamat malam semuanya",
      "english": "Good evening everyone"
    }
  ]
}
```

---

## Cleaning Rules

`05_clean.py` auto-drops:
- Pure English clips (where original == english)

Manual drops go in `drops.txt`:
```
# Comments start with #
# One clip ID per line

# Pure English
43
45

# Fragments / noise
17
```

---

## Verification

`07_verify.py` sends each clip + transcription to Gemini for verification.

**Features:**
- Rate-limited (default 20 RPM)
- Parallel workers (default 10)
- Resumable (saves progress incrementally)
- Retries on transient failures

**Output schema:**
```json
{
  "clip_id": 0,
  "original": true,
  "english": false,
  "corrected_original": "",
  "corrected_english": "Good evening, everyone!",
  "notes": "Minor punctuation fix"
}
```

---

## Deck Building

`08_build_deck.py` creates Anki deck with:
- Front: audio player
- Back: Original text + English translation

Only includes clips that:
- Are verified (in verification_results.json)
- Are not in drops.txt
- Have corrections applied if flagged

---

## Configuration

Environment variables:
- `GEMINI_API_KEY` - API key (or put in `~/.gemini_key`)
- `GEMINI_MODEL` - Model name (default: gemini-2.0-flash)
- `TARGET_LANGUAGE` - Language to transcribe (default: Indonesian)
- `YT_COOKIES` - Path to YouTube cookies file for members-only content

Edit `lib/config.py` for:
- VAD parameters
- Batch size
- Rate limits
- Worker count

---

## Requirements

- Python 3.10+
- ffmpeg
- yt-dlp (for download)
- See requirements.txt for Python packages

---

## Notes

- VAD runs best on GPU but works on CPU
- Gemini free tier: ~1500 requests/day (varies)
- For long streams, verification may take multiple days due to rate limits
- The verify loop pattern: `while true; do ./07_verify.py; sleep 180; done`
