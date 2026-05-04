#!/usr/bin/env python3
"""
Generate recipe cards (markdown) for each cinematic Shorts video.
Documents every parameter: APOD, TTS, segments, FFmpeg filters, output.
"""

import json
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent.parent / "output" / "cinematic"
RECIPES_DIR = Path(__file__).parent.parent / "recipes"
RECIPES_DIR.mkdir(exist_ok=True)

# ─── DATA FOR EACH SHORTS ────────────────────────────────────────

SCENES = [
    {
        "id": "saturn-moons",
        "output_file": "shorts_saturn-moons.mp4",
        "fact_title": "Which Planet Has the Most Moons? (2024)",
        "fact_source": "space_facts.json — id: saturn-moons",
        "apod": {
            "date": "2026-04-12",
            "title": "Comet R3 (PanSTARRS) Brightens",
            "url": "https://apod.nasa.gov/apod/ap260412.html",
        },
        "narration": "Which planet has the most moons? Saturn has 146 confirmed moons, more than any other planet in our solar system. Jupiter comes second with ninety five.",
        "tts_audio": "tts_saturn-moons.wav",
        "tts_params": {
            "model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "voice_preset": "narrator",
            "language": "english",
            "speed": 1.0,
            "temperature": 0.9,
        },
        "tts_duration": 12.2,
        "segments": [
            (0.5, 5.0, "Which Planet Has\nthe Most Moons?", 42, "(w-text_w)/2", 780, "Title — large, centered"),
            (1.5, 5.0, "2024", 64, "(w-text_w)/2", 870, "Year — gold, large"),
            (3.0, 9.5, "Saturn — 146 confirmed moons", 28, "(w-text_w)/2", 1000, "Subtitle — key fact"),
        ],
    },
    {
        "id": "gold-from-space",
        "output_file": "shorts_gold-from-space.mp4",
        "fact_title": "Gold Comes From Space",
        "fact_source": "space_facts.json — id: gold-from-space",
        "apod": {
            "date": "2026-04-08",
            "title": "Earthset",
            "url": "https://apod.nasa.gov/apod/ap260408.html",
        },
        "narration": "The gold on Earth was formed in neutron star collisions billions of years ago. We are literally wearing stardust.",
        "tts_audio": "tts_gold-from-space.wav",
        "tts_params": {
            "model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "voice_preset": "narrator",
            "language": "english",
            "speed": 1.0,
            "temperature": 0.9,
        },
        "tts_duration": 8.9,
        "segments": [
            (0.5, 5.0, "Gold Comes From Space", 48, "(w-text_w)/2", 780, "Title"),
            (3.0, 8.5, "Forged in neutron star collisions", 28, "(w-text_w)/2", 1000, "Subtitle"),
        ],
    },
    {
        "id": "jupiter-red-spot",
        "output_file": "shorts_jupiter-red-spot.mp4",
        "fact_title": "Jupiter's Great Red Spot (1665)",
        "fact_source": "space_facts.json — id: jupiter-red-spot",
        "apod": {
            "date": "2026-04-16",
            "title": "South Celestial Tree",
            "url": "https://apod.nasa.gov/apod/ap260416.html",
        },
        "narration": "Jupiter's Great Red Spot is a storm larger than Earth that has been raging for at least three hundred and fifty years.",
        "tts_audio": "tts_jupiter-red-spot.wav",
        "tts_params": {
            "model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "voice_preset": "narrator",
            "language": "english",
            "speed": 1.0,
            "temperature": 0.9,
        },
        "tts_duration": 7.0,
        "segments": [
            (0.5, 5.0, "Jupiters Great Red Spot", 48, "(w-text_w)/2", 780, "Title (apostrophe removed for FFmpeg compat)"),
            (1.5, 5.0, "1665", 64, "(w-text_w)/2", 870, "Year"),
            (3.0, 9.5, "A storm bigger than Earth", 28, "(w-text_w)/2", 1000, "Subtitle"),
        ],
    },
    {
        "id": "pluto-heart",
        "output_file": "shorts_pluto-heart.mp4",
        "fact_title": "Pluto Has a Heart (2015)",
        "fact_source": "space_facts.json — id: pluto-heart",
        "apod": {
            "date": "2026-04-04",
            "title": "Hello World",
            "url": "https://apod.nasa.gov/apod/ap260404.html",
        },
        "narration": "Pluto has a heart shaped glacier called Tombaugh Regio, discovered by New Horizons in twenty fifteen. It is made of nitrogen ice.",
        "tts_audio": "tts_pluto-heart.wav",
        "tts_params": {
            "model": "Qwen/Qwen3-TTS-12Hz-1.7B-VoiceDesign",
            "voice_preset": "narrator",
            "language": "english",
            "speed": 1.0,
            "temperature": 0.9,
        },
        "tts_duration": 8.9,
        "segments": [
            (0.5, 5.0, "Pluto Has a Heart", 48, "(w-text_w)/2", 780, "Title"),
            (1.5, 5.0, "2015", 64, "(w-text_w)/2", 870, "Year"),
            (3.0, 9.5, "A giant glacier in the shape of a heart", 26, "(w-text_w)/2", 1000, "Subtitle"),
        ],
    },
]

# ─── RECIPE GENERATION ──────────────────────────────────────────

def generate_recipe(scene: dict, video_path: Path) -> str:
    """Generate a markdown recipe card for a Shorts video."""
    
    import subprocess
    
    # Get video info
    info = {}
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", 
         "format=size,duration,bit_rate",
         "-of", "json", str(video_path)],
        capture_output=True, text=True, timeout=10,
    )
    if probe.returncode == 0:
        info = json.loads(probe.stdout).get("format", {})
    
    size_mb = int(info.get("size", 0)) / (1024*1024) if info.get("size") else 0
    duration = float(info.get("duration", 0))
    bitrate = int(info.get("bit_rate", 0)) // 1000 if info.get("bit_rate") else 0
    
    # Build recipe
    recipe = f"""# 📋 Recipe: {scene['fact_title']}

> **Output:** `{scene['output_file']}` | {size_mb:.1f} MB | {duration:.0f}s | 1080×1920 | {bitrate} kbps

---

## 1. 📸 Background Image

| Param | Value |
|-------|-------|
| **Source** | NASA APOD |
| **Date** | {scene['apod']['date']} |
| **Title** | {scene['apod']['title']} |
| **URL** | {scene['apod']['url']} |
| **Processing** | Scale+center-crop to fill 1080×1920 portrait |
| **Aspect fix** | `scale=force_original_aspect_ratio=increase,crop=1080:1920` |

## 2. 🎙️ Narration (TTS)

| Param | Value |
|-------|-------|
| **Engine** | Qwen3 TTS (v2.1.0) |
| **Model** | `{scene['tts_params']['model']}` |
| **Voice** | `{scene['tts_params']['voice_preset']}` |
| **Language** | `{scene['tts_params']['language']}` |
| **Speed** | {scene['tts_params']['speed']} |
| **Temperature** | {scene['tts_params']['temperature']} |
| **Duration** | {scene['tts_duration']}s |
| **Server** | http://localhost:8050 (Docker, GPU P40) |
| **Inference** | ~30s generation on Tesla P40 |

**Narration text:**
```
{scene['narration']}
```

## 3. 📝 Text Overlays

| # | Start | End | Text | Font Size | Y Position | Notes |
|---|-------|-----|------|-----------|------------|-------|
"""
    
    for i, seg in enumerate(scene["segments"], 1):
        start, end, text, size, x, y, note = seg
        recipe += f"| {i} | {start}s | {end}s | `{text}` | {size}px | {y} | {note} |\n"
    
    recipe += f"""
**Style parameters (all segments):**
- Color: `white` (full opacity with fade)
- Alpha fade: 0.4s fade-in, 0.4s fade-out per segment
- Drop shadow: `black`, 2px offset
- Horizontal position: centered `(w-text_w)/2`
- Enable: `between(t,start,end)`
- Font: `DejaVuSans.ttf` (system)

## 4. 🎞️ Video Composition

| Layer | Element | Filter |
|-------|---------|--------|
| 1 (bottom) | APOD background | `scale + crop + zoompan` (Ken Burns 1.0→1.15) |
| 2 | Dark gradient overlay | `geq` alpha gradient (transparent top → 100% bottom) |
| 3 | Text | `drawtext` with fade animation |
| 4 (top) | TTS audio | `afade` out at 1.5s before end |

**Full FFmpeg filter complex:**
```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,
zoompan=z='min(1+0.15*on/{300:.0f},1.15)':d={300:.0f}:
x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':
s=1080x1920:fps=30[bg];

[1:v]loop=loop={300:.0f}:size=1,format=rgba[grad];

[bg][grad]overlay=0:0[base];

[base]drawtext=...text filters...[outv];

[2:a]afade=t=out:st={duration-1.5:.1f}:d=1.5[aud]
```

## 5. ⚙️ Encoding

| Param | Value |
|-------|-------|
| Codec | H.264 (libx264) |
| CRF | 18 (high quality) |
| Preset | medium |
| Pixel format | yuv420p |
| Audio codec | AAC, 128 kbps, mono |
| FPS | 30 |
| Duration | {duration:.0f}s |
| Total frames | ~{int(duration*30)} |

---

*Generated: 2026-05-04 | Sentinel Shorts Pipeline v1*
"""
    return recipe


def main():
    for scene in SCENES:
        video_path = OUTPUT_DIR / scene["output_file"]
        if not video_path.exists():
            print(f"⚠️  Missing: {scene['output_file']}")
            continue
        
        recipe = generate_recipe(scene, video_path)
        recipe_path = RECIPES_DIR / f"recipe_{scene['id']}.md"
        recipe_path.write_text(recipe)
        print(f"✅ Recipe: recipe_{scene['id']}.md")
    
    # Generate index
    index = "# 📚 Shorts Recipe Collection\n\n"
    for scene in SCENES:
        video_path = OUTPUT_DIR / scene["output_file"]
        size = video_path.stat().st_size / (1024*1024) if video_path.exists() else 0
        index += f"- [{scene['fact_title']}](recipe_{scene['id']}.md) — `{scene['output_file']}` ({size:.1f} MB, {scene['apod']['date']})\n"
    
    (RECIPES_DIR / "README.md").write_text(index)
    print(f"✅ Index: README.md")
    print(f"\n📁 {RECIPES_DIR}/")


if __name__ == "__main__":
    main()
