#!/usr/bin/env python3
"""LLM-powered eval harness for prompt library entries.

Usage: python scripts/eval.py prompts/examples/code-review-agent.yaml
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from common.llm import LLMError, complete  # noqa: E402

from ruamel.yaml import YAML  # noqa: E402

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 100

# Defensive cap: a prompt file with runaway test_cases shouldn't silently burn
# through a free-tier quota (or a bill, if using Claude).
MAX_TEST_CASES = 10


def render(template: str, inputs: dict) -> str:
    rendered = template
    for name, value in inputs.items():
        rendered = rendered.replace("{{" + name + "}}", str(value))
    return rendered


def run_prompt(template: str, inputs: dict) -> str:
    return complete(render(template, inputs), max_tokens=2048)


def score_response(response_text: str, expected_contains: list) -> dict:
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

    text = complete(grading_prompt, max_tokens=200)

    score = None
    for line in text.splitlines():
        if line.lower().startswith("score:"):
            try:
                score = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    # Take everything after "notes:" rather than just that line's remainder —
    # models sometimes put "notes:" on its own line with the text below it,
    # which a same-line split would silently turn into an empty string.
    lower_text = text.lower()
    notes_idx = lower_text.find("notes:")
    notes = text[notes_idx + len("notes:"):].strip() if notes_idx != -1 else text.strip()

    return {"score": score, "notes": notes}


def main():
    parser = argparse.ArgumentParser(description="Score a prompt-library entry against its test cases.")
    parser.add_argument("prompt_file", help="Path to a prompt YAML file")
    args = parser.parse_args()

    with open(args.prompt_file, encoding="utf-8") as f:
        data = yaml.load(f)

    test_cases = data.get("test_cases") or []
    if not test_cases:
        sys.exit(f"{args.prompt_file} has no test_cases to run.")
    if len(test_cases) > MAX_TEST_CASES:
        print(f"Note: only running the first {MAX_TEST_CASES} of {len(test_cases)} test_cases.")
        test_cases = test_cases[:MAX_TEST_CASES]

    template = data["prompt"]

    try:
        scores = []
        notes = []
        for case in test_cases:
            print(f"Running: {case['name']}")
            response_text = run_prompt(template, case.get("inputs", {}))
            result = score_response(response_text, case.get("expected_contains", []))
            print(f"  score={result['score']} notes={result['notes']}")
            if result["score"] is not None:
                scores.append(result["score"])
            notes.append(f"{case['name']}: {result['notes']}")
    except LLMError as exc:
        sys.exit(str(exc))

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
