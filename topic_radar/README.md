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

## Automation

[`.github/workflows/topic-radar.yml`](../.github/workflows/topic-radar.yml) runs this
automatically every Monday (`workflow_dispatch` also lets you trigger it manually from
the Actions tab), commits the new digest, and rebuilds the site — so you don't have to
remember to run it.

One-time setup: add your key as a repo secret so the workflow can use it (this has to be
done in GitHub's UI, not from a script — secrets are one-way write, no one can read them
back, including you):

1. Repo → Settings → Secrets and variables → Actions → New repository secret
2. Name: `GEMINI_API_KEY`, value: your key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

Until that secret exists, the workflow runs on schedule but skips the actual work (logs
a message and exits cleanly — no failure emails). Change the cadence by editing the
`cron` line in the workflow file.

## Adding a source

Each module in `sources/` exposes one function: `fetch(limit=15) -> list[dict]`,
returning items shaped like:

```python
{"title": str, "url": str, "source": str, "signal": str, "published_at": str, "summary": str}
```

Add the module, then include it in `gather_items()` in [`digest.py`](digest.py).
