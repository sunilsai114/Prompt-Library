# Prompt-Library

Personal AI-literacy hub behind the **Tech2You** tech page — one place to learn, source content ideas, and reference material for videos.

Built for two jobs at once:

1. **Learning** — a running, organized base of AI knowledge (prompts, concepts, tools) I can revisit anytime.
2. **Content sourcing** — surfaces trending AI topics from free APIs so I always have a pipeline of ideas worth turning into a video, instead of guessing what to teach next.

## Sections

### Prompt Library
Prompt engineering didn't die, it moved down a layer — every agent loop, tool call, and graph node is still driven by a hand-tuned prompt underneath. So this isn't a "paste into ChatGPT" collection; it's reusable prompt building blocks for agents and pipelines: system prompts, tool-call instructions, few-shot examples, and eval rubrics, with Claude-powered quality scoring. (The original core of this project — kept as one pillar of the broader hub.)

### Topic Radar (planned)
Pulls trending AI topics/news from free-tier APIs (e.g. X/Twitter API, Reddit, Hacker News, arXiv, GitHub Trending) so I can spot what's worth making a video about, and keep a log of what's already been covered.

## Quick start (Prompt Library v1)

Each prompt is a YAML file with variables, expected output format, and test cases —
see [`prompts/README.md`](prompts/README.md) for the schema, and
[`prompts/examples/code-review-agent.yaml`](prompts/examples/code-review-agent.yaml)
for a worked example, including how it declares its position in a larger agent graph.

```bash
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
python scripts/eval.py prompts/examples/code-review-agent.yaml
```

`scripts/eval.py` runs each test case through Claude, scores the response, and
writes the result back into the prompt file's `eval` block — so quality scores
live next to the prompt, not in a separate spreadsheet.

## Status

Prompt Library v1 (composable prompt schema + eval harness) is live. Topic Radar is not yet built.
