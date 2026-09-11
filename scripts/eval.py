#!/usr/bin/env python3
"""Claude-powered eval harness for prompt library entries.

Usage: python scripts/eval.py prompts/examples/code-review-agent.yaml
"""

import argparse
import os
import sys
from datetime import datetime, timezone

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from ruamel.yaml import YAML
import anthropic

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 100

MODEL = "claude-sonnet-5"


def render(template: str, inputs: dict) -> str:
    rendered = template
    for name, value in inputs.items():
        rendered = rendered.replace("{{" + name + "}}", str(value))
    return rendered


def run_prompt(client: anthropic.Anthropic, template: str, inputs: dict) -> str:
    rendered = render(template, inputs)
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        messages=[{"role": "user", "content": rendered}],
    )
    return "".join(block.text for block in response.content if block.type == "text")


def score_response(client: anthropic.Anthropic, response_text: str, expected_contains: list) -> dict:
    if not expected_contains:
        rubric = (
            "The expected behavior was that the response should NOT raise any "
            "false-positive concerns. Score 5 if it correctly found nothing to "
            "flag, lower if it invented issues."
        )
    else:
        joined = ", ".join(f'"{e}"' for e in expected_contains)
        rubric = (
            f"The response should meaningfully cover these concepts: {joined}. "
            "Score 5 if all are clearly addressed, lower for each one missing or vague."
        )

    grading_prompt = f"""You are grading an AI response for a prompt-library eval.

{rubric}

Response to grade:
---
{response_text}
---

Reply with exactly two lines:
score: <integer 1-5>
notes: <one sentence on what was missing or well done>"""

    result = client.messages.create(
        model=MODEL,
        max_tokens=200,
        messages=[{"role": "user", "content": grading_prompt}],
    )
    text = "".join(block.text for block in result.content if block.type == "text")

    score, notes = None, text.strip()
    for line in text.splitlines():
        if line.lower().startswith("score:"):
            try:
                score = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass
        if line.lower().startswith("notes:"):
            notes = line.split(":", 1)[1].strip()
    return {"score": score, "notes": notes}


def main():
    parser = argparse.ArgumentParser(description="Score a prompt-library entry against its test cases.")
    parser.add_argument("prompt_file", help="Path to a prompt YAML file")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in, or export it directly.")

    with open(args.prompt_file, encoding="utf-8") as f:
        data = yaml.load(f)

    test_cases = data.get("test_cases") or []
    if not test_cases:
        sys.exit(f"{args.prompt_file} has no test_cases to run.")

    client = anthropic.Anthropic(api_key=api_key)
    template = data["prompt"]

    scores = []
    notes = []
    for case in test_cases:
        print(f"Running: {case['name']}")
        response_text = run_prompt(client, template, case.get("inputs", {}))
        result = score_response(client, response_text, case.get("expected_contains", []))
        print(f"  score={result['score']} notes={result['notes']}")
        if result["score"] is not None:
            scores.append(result["score"])
        notes.append(f"{case['name']}: {result['notes']}")

    avg_score = round(sum(scores) / len(scores), 2) if scores else None

    data["eval"] = {
        "last_run": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "score": avg_score,
        "notes": " | ".join(notes),
    }

    with open(args.prompt_file, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    print(f"\nAverage score: {avg_score}")


if __name__ == "__main__":
    main()
