#!/usr/bin/env python3
"""Pull trending AI topics from free APIs and curate a video-idea digest.

Usage: python topic_radar/digest.py [--top N]
"""

import argparse
import json
import sys
from datetime import date
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.llm import LLMError, complete  # noqa: E402

from sources import arxiv, github_trending, hackernews  # noqa: E402

DIGESTS_DIR = Path(__file__).parent / "digests"

# Defensive cap on the digest size — a big --top doesn't need more LLM calls
# (curation is one call regardless), but it does grow that call's token count.
MAX_TOP = 20


def gather_items() -> list:
    items = []
    items += hackernews.fetch()
    items += arxiv.fetch()
    items += github_trending.fetch()
    return items


def curate(items: list, top_n: int) -> list:
    catalog = [
        {
            "index": i,
            "title": it["title"],
            "source": it["source"],
            "signal": it.get("signal", ""),
            "summary": it.get("summary", ""),
        }
        for i, it in enumerate(items)
    ]

    prompt = f"""You're helping curate topics for an AI-literacy tech channel (Tech2You) that
teaches followers about AI concepts, tools, and news.

From this list of {len(catalog)} recent items, pick the {top_n} most worth making a video about.
Favor items that are explainable to a general audience, timely, and either teach a concept or
introduce something people should know about.

Items (JSON):
{json.dumps(catalog, indent=2)}

Respond with ONLY a JSON array (no prose, no markdown fences), ordered best-topic-first:
[{{"index": 0, "video_angle": "one sentence video angle/hook"}}, ...]"""

    # Generous budget: Gemini 3.x spends part of max_tokens on invisible
    # "thinking" before the visible output, so a tight cap can truncate the
    # JSON mid-array for a large catalog (seen firsthand with 45 items/1500).
    text = complete(prompt, max_tokens=4000).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]

    try:
        picks = json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Couldn't parse the curation response as JSON: {exc}\n\nRaw response:\n{text}") from exc
    return [{**items[pick["index"]], "video_angle": pick.get("video_angle", "")} for pick in picks]


def write_digest(curated: list, out_path: Path) -> None:
    lines = [f"# Topic Radar — {date.today().isoformat()}", ""]
    for item in curated:
        lines.append(f"## {item['title']}")
        lines.append(f"- Source: {item['source']} ({item.get('signal', '')})")
        lines.append(f"- Link: {item['url']}")
        lines.append(f"- Video angle: {item['video_angle']}")
        lines.append("")
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Pull trending AI topics and curate a video-idea digest.")
    parser.add_argument("--top", type=int, default=8, help=f"Number of items to keep in the digest (max {MAX_TOP})")
    args = parser.parse_args()
    if args.top > MAX_TOP:
        print(f"Note: capping --top at {MAX_TOP} (requested {args.top}).")
        args.top = MAX_TOP

    print("Gathering items from Hacker News, arXiv, GitHub...")
    items = gather_items()
    print(f"Collected {len(items)} raw items. Asking the LLM to curate top {args.top}...")

    try:
        curated = curate(items, top_n=args.top)
    except LLMError as exc:
        sys.exit(str(exc))

    DIGESTS_DIR.mkdir(exist_ok=True)
    out_path = DIGESTS_DIR / f"{date.today().isoformat()}.md"
    write_digest(curated, out_path)

    print(f"\nDigest written to {out_path}")


if __name__ == "__main__":
    main()
