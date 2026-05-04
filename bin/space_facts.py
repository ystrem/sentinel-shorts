#!/usr/bin/env python3
"""
Sentinel Shorts — Space Facts Engine
Manages a database of interesting space facts for Shorts videos.
Can return random facts, facts by category, or generate facts from APOD.
"""

import json
import random
from pathlib import Path
from typing import Optional


def load_facts(facts_path: Optional[Path] = None) -> list[dict]:
    """Load space facts from JSON database."""
    if facts_path is None:
        facts_path = Path(__file__).parent.parent / "data" / "facts" / "space_facts.json"
    
    if not facts_path.exists():
        print(f"  ⚠ Facts database not found: {facts_path}")
        return []
    
    with open(facts_path) as f:
        return json.load(f)


def get_random_fact(category: Optional[str] = None) -> Optional[dict]:
    """Get a random space fact, optionally filtered by category."""
    facts = load_facts()
    if not facts:
        return None
    
    if category:
        filtered = [f for f in facts if f.get("category", "").lower() == category.lower()]
        if not filtered:
            print(f"  ⚠ No facts in category '{category}', using any")
            filtered = facts
    else:
        filtered = facts
    
    return random.choice(filtered) if filtered else None


def get_fact_by_id(fact_id: str) -> Optional[dict]:
    """Get a specific fact by ID."""
    facts = load_facts()
    for fact in facts:
        if fact.get("id") == fact_id:
            return fact
    return None


def get_categories() -> list[str]:
    """List all available categories."""
    facts = load_facts()
    categories = sorted(set(f.get("category", "uncategorized") for f in facts))
    return categories


def generate_fact_from_apod(apod_data: dict, api_key: Optional[str] = None) -> Optional[dict]:
    """
    Generate a Shorts-friendly fact from NASA APOD data using AI.
    Falls back to simple extraction if AI is unavailable.
    """
    title = apod_data.get("title", "Unknown")
    explanation = apod_data.get("explanation", "")
    date = apod_data.get("date", "")
    
    # Try AI generation first
    if api_key:
        try:
            return _generate_with_ai(title, explanation, date, api_key)
        except Exception as e:
            print(f"  ⚠ AI fact generation failed: {e}")
    
    # Fallback: extract interesting snippet from explanation
    return _extract_from_explanation(title, explanation, date)


def _extract_from_explanation(title: str, explanation: str, date: str) -> dict:
    """Extract a fact-like snippet from APOD explanation."""
    # Take first 1-2 sentences
    import re
    sentences = re.split(r'(?<=[.!?])\s+', explanation)
    fact_text = sentences[0] if sentences else explanation
    
    # Remove trailing ... if present
    fact_text = re.sub(r'\s*\.\.\.$', '.', fact_text)
    
    # Keep it short
    if len(fact_text) > 200:
        fact_text = fact_text[:197] + "..."
    
    return {
        "id": f"apod_{date}",
        "title": title,
        "year": date[:4] if date else "",
        "subtitle": fact_text[:80] + "..." if len(fact_text) > 80 else fact_text,
        "fact": fact_text,
        "category": "apod",
        "tags": ["nasa", "apod"],
        "source": "NASA APOD",
    }


def _generate_with_ai(title: str, explanation: str, date: str, api_key: str) -> dict:
    """Use AI to generate a Shorts-style fact from APOD data."""
    import httpx
    
    prompt = f"""Create an interesting Shorts-style space fact from this NASA APOD data.
    
Title: {title}
Explanation: {explanation}

Format as JSON:
{{
    "title": "Short engaging title (1-4 words)",
    "year": "Year if relevant (e.g. '2024' or empty string)",
    "subtitle": "One-line interesting detail (max 80 chars)",
    "fact": "The full fact text (1-2 sentences, max 200 chars)",
    "category": "One of: planets, stars, galaxies, history, spacecraft, cosmology, astronomy, black-holes"
}}

Return ONLY valid JSON, nothing else."""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    import yaml
    config_path = Path(__file__).parent.parent / "config.yaml"
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    ai_cfg = config.get("ai", {})
    payload = {
        "model": ai_cfg.get("model", "qwen3.5-plus"),
        "messages": [{"role": "user", "content": prompt}],
        "temperature": ai_cfg.get("temperature", 0.7),
        "max_tokens": 300,
    }
    
    with httpx.Client(timeout=30) as client:
        resp = client.post(
            f"{ai_cfg.get('base_url', 'http://aicore:4000')}/v1/chat/completions",
            headers=headers,
            json=payload,
        )
        resp.raise_for_status()
        data = resp.json()
        content = data["choices"][0]["message"]["content"]
    
    # Extract JSON from response
    import re
    json_match = re.search(r'\{.*\}', content, re.DOTALL)
    if json_match:
        fact = json.loads(json_match.group())
        fact["id"] = f"apod_{date}"
        fact["tags"] = ["nasa", "apod", "ai-generated"]
        fact["source"] = "NASA APOD"
        return fact
    
    return _extract_from_explanation(title, explanation, date)


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Space facts engine")
    parser.add_argument("--random", action="store_true", help="Get random fact")
    parser.add_argument("--category", default=None, help="Filter by category")
    parser.add_argument("--id", dest="fact_id", default=None, help="Get fact by ID")
    parser.add_argument("--list", action="store_true", help="List all categories")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if args.list:
        cats = get_categories()
        print("Categories:")
        for c in cats:
            count = len([f for f in load_facts() if f.get("category") == c])
            print(f"  • {c} ({count} facts)")
        return 0
    
    fact = None
    if args.fact_id:
        fact = get_fact_by_id(args.fact_id)
    elif args.random:
        fact = get_random_fact(args.category)
    else:
        fact = get_random_fact()
    
    if fact:
        if args.json:
            print(json.dumps(fact, indent=2))
        else:
            print(f"📌 {fact.get('title', '')}")
            if fact.get("year"):
                print(f"   {fact.get('year')}")
            if fact.get("subtitle"):
                print(f"   {fact.get('subtitle')}")
            print(f"   ──")
            print(f"   {fact.get('fact', '')}")
            print(f"   [{fact.get('category', '')}]")
        return 0
    else:
        print("No facts available")
        return 1


if __name__ == "__main__":
    exit(main())
