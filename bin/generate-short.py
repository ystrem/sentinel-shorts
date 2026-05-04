#!/usr/bin/env python3
"""
Sentinel Shorts — Main Generator
Orchestrates: fetch image → pick fact → render Shorts → deliver
"""

import sys
import json
import yaml
import random
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add bin/ to path for imports
BIN_DIR = Path(__file__).parent
REPO_DIR = BIN_DIR.parent
sys.path.insert(0, str(BIN_DIR))

from fetch_image import fetch_image, load_nasa_key
from render_short import ShortsRenderer
from space_facts import load_facts, get_random_fact, generate_fact_from_apod


def load_config() -> dict:
    """Load YAML config."""
    config_path = REPO_DIR / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)


CONFIG = load_config()


def generate_short(date: Optional[str] = None,
                   fact_id: Optional[str] = None,
                   category: Optional[str] = None,
                   output_dir: Optional[Path] = None,
                   quiet: bool = False) -> Optional[Path]:
    """
    Generate a single Shorts video.
    
    Args:
        date: APOD date for background image
        fact_id: Specific fact ID to use
        category: Filter facts by category
        output_dir: Custom output directory
        quiet: Minimal output
    
    Returns:
        Path to generated video, or None on failure
    """
    if not quiet:
        print(f"\n{'='*50}")
        print(f"  🚀 Sentinel Shorts Generator")
        print(f"{'='*50}")
    
    # 1. Fetch background image
    if not quiet:
        print(f"\n📸 Step 1: Fetching background image...")
    
    cache_dir = REPO_DIR / "data" / "images"
    result = fetch_image(date, cache_dir, prefer_random=True)
    
    if not result:
        print(f"  ❌ Failed to get background image")
        return None
    
    img_path, apod_data = result
    
    # 2. Get or generate space fact
    if not quiet:
        print(f"\n📝 Step 2: Getting space fact...")
    
    fact = None
    if fact_id:
        # Specific fact by ID
        facts = load_facts()
        fact = next((f for f in facts if f.get("id") == fact_id), None)
        if not fact:
            print(f"  ⚠ Fact '{fact_id}' not found")
    
    if not fact:
        # Random fact, optionally filtered by category
        fact = get_random_fact(category)
    
    if not fact:
        # Fallback: generate from APOD
        if not quiet:
            print(f"  ⚠ No fact in database, generating from APOD...")
        nasa_key = load_nasa_key()
        fact = generate_fact_from_apod(apod_data, nasa_key)
    
    if not fact:
        print(f"  ❌ No fact available")
        return None
    
    if not quiet:
        print(f"  📌 {fact.get('title', '')}")
        if fact.get("year"):
            print(f"     {fact.get('year')}")
        print(f"     {fact.get('subtitle', '')}")
    
    # 3. Render Shorts video
    if not quiet:
        print(f"\n🎬 Step 3: Rendering Shorts video...")
    
    if output_dir is None:
        output_dir = REPO_DIR / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find music
    music_dir = REPO_DIR / "data" / "music"
    music_files = list(music_dir.glob("*.mp3")) if music_dir.exists() else []
    music_path = random.choice(music_files) if music_files else None
    if music_path and not quiet:
        print(f"  🎵 Music: {music_path.name}")
    elif not music_files:
        if not quiet:
            print(f"  ⚠ No music files found, rendering silent")
    
    # Determine output filename
    safe_title = fact.get("id", fact.get("title", "shorts").lower().replace(" ", "_"))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"shorts_{safe_title}_{timestamp}.mp4"
    
    renderer = ShortsRenderer(CONFIG)
    ok = renderer.render(img_path, fact, output_path, music_path)
    
    if not ok:
        print(f"  ❌ Render failed")
        return None
    
    if not quiet:
        print(f"\n{'='*50}")
        print(f"  ✅ Shorts video generated!")
        print(f"     📁 {output_path}")
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"     📏 {size_mb:.1f} MB")
        print(f"{'='*50}\n")
    
    return output_path


def deliver_to_telegram(video_path: Path, fact: dict):
    """Send generated Shorts to Telegram."""
    telegram_script = Path.home() / "bin" / "telegram-send.py"
    if not telegram_script.exists():
        print(f"  ⚠ Telegram script not found")
        return False
    
    import subprocess
    delivery_cfg = CONFIG.get("delivery", {}).get("telegram", {})
    chat_id = delivery_cfg.get("chat_id", "362955491")
    category = fact.get("category", "Space")
    caption = delivery_cfg.get("caption", "🌌 {fact_category}\n#Space #Shorts #Facts")
    caption = caption.format(fact_category=category.capitalize())
    
    import os
    env = os.environ.copy()
    
    result = subprocess.run(
        [str(telegram_script), "--chat_id", chat_id,
         "--media", str(video_path), "--message", caption],
        capture_output=True, text=True, timeout=60,
        env=env
    )
    
    if result.returncode == 0:
        print(f"  ✅ Delivered to Telegram")
        return True
    else:
        print(f"  ❌ Telegram delivery failed: {result.stderr[:200]}")
        return False


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate a Shorts space fact video")
    parser.add_argument("--date", default=None, help="APOD date (YYYY-MM-DD or 'today')")
    parser.add_argument("--fact-id", default=None, help="Specific fact ID from database")
    parser.add_argument("--category", default=None, help="Fact category filter")
    parser.add_argument("--output", default=None, help="Output directory")
    parser.add_argument("--deliver", action="store_true", help="Deliver to Telegram")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--list-facts", action="store_true", help="List available facts")
    parser.add_argument("--list-categories", action="store_true", help="List fact categories")
    
    args = parser.parse_args()
    
    # List operations
    if args.list_categories:
        from space_facts import get_categories
        cats = get_categories()
        print("Available categories:")
        for c in cats:
            print(f"  • {c}")
        return 0
    
    if args.list_facts:
        facts = load_facts()
        print(f"Available facts ({len(facts)}):")
        for f in facts:
            print(f"  [{f.get('id', '?')}] {f.get('title', '')}")
        return 0
    
    # Generate
    output_dir = Path(args.output) if args.output else None
    video_path = generate_short(
        date=args.date,
        fact_id=args.fact_id,
        category=args.category,
        output_dir=output_dir,
        quiet=args.quiet,
    )
    
    if not video_path:
        return 1
    
    # Deliver to Telegram if requested
    if args.deliver:
        fact = None
        if args.fact_id:
            from space_facts import get_fact_by_id
            fact = get_fact_by_id(args.fact_id)
        if not fact:
            from space_facts import get_random_fact
            fact = get_random_fact(args.category)
        if fact:
            deliver_to_telegram(video_path, fact)
    
    return 0


if __name__ == "__main__":
    exit(main())
