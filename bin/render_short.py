#!/usr/bin/env python3
"""
Sentinel Shorts — Vertical Shorts Renderer
Renders a background image with text overlays + music into 1080×1920 Shorts video.
Uses FFmpeg drawtext for clean text rendering.
"""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Optional


# Load configuration
def load_config(config_path: Optional[Path] = None) -> dict:
    """Load YAML config."""
    import yaml
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


CONFIG = load_config()


class ShortsRenderer:
    """Renders vertical Shorts videos with text overlays."""

    def __init__(self, config: Optional[dict] = None):
        self.config = config or CONFIG
        self.video_cfg = self.config.get("video", {})
        self.text_cfg = self.config.get("text", {})
        self.music_cfg = self.config.get("music", {})

        self.width, self.height = 1080, 1920

    def build_text_filters(self, fact: dict) -> list:
        """
        Build FFmpeg drawtext filter chain for the fact overlay.
        Returns list of drawtext filter strings.
        
        Layout (UNIVERSIA-style):
        - Title: 48px CENTERED (y ~ center - 80)
        - Year: 64px CENTERED (y ~ center + 20) — if present
        - Subtitle: 24px CENTERED (y ~ center + 110)
        """
        filters = []
        font = self.text_cfg.get("title", {}).get("font", "Arial")
        shadow = self.text_cfg.get("title", {}).get("shadow", True)
        shadow_color = self.text_cfg.get("title", {}).get("shadow_color", "#000000")

        center_y = self.height // 2  # 960

        # Escape special FFmpeg characters in text
        def escape_ffmpeg(text: str) -> str:
            return text.replace("'", "\\'").replace(":", "\\:").replace("%", "\\%")

        # Build shadow + main text for a line
        def drawtext_filter(text: str, fontsize: int, x: str, y: str,
                           color: str = "#FFFFFF", box: int = 0,
                           box_color: str = "#000000@0.5") -> list:
            lines = []
            txt = escape_ffmpeg(text)
            if shadow:
                # Shadow
                lines.append(
                    f"drawtext=text='{txt}':fontsize={fontsize}:fontcolor={shadow_color}"
                    f":fontfile={font}:x={x}+2:y={y}+2:"
                    f"box={box}:boxcolor={box_color}"
                )
            # Main text
            lines.append(
                f"drawtext=text='{txt}':fontsize={fontsize}:fontcolor={color}"
                f":fontfile={font}:x={x}:y={y}"
                f":box={box}:boxcolor={box_color}"
            )
            return lines

        # --- Title (48px, centered) ---
        title = fact.get("title", "")
        title_size = self.text_cfg.get("title", {}).get("font_size", 48)
        title_y = f"{center_y - 80}"
        filters.extend(
            drawtext_filter(
                title,
                title_size,
                "(w-text_w)/2",
                title_y,
                color=self.text_cfg.get("title", {}).get("font_color", "#FFFFFF"),
            )
        )

        # --- Year (64px if present, centered) ---
        year = fact.get("year", "")
        if year:
            year_y = f"{center_y + 20}"
            filters.extend(
                drawtext_filter(
                    year,
                    64,
                    "(w-text_w)/2",
                    year_y,
                    color="#FFD700",  # Gold for year
                )
            )

        # --- Subtitle (24px, centered below) ---
        subtitle = fact.get("subtitle", "")
        subtitle_size = self.text_cfg.get("subtitle", {}).get("font_size", 24)
        if year:
            sub_y = f"{center_y + 110}"
        else:
            sub_y = f"{center_y + 20}"
        if subtitle:
            filters.extend(
                drawtext_filter(
                    subtitle,
                    subtitle_size,
                    "(w-text_w)/2",
                    sub_y,
                    color=self.text_cfg.get("subtitle", {}).get("font_color", "#CCCCCC"),
                )
            )

        return filters

    def render(self, image_path: Path, fact: dict, output_path: Path,
               music_path: Optional[Path] = None) -> bool:
        """
        Render a Shorts video from image + fact.
        
        Args:
            image_path: Path to background image
            fact: Fact dict with title, year, subtitle
            output_path: Output video path
            music_path: Optional background music
        """
        duration = self.video_cfg.get("duration", 20)
        fps = self.video_cfg.get("fps", 30)
        crf = self.video_cfg.get("crf", 23)

        # Build text filters
        text_filters = self.build_text_filters(fact)

        if not text_filters:
            print("  ✗ No text to render")
            return False

        # Combine all drawtext filters with commas
        text_filter_str = ",".join(text_filters)

        # Ken Burns zoom
        kb_cfg = self.video_cfg.get("ken_burns", {})
        if kb_cfg.get("enabled", True):
            zoom_start = kb_cfg.get("zoom_start", 1.0)
            zoom_end = kb_cfg.get("zoom_end", 1.15)
            total_frames = duration * fps
            # Gentle zoom
            zoom_expr = f"min({zoom_start}+({zoom_end}-{zoom_start})*on/{total_frames},{zoom_end})"
            zoom_filter = (
                f"zoompan=z='{zoom_expr}':"
                f"d={total_frames}:"
                f"x='iw/2-(iw/zoom/2)':"
                f"y='ih/2-(ih/zoom/2)':"
                f"s={self.width}x{self.height}"
            )
        else:
            zoom_filter = f"scale={self.width}:{self.height}:force_original_aspect_ratio=decrease,pad={self.width}:{self.height}:(ow-iw)/2:(oh-ih)/2:black"

        # Build FFmpeg command
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
        ]

        # Complex filter: zoom + text
        filter_complex = f"[0:v]{zoom_filter}[bg];[bg]{text_filter_str}[out]"

        # Add music if available
        if music_path and music_path.exists():
            music_vol = self.music_cfg.get("volume", 0.15)
            fade_in = self.music_cfg.get("fade_in", 1.5)
            fade_out = self.music_cfg.get("fade_out", 2.0)
            cmd.extend(["-i", str(music_path)])
            # Music audio with fade and volume
            afilter = (
                f"[1:a]"
                f"volume={music_vol},"
                f"afade=t=in:st=0:d={fade_in},"
                f"afade=t=out:st={duration-fade_out}:d={fade_out}"
                f"[audio]"
            )
            cmd.extend([
                "-filter_complex", f"{filter_complex};{afilter}",
                "-map", "[out]",
                "-map", "[audio]",
            ])
        else:
            cmd.extend([
                "-filter_complex", filter_complex,
                "-map", "[out]",
            ])
            # Generate silent audio track
            cmd.extend([
                "-f", "lavfi",
                "-i", "anullsrc=r=44100:cl=stereo",
                "-shortest",
            ])

        # Output encoding
        cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", str(crf),
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-t", str(duration),
            "-movflags", "+faststart",
            str(output_path),
        ])

        print(f"  🎬 Rendering Shorts video ({duration}s, {self.width}x{self.height})...")
        print(f"  Image: {image_path.name}")
        print(f"  Fact: {fact.get('title', '')}")
        if music_path and music_path.exists():
            print(f"  Music: {music_path.name}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if output_path.exists() and output_path.stat().st_size > 0:
            size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"  ✅ Shorts video created: {output_path.name} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"  ❌ Video creation failed")
            stderr_lines = result.stderr.strip().split("\n")[-20:]
            for line in stderr_lines:
                print(f"     {line}")
            return False

    def render_batch(self, image_path: Path, facts: list[dict], output_dir: Path,
                     music_path: Optional[Path] = None) -> list[Path]:
        """Render multiple Shorts videos from a list of facts."""
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        for i, fact in enumerate(facts):
            safe_title = fact.get("id", f"short_{i}")
            output_path = output_dir / f"{safe_title}.mp4"
            ok = self.render(image_path, fact, output_path, music_path)
            results.append((safe_title, ok, output_path))
        return results


def main():
    """CLI entry point for direct rendering."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Render Shorts video from image + fact")
    parser.add_argument("--image", required=True, help="Background image path")
    parser.add_argument("--fact", required=True, help="Fact JSON string or path to JSON file")
    parser.add_argument("--output", default=None, help="Output video path")
    parser.add_argument("--music", default=None, help="Background music path")
    parser.add_argument("--duration", type=int, default=20, help="Video duration in seconds")

    args = parser.parse_args()

    # Load fact
    fact_path = Path(args.fact)
    if fact_path.exists():
        with open(fact_path) as f:
            fact = json.load(f)
    else:
        try:
            fact = json.loads(args.fact)
        except json.JSONDecodeError:
            print("❌ Invalid fact JSON")
            return 1

    # Output path
    if args.output:
        output_path = Path(args.output)
    else:
        fact_id = fact.get("id", "shorts")
        output_path = Path("output") / f"{fact_id}.mp4"

    # Override duration
    renderer = ShortsRenderer()
    if args.duration:
        renderer.video_cfg["duration"] = args.duration

    # Render
    image_path = Path(args.image)
    music_path = Path(args.music) if args.music else None

    ok = renderer.render(image_path, fact, output_path, music_path)
    return 0 if ok else 1


if __name__ == "__main__":
    exit(main())
