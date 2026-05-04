#!/usr/bin/env python3
"""
Batch generate 4 cinematic Shorts with different facts and APOD images.
Each Shorts has:
- Unique APOD background from ~1 month ago
- Qwen3 TTS narration
- Gradient overlay + animated text
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from datetime import datetime

REPO_DIR = Path(__file__).parent.parent
OUTPUT_DIR = REPO_DIR / "output" / "cinematic"

# ─── SCENE DEFINITIONS ────────────────────────────────────────
# Each scene: (fact_id, image_date, narration, segments, output_name)

SCENES = [
    {
        "id": "saturn-moons",
        "image": "apod_2026-04-12.jpg",  # Comet R3 (PanSTARRS)
        "narration": "Which planet has the most moons? Saturn has 146 confirmed moons, more than any other planet in our solar system. Jupiter comes second with ninety five.",
        "segments": [
            (0.5, 5.0, "Which Planet Has\nthe Most Moons?", 42, "(w-text_w)/2", 780),
            (1.5, 5.0, "2024", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "Saturn — 146 confirmed moons", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "gold-from-space",
        "image": "apod_2026-04-08.jpg",  # Earthset
        "narration": "The gold on Earth was formed in neutron star collisions billions of years ago. We are literally wearing stardust.",
        "segments": [
            (0.5, 5.0, "Gold Comes From Space", 48, "(w-text_w)/2", 780),
            (3.0, 8.5, "Forged in neutron star collisions", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "jupiter-red-spot",
        "image": "apod_2026-04-16.jpg",  # South Celestial Tree
        "narration": "Jupiter's Great Red Spot is a storm larger than Earth that has been raging for at least three hundred and fifty years.",
        "segments": [
            (0.5, 5.0, "Jupiters Great Red Spot", 48, "(w-text_w)/2", 780),
            (1.5, 5.0, "1665", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "A storm bigger than Earth", 28, "(w-text_w)/2", 1000),
        ],
    },
    {
        "id": "pluto-heart",
        "image": "apod_2026-04-04.jpg",  # Hello World
        "narration": "Pluto has a heart shaped glacier called Tombaugh Regio, discovered by New Horizons in twenty fifteen. It is made of nitrogen ice.",
        "segments": [
            (0.5, 5.0, "Pluto Has a Heart", 48, "(w-text_w)/2", 780),
            (1.5, 5.0, "2015", 64, "(w-text_w)/2", 870),
            (3.0, 9.5, "A giant glacier in the shape of a heart", 26, "(w-text_w)/2", 1000),
        ],
    },
]

TTS_URL = "http://localhost:8050/generate"
CONTAINER = "sentinel-media-factory-tts-server-1"
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"


def create_gradient(grad_dir, width=1080, height=1920):
    """Create gradient overlay PNG."""
    grad_path = grad_dir / "gradient_full.png"
    if grad_path.exists():
        return grad_path
    
    grad_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#000000:s={width}x{height}:d=1:r=1",
        "-vf", f"format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='255-255*(Y/{height})'",
        "-frames:v", "1", "-c:v", "png", str(grad_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return grad_path


def generate_tts(text, output_path):
    """Generate TTS audio using Qwen3."""
    import requests
    print(f"    🎙️ TTS: {text[:50]}...")
    resp = requests.post(
        TTS_URL,
        json={
            "text": text,
            "language": "english",
            "voice_preset": "narrator",
            "speed": 1.0,
            "temperature": 0.9,
        },
        timeout=120,
    )
    resp.raise_for_status()
    data = resp.json()
    
    # Copy from container
    container_path = data["file_path"]
    subprocess.run(
        ["docker", "cp", f"{CONTAINER}:{container_path}", str(output_path)],
        capture_output=True, text=True, timeout=30,
    )
    print(f"      ✅ {data['duration']:.1f}s audio ({Path(output_path).name})")
    return data["duration"]


def render_shorts(image_path, gradient_path, audio_path, segments, output_path):
    """Render a single cinematic Shorts with TTS."""
    width, height = 1080, 1920
    duration = 10
    fps = 30
    total_frames = duration * fps
    
    # Ken Burns zoom — fix aspect ratio: scale to fill portrait then crop
    # APOD images are landscape, we need portrait 1080×1920 without stretching
    zoompan = (f"scale=w={width}:h={height}:force_original_aspect_ratio=increase,"
               f"crop={width}:{height},"
               f"zoompan=z='min(1+0.15*on/{total_frames},1.15)':"
               f"d={total_frames}:"
               f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
               f"s={width}x{height}:fps={fps}")
    
    # Text filters
    text_filters = []
    for start, end, text, fontsize, x_pos, y_pos in segments:
        fade = min(0.4, (end - start) / 5)
        safe = text.replace("'", "’").replace("%", "%%")
        alpha = (f"if(lte(t,{start}+{fade}),(t-{start})/{fade},"
                 f"if(gte(t,{end}-{fade}),({end}-t)/{fade},1))")
        text_filters.append(
            f"drawtext=text='{safe}':fontfile={FONT}:"
            f"fontsize={fontsize}:fontcolor=white:alpha='{alpha}':"
            f"x={x_pos}:y={y_pos}:shadowcolor=black:shadowx=2:shadowy=2:"
            f"enable='between(t,{start},{end})'"
        )
    
    # Filter complex
    filters = [
        f"[0:v]{zoompan}[bg]",
        f"[1:v]loop=loop={total_frames}:size=1,format=rgba[grad]",
        "[bg][grad]overlay=0:0[base]",
    ]
    chain = "[base]" + ",".join(text_filters)
    filters.append(f"{chain}[outv]")
    filters.append(f"[2:a]afade=t=out:st={duration-1.5}:d=1.5[aud]")
    filter_complex = ";".join(filters)
    
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", str(gradient_path),
        "-i", str(audio_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[aud]",
        "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-r", str(fps), "-t", str(duration),
        "-movflags", "+faststart",
        str(output_path),
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if output_path.exists():
        mb = output_path.stat().st_size / (1024 * 1024)
        print(f"      ✅ {output_path.name} ({mb:.1f} MB)")
        return True
    else:
        print(f"      ❌ FFmpeg error")
        for line in result.stderr.strip().split("\n")[-5:]:
            print(f"         {line}")
        return False


def main():
    print("=" * 50)
    print("  🚀 Batch generating 4 cinematic Shorts")
    print("=" * 50)
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    images_dir = REPO_DIR / "data" / "images"
    grad_dir = OUTPUT_DIR / ".gradients"
    
    # Create gradient (shared)
    print("\n📐 Creating gradient overlay...")
    gradient_path = create_gradient(grad_dir)
    
    totals = {"success": 0, "fail": 0}
    
    for i, scene in enumerate(SCENES, 1):
        print(f"\n{'='*50}")
        print(f"  📹 Shorts {i}/4: {scene['id']}")
        print(f"{'='*50}")
        
        # Image
        img_path = images_dir / scene["image"]
        if not img_path.exists():
            print(f"  ❌ Image not found: {scene['image']}")
            totals["fail"] += 1
            continue
        
        print(f"  🖼️  Image: {scene['image']}")
        
        # TTS
        audio_path = OUTPUT_DIR / f"tts_{scene['id']}.wav"
        if not audio_path.exists():
            try:
                dur = generate_tts(scene["narration"], audio_path)
            except Exception as e:
                print(f"  ❌ TTS failed: {e}")
                totals["fail"] += 1
                continue
        else:
            print(f"  🎙️ TTS cached: {audio_path.name}")
        
        # Render
        output_path = OUTPUT_DIR / f"shorts_{scene['id']}.mp4"
        if render_shorts(img_path, gradient_path, audio_path, scene["segments"], output_path):
            totals["success"] += 1
        else:
            totals["fail"] += 1
    
    print(f"\n{'='*50}")
    print(f"  ✅ Done: {totals['success']}/{len(SCENES)} videos")
    if totals["fail"]:
        print(f"  ❌ Failed: {totals['fail']}")
    print(f"  📁 {OUTPUT_DIR}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()
