"""GitHub source — free via the public search API (unauthenticated: 10 req/min).

GitHub has no public "trending" endpoint, so this approximates it: AI-tagged
repos *created* in the last `days` days, sorted by stars. That surfaces new
tools gaining traction, not older repos suddenly spiking — a real limitation,
but the closest free signal available without scraping github.com/trending.

The search API also doesn't support "(topic:a OR topic:b)" grouping reliably,
so this runs one query per topic and merges/dedupes the results instead.
"""

from datetime import datetime, timedelta, timezone

import requests

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "tech2you-topic-radar"}
TOPICS = ["ai", "llm", "machine-learning", "generative-ai", "agents"]


def fetch(limit: int = 15, days: int = 7) -> list:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    seen = {}
    for topic in TOPICS:
        query = f"topic:{topic} created:>{since}"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": 10}
        resp = requests.get(GITHUB_SEARCH_URL, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        for repo in resp.json().get("items", []):
            repo_id = repo["id"]
            if repo_id in seen:
                continue
            stars = repo["stargazers_count"]
            seen[repo_id] = {
                "title": repo["full_name"],
                "url": repo["html_url"],
                "source": "GitHub",
                "signal": f"{stars} stars",
                "_rank": stars,
                "published_at": repo["created_at"],
                "summary": (repo.get("description") or "")[:300],
            }

    items = sorted(seen.values(), key=lambda it: it["_rank"], reverse=True)[:limit]
    for item in items:
        item.pop("_rank", None)
    return items
