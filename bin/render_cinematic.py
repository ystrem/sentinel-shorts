#!/usr/bin/env python3
"""
Sentinel Shorts — Cinematic Shorts Producer
Creates a polished Shorts video with:
- Dark gradient overlay for text readability
- Animated text (fade-in with proper positioning)
- TTS narration audio
- No background music
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime


# ─── SCENE DEFINITION ─────────────────────────────────────────────
# Each segment: (start, end, text, font_size, x_center, y_pos)
# x_center: "(w-text_w)/2" for centered
# y_pos: "Y" as pixel or expression

SEGMENTS = [
    # Opening: title fades in
    (0.5, 5.0, "Carrington Event", 48, "(w-text_w)/2", 780),
    # Year appears below title
    (1.5, 5.0, "1859", 64, "(w-text_w)/2", 860),
    # Subtitle when TTS says "Northern lights..."
    (3.0, 9.5, "Northern lights visible from Cuba", 28, "(w-text_w)/2", 1000),
]

NARRATION = (
    "In 1859, during the Carrington Event, "
    "the Northern lights were so bright that people in Cuba "
    "could read newspapers at midnight."
)


def create_gradient_overlay(output_path, width=1080, height=1920):
    """Create a dark gradient overlay from transparent top to semi-opaque bottom."""
    print(f"  Gradient overlay...")
    # Full gradient: transparent → dark at bottom
    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", f"color=c=#000000:s={width}x{height}:d=1:r=1",
        "-vf", (
            f"format=rgba,"
            f"geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':"
            f"a='255-255*(Y/{height})'"
        ),
        "-frames:v", "1",
        "-c:v", "png",
        str(output_path),
    ]
    subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    print(f"  ✓ {output_path.name}")


def render_cinematic_shorts(image_path, audio_path, output_path,
                             font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                             width=1080, height=1920):
    """
    Render final cinematic Shorts with proper text positioning.
    """
    duration = 10
    fps = 30
    total_frames = duration * fps

    # Create gradient overlay
    grad_dir = output_path.parent / ".gradients"
    grad_dir.mkdir(exist_ok=True)
    gradient_png = grad_dir / "gradient_full.png"
    create_gradient_overlay(gradient_png, width, height)

    # Ken Burns zoom
    zoompan = (
        f"zoompan=z='min(1+0.15*on/{total_frames},1.15)':"
        f"d={total_frames}:"
        f"x='iw/2-(iw/zoom/2)':"
        f"y='ih/2-(ih/zoom/2)':"
        f"s={width}x{height}:fps={fps}"
    )

    # Build drawtext filters with alpha fade
    text_filters = []
    for start, end, text, fontsize, x_pos, y_pos in SEGMENTS:
        fade = min(0.4, (end - start) / 5)
        alpha = (
            f"if(lte(t,{start}+{fade}),(t-{start})/{fade},"
            f"if(gte(t,{end}-{fade}),({end}-t)/{fade},1))"
        )
        # Escape single quotes in text for FFmpeg
        safe_text = text.replace("'", "\\'").replace("%", "\\%")
        text_filters.append(
            f"drawtext=text='{safe_text}':"
            f"fontfile={font_path}:"
            f"fontsize={fontsize}:"
            f"fontcolor=white:"
            f"alpha='{alpha}':"
            f"x={x_pos}:"
            f"y={y_pos}:"
            f"shadowcolor=black:"
            f"shadowx=2:shadowy=2:"
            f"enable='between(t,{start},{end})'"
        )

    # Filter complex
    filter_parts = [
        f"[0:v]{zoompan}[bg]",
        f"[1:v]loop=loop={total_frames}:size=1,format=rgba[grad]",
        "[bg][grad]overlay=0:0[base]",
    ]
    # Chain drawtext
    chain = "[base]" + ",".join(text_filters)
    filter_parts.append(f"{chain}[outv]")
    # Audio
    has_audio = audio_path and Path(audio_path).exists()
    filter_parts.append(
        f"[2:a]afade=t=out:st={duration-1.5}:d=1.5[aud]"
        if has_audio else
        "[2:a]volume=0[aud]"
    )

    filter_complex = ";".join(filter_parts)

    # FFmpeg command
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", str(image_path),
        "-i", str(gradient_png),
    ]
    if has_audio:
        cmd.extend(["-i", str(audio_path)])
    else:
        cmd.extend(["-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono"])

    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]", "-map", "[aud]",
        "-shortest",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-r", str(fps), "-t", str(duration),
        "-movflags", "+faststart",
        str(output_path),
    ])

    print(f"🎬 Rendering cinematic Shorts...")
    print(f"  Image: {Path(image_path).name}")
    print(f"  Audio: {'✓' if has_audio else '— (silent)'}")
    print(f"  {duration}s @ {fps}fps, {width}x{height}")

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

    if output_path.exists() and output_path.stat().st_size > 0:
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  ✅ Rendered: {output_path.name} ({size_mb:.1f} MB)")
        return True
    else:
        print(f"  ❌ Render failed")
        for line in result.stderr.strip().split("\n")[-15:]:
            print(f"     {line}")
        return False


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Render cinematic Shorts")
    parser.add_argument("--image", required=True)
    parser.add_argument("--audio", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    image_path = Path(args.image)
    audio_path = Path(args.audio) if args.audio else None
    output_dir = Path(__file__).parent.parent / "output" / "cinematic"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = Path(args.output) if args.output else \
        output_dir / f"cinematic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"

    ok = render_cinematic_shorts(image_path, audio_path, output_path)
    return 0 if ok else 1


if __name__ == "__main__":
    exit(main())
