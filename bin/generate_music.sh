#!/bin/bash
# Generate ambient background music for Sentinel Shorts
# Simple sine wave tones — no heavy echo processing
# CC-0, no copyright issues

MUSIC_DIR="$(cd "$(dirname "$0")/../data/music" && pwd)"
mkdir -p "$MUSIC_DIR"

echo "🎵 Generating ambient space music..."

# Deep drone — low frequency pad
echo "  Generating deep_space_drone.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=55:duration=60:sample_rate=44100" \
  -af "volume=0.5, lowpass=f=200, aecho=0.8:0.6:1000:0.4" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/deep_space_drone.mp3" 2>/dev/null

# Ethereal — mid frequency with subtle shimmer
echo "  Generating ethereal_pad.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=220:duration=60:sample_rate=44100" \
  -af "volume=0.4, aecho=0.7:0.5:800:0.3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/ethereal_pad.mp3" 2>/dev/null

# Cosmic — gentle pulse
echo "  Generating cosmic_pulse.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=80:duration=60:sample_rate=44100" \
  -af "volume=0.4, tremolo=f=0.4:d=0.3, aecho=0.6:0.7:1200:0.3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/cosmic_pulse.mp3" 2>/dev/null

# Starlight — higher shimmer
echo "  Generating starlight_shimmer.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=330:duration=60:sample_rate=44100" \
  -af "volume=0.35, aecho=0.6:0.5:700:0.3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/starlight_shimmer.mp3" 2>/dev/null

# Lunar calm — soft pad
echo "  Generating lunar_calm.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=120:duration=60:sample_rate=44100" \
  -af "volume=0.45, aecho=0.7:0.6:600:0.3, afade=t=in:st=0:d=3, afade=t=out:st=57:d=3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/lunar_calm.mp3" 2>/dev/null

echo ""
echo "✅ Generated $(ls "$MUSIC_DIR"/*.mp3 2>/dev/null | wc -l) ambient tracks"

# Normalize all to reasonable level
for f in "$MUSIC_DIR"/*.mp3; do
  name=$(basename "$f")
  level=$(ffmpeg -i "$f" -af "volumedetect" -f null - 2>&1 | grep "max_volume" | grep -oP '[-0-9.]+(?= dB)')
  if [ -n "$level" ]; then
    boost=$(echo "$level" | head -1 | awk '{print -1 * $1 + 6}' | cut -d. -f1)
    if [ "$boost" -gt 0 ]; then
      echo "  Normalizing $name (+${boost}dB)..."
      tmp=$(mktemp /tmp/music_XXXX.mp3)
      ffmpeg -y -i "$f" -af "volume=${boost}dB" "$tmp" 2>/dev/null && mv "$tmp" "$f"
    fi
  fi
done

echo ""
ls -lh "$MUSIC_DIR"/*.mp3 2>/dev/null