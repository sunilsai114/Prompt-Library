# Prompt-Library

Personal AI-literacy hub behind the **Tech2You** tech page — one place to learn, source content ideas, and reference material for videos.

Built for two jobs at once:

1. **Learning** — a running, organized base of AI knowledge (prompts, concepts, tools) I can revisit anytime.
2. **Content sourcing** — surfaces trending AI topics from free APIs so I always have a pipeline of ideas worth turning into a video, instead of guessing what to teach next.

## Sections

### Prompt Library
Prompt engineering didn't die, it moved down a layer — every agent loop, tool call, and graph node is still driven by a hand-tuned prompt underneath. So this isn't a "paste into ChatGPT" collection; it's reusable prompt building blocks for agents and pipelines: system prompts, tool-call instructions, few-shot examples, and eval rubrics, with LLM-powered quality scoring. (The original core of this project — kept as one pillar of the broader hub.)

### Topic Radar
Pulls trending AI topics from free, no-auth APIs (Hacker News, arXiv, GitHub) and asks an LLM to
curate the ones worth making a video about, with a suggested angle for each. See
[`topic_radar/README.md`](topic_radar/README.md) for usage and source details — including why
X/Twitter isn't one of the sources (its free API tier no longer supports reading other users' posts).

```bash
python topic_radar/digest.py --top 8
```

## Setup

Both pillars share one LLM client ([`common/llm.py`](common/llm.py)) that defaults to
**Gemini's free tier** and uses Claude instead if `ANTHROPIC_API_KEY` is set.

```bash
pip install -r requirements.txt
cp .env.example .env
```

Get a free Gemini key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey), then:
1. Leave billing **off** on that Cloud project — free-tier requests get rate-limited once you hit
   quota, but can't generate a bill, so this is what actually keeps a leaked key from costing money.
2. Restrict the key to the Generative Language API only (API restrictions in the console).
3. Keep `.env` out of git (already in `.gitignore`) and off-screen when recording.

## Quick start (Prompt Library v1)

Each prompt is a YAML file with variables, expected output format, and test cases —
see [`prompts/README.md`](prompts/README.md) for the schema, and
[`prompts/examples/code-review-agent.yaml`](prompts/examples/code-review-agent.yaml)
for a worked example, including how it declares its position in a larger agent graph.

```bash
python scripts/eval.py prompts/examples/code-review-agent.yaml
```

`scripts/eval.py` runs each test case through the LLM, scores the response, and
writes the result back into the prompt file's `eval` block — so quality scores
live next to the prompt, not in a separate spreadsheet.

## Status

Prompt Library v1 (composable prompt schema + eval harness) and Topic Radar v1
(Hacker News + arXiv + GitHub, LLM-curated digest) are both live, running on a
provider-agnostic client that defaults to Gemini's free tier.
