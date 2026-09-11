# Topic Radar

Pulls trending AI topics from free APIs and asks an LLM to curate the ones
most worth turning into a Tech2You video, with a one-line angle for each.

## Sources (v1)

| Source | API | Auth | Notes |
|---|---|---|---|
| Hacker News | [Algolia HN Search](https://hn.algolia.com/api) | none | Keyword search across AI-related terms, filtered by min points |
| arXiv | [arXiv API](https://info.arxiv.org/help/api/index.html) | none | Latest papers in cs.AI / cs.CL / cs.LG |
| GitHub | [REST Search API](https://docs.github.com/en/rest/search) | none (rate-limited) | AI-tagged repos created in the last 7 days, sorted by stars — see the caveat in [`sources/github_trending.py`](sources/github_trending.py) |

**X/Twitter is intentionally excluded.** Its free API tier stopped supporting
reads/search of other users' posts in 2023 — it's paid-only for that now, so
it doesn't work as a free topic source.

Reddit was left out of v1 too (it needs a one-time OAuth app registration,
still free) — easy to add later as another module in `sources/`.

## Usage

```bash
pip install -r ../requirements.txt
cp ../.env.example ../.env   # add your GEMINI_API_KEY (free) — see root README.md#setup
python digest.py --top 8
```

Writes `digests/<today's date>.md` — a ranked shortlist with source, link, and
a suggested video angle for each item. Digests are meant to be committed, so
the repo doubles as a running log of what was considered and when.

## Adding a source

Each module in `sources/` exposes one function: `fetch(limit=15) -> list[dict]`,
returning items shaped like:

```python
{"title": str, "url": str, "source": str, "signal": str, "published_at": str, "summary": str}
```

Add the module, then include it in `gather_items()` in [`digest.py`](digest.py).
