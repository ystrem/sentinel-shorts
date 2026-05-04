#!/usr/bin/env python3
"""
Sentinel Shorts — Image Fetcher
Fetches background images from NASA APOD or other space image sources.
"""

import json
import urllib.request
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


NASA_API_URL = "https://api.nasa.gov/planetary/apod"


def load_nasa_key() -> str:
    """Load NASA API key from environment or .env file."""
    import os
    key = os.getenv("NASA_API_KEY")
    if key:
        return key

    # Try sentinel-media-factory .env
    env_paths = [
        Path.home() / "sentinel-shorts" / ".env",
        Path.home() / "sentinel-media-factory" / ".env",
        Path.home() / ".hermes" / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("NASA_API_KEY=") and not line.startswith("#"):
                    return line.split("=", 1)[1].strip()
    return "DEMO_KEY"


def fetch_apod(date: Optional[str] = None) -> Optional[dict]:
    """Fetch APOD data from NASA API."""
    api_key = load_nasa_key()
    
    if date and date.lower() == "today":
        date = datetime.now().strftime("%Y-%m-%d")
    elif date is None:
        date = "today"
    
    url = f"{NASA_API_URL}?api_key={api_key}"
    if date and date != "today":
        url += f"&date={date}"
    
    print(f"  🌍 Fetching NASA APOD...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Sentinel-Shorts/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
        
        if data.get("media_type") == "image":
            print(f"  ✓ {data.get('title', 'Unknown')} ({data.get('date', '')})")
            return data
        else:
            print(f"  ⚠ Media type is {data.get('media_type')} — skipping")
            return None
    except Exception as e:
        print(f"  ✗ NASA API error: {e}")
        return None


def download_image(url: str, output_path: Path) -> bool:
    """Download image from URL to local path."""
    try:
        print(f"  ↓ Downloading image...")
        req = urllib.request.Request(url, headers={"User-Agent": "Sentinel-Shorts/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            output_path.write_bytes(resp.read())
        
        size_mb = output_path.stat().st_size / (1024 * 1024)
        print(f"  ✓ Saved: {output_path.name} ({size_mb:.1f} MB)")
        return True
    except Exception as e:
        print(f"  ✗ Download failed: {e}")
        return False


def fetch_image(date: Optional[str] = None,
                cache_dir: Optional[Path] = None,
                max_age_days: int = 7) -> Optional[tuple[Path, dict]]:
    """
    Fetch a space background image and return (image_path, metadata).
    
    Falls back to recent images if today's APOD is not available.
    """
    if cache_dir is None:
        cache_dir = Path(__file__).parent.parent / "data" / "images"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Try to fetch APOD
    apod = fetch_apod(date)
    if apod and apod.get("media_type") == "image":
        img_url = apod.get("hdurl") or apod.get("url")
        date_str = apod.get("date", datetime.now().strftime("%Y-%m-%d"))
        ext = img_url.split(".")[-1].split("?")[0] if img_url else "jpg"
        if ext.lower() not in ("jpg", "jpeg", "png"):
            ext = "jpg"
        
        img_path = cache_dir / f"apod_{date_str}.{ext}"
        if not img_path.exists():
            if not download_image(img_url, img_path):
                return None
        else:
            print(f"  ✓ Cached: {img_path.name}")
        
        return img_path, apod

    # Fallback: try last N days
    print(f"  ⚠ Trying recent APOD images...")
    for days_ago in range(1, max_age_days + 1):
        past_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
        apod = fetch_apod(past_date)
        if apod and apod.get("media_type") == "image":
            img_url = apod.get("hdurl") or apod.get("url")
            ext = img_url.split(".")[-1].split("?")[0] if img_url else "jpg"
            if ext.lower() not in ("jpg", "jpeg", "png"):
                ext = "jpg"
            img_path = cache_dir / f"apod_{past_date}.{ext}"
            if not img_path.exists():
                if download_image(img_url, img_path):
                    return img_path, apod
            else:
                print(f"  ✓ Cached: {img_path.name}")
                return img_path, apod
    
    print(f"  ✗ No APOD image available")
    return None


def main():
    """CLI entry point."""
    import argparse
    import sys
    
    parser = argparse.ArgumentParser(description="Fetch space background image")
    parser.add_argument("--date", default=None, help="APOD date (YYYY-MM-DD)")
    parser.add_argument("--output", default=None, help="Output directory")
    args = parser.parse_args()
    
    cache_dir = Path(args.output) if args.output else None
    result = fetch_image(args.date, cache_dir)
    
    if result:
        img_path, metadata = result
        print(f"\n✅ Image: {img_path}")
        print(f"   Title: {metadata.get('title', '')}")
        print(f"   Date:  {metadata.get('date', '')}")
        return 0
    return 1


if __name__ == "__main__":
    exit(main())
