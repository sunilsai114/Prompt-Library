"""Hacker News source — free, no auth, via the Algolia HN Search API.

Algolia's `query` param is plain full-text search, not boolean syntax — a
single "A OR B OR C" query matches almost nothing. So this runs one query per
keyword and merges/dedupes the results instead.
"""

import requests

HN_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"
KEYWORDS = ["AI", "LLM", "GPT", "Claude", "machine learning", "neural network", "Anthropic", "OpenAI"]


def fetch(limit: int = 15, min_points: int = 20) -> list:
    seen = {}
    for keyword in KEYWORDS:
        params = {
            "tags": "story",
            "query": keyword,
            "numericFilters": f"points>={min_points}",
            "hitsPerPage": 10,
        }
        resp = requests.get(HN_SEARCH_URL, params=params, timeout=15)
        resp.raise_for_status()
        for hit in resp.json().get("hits", []):
            object_id = hit.get("objectID")
            if object_id in seen:
                continue
            points = hit.get("points", 0)
            seen[object_id] = {
                "title": hit.get("title"),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={object_id}",
                "source": "Hacker News",
                "signal": f"{points} points",
                "_rank": points,
                "published_at": hit.get("created_at"),
                "summary": "",
            }

    items = sorted(seen.values(), key=lambda it: it["_rank"], reverse=True)[:limit]
    for item in items:
        item.pop("_rank", None)
    return items
