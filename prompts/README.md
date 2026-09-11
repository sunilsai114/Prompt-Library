# Prompt format

Every prompt lives in its own YAML file. A prompt can stand alone, or declare its
position in a larger agent graph so multi-step recipes (router → tool-call →
critic → summarizer, etc.) are stored as data, not just prose.

## Schema

```yaml
id: string                     # unique, kebab-case, matches filename
title: string
description: string            # one line, what this prompt/agent does
category: single-prompt | agent-recipe

type: standalone | graph_node  # standalone prompt, or one node in a larger graph
graph:                         # only present when type: graph_node
  position: string             # this node's role, e.g. "reviewer"
  upstream: [string]           # ids of nodes that feed into this one
  downstream: [string]         # ids of nodes this one feeds into

model:
  recommended: string          # e.g. claude-sonnet-5
  min_context: int             # optional, tokens

variables:                     # inputs the prompt template expects
  - name: string
    type: string
    required: bool
    description: string

output_format:
  type: text | json
  schema: {}                   # optional, expected JSON shape when type: json

prompt: |                      # the actual prompt template, {{variable}} placeholders
  ...

test_cases:                    # inputs + what a good response must contain
  - name: string
    inputs: { variable_name: value }
    expected_contains: [string]   # substrings/concepts the response should cover

eval:                          # written by scripts/eval.py — don't hand-edit
  last_run: null
  score: null
  notes: null
```

## Adding a prompt

1. Copy [`examples/code-review-agent.yaml`](examples/code-review-agent.yaml) as a starting point.
2. Fill in `prompt`, `variables`, and at least one `test_case`.
3. Run the eval harness to score it before opening a PR:

```bash
python scripts/eval.py prompts/examples/your-prompt.yaml
```

This calls Claude once per test case to run the prompt, then once more to score
the response against `expected_contains`, and writes the result into the file's
`eval` block.
