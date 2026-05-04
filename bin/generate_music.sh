#!/bin/bash
# Generate ambient background music for Sentinel Shorts
# Uses FFmpeg sine wave synthesis (CC-0, no copyright issues)

MUSIC_DIR="$(cd "$(dirname "$0")/../data/music" && pwd)"
mkdir -p "$MUSIC_DIR"

echo "🎵 Generating ambient space music..."

# Deep space drone — 80Hz with echo
echo "  Generating deep_space_drone.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=80:duration=60:sample_rate=44100" \
  -af "volume=0.12, aecho=0.4:0.6:1000:0.5, aecho=0.3:0.5:2000:0.3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/deep_space_drone.mp3" 2>/dev/null

# Ethereal pad — 220Hz with layered echoes
echo "  Generating ethereal_pad.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=220:duration=60:sample_rate=44100" \
  -af "volume=0.08, aecho=0.5:0.7:500:0.4, aecho=0.3:0.5:1500:0.3, aecho=0.2:0.4:3000:0.2" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/ethereal_pad.mp3" 2>/dev/null

# Cosmic pulse — 55Hz with tremolo
echo "  Generating cosmic_pulse.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=55:duration=60:sample_rate=44100" \
  -af "volume=0.10, aecho=0.6:0.8:800:0.5, tremolo=f=0.3:d=0.4" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/cosmic_pulse.mp3" 2>/dev/null

# Starlight shimmer — 330Hz + 440Hz mix
echo "  Generating starlight_shimmer.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=330:duration=60:sample_rate=44100" \
  -af "volume=0.06, aecho=0.3:0.5:700:0.3, aecho=0.2:0.4:1400:0.2, aecho=0.1:0.3:2800:0.15" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/starlight_shimmer.mp3" 2>/dev/null

# Lunar calm — 120Hz soft pad
echo "  Generating lunar_calm.mp3..."
ffmpeg -y -f lavfi -i "sine=frequency=120:duration=60:sample_rate=44100" \
  -af "volume=0.07, aecho=0.3:0.7:600:0.3, afade=t=in:st=0:d=3, afade=t=out:st=57:d=3" \
  -c:a libmp3lame -b:a 128k "$MUSIC_DIR/lunar_calm.mp3" 2>/dev/null

echo ""
echo "✅ Generated $(ls "$MUSIC_DIR"/*.mp3 2>/dev/null | wc -l) ambient tracks"
ls -lh "$MUSIC_DIR"/*.mp3 2>/dev/null
