#!/bin/bash
# Download stream and extract audio

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PIPELINE_ROOT="$SCRIPT_DIR"

# Cookies path - set via env or argument
COOKIES="${YT_COOKIES:-}"

usage() {
    echo "Usage: $0 <stream-id> <url> [cookies-file]"
    echo ""
    echo "Arguments:"
    echo "  stream-id    Identifier for this stream (e.g., my-stream-2025-01)"
    echo "  url          YouTube URL"
    echo "  cookies-file Optional: path to cookies file (or set YT_COOKIES env)"
    echo ""
    echo "Example:"
    echo "  $0 my-stream-2025-01 'https://youtube.com/watch?v=xxx' ~/cookies.txt"
    echo "  YT_COOKIES=~/cookies.txt $0 my-stream-2025-01 'https://youtube.com/watch?v=xxx'"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

STREAM_ID="$1"
URL="$2"
if [ -n "$3" ]; then
    COOKIES="$3"
fi

STREAM_DIR="$PIPELINE_ROOT/streams/$STREAM_ID"

# Build yt-dlp cookie args
COOKIE_ARGS=""
if [ -n "$COOKIES" ]; then
    if [ ! -f "$COOKIES" ]; then
        echo "Error: Cookies file not found: $COOKIES"
        exit 1
    fi
    COOKIE_ARGS="--cookies $COOKIES"
fi

# Fetch title from YouTube
echo "Fetching title..."
TITLE=$(yt-dlp $COOKIE_ARGS --get-title "$URL" 2>/dev/null || echo "$STREAM_ID")
echo "Title: $TITLE"
echo ""

# Create directory if needed
if [ ! -d "$STREAM_DIR" ]; then
    mkdir -p "$STREAM_DIR"/{clips,batch_audio}
    touch "$STREAM_DIR/drops.txt"
fi

cd "$STREAM_DIR"

# Create stream.json
cat > stream.json << EOF
{
  "id": "$STREAM_ID",
  "url": "$URL",
  "title": "$TITLE",
  "created": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF

# Download (format 93 = 360p, same audio as 1080p, 1/6 size)
echo "Downloading..."
yt-dlp $COOKIE_ARGS -f 93 -o "stream_raw.mp4" "$URL"

echo ""
echo "Extracting audio..."
ffmpeg -y -i stream_raw.mp4 -vn -c:a copy stream.m4a

echo ""
ls -lh stream_raw.mp4 stream.m4a
echo ""
echo "Next: cd streams/$STREAM_ID && ../../02_vad.py"
