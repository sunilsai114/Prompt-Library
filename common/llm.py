"""Provider-agnostic LLM client.

Defaults to Gemini's free tier (GEMINI_API_KEY). Set ANTHROPIC_API_KEY instead
to use Claude — it takes priority if both are set. Plain REST via `requests`
for both, so there's no SDK dependency either way.

Gemini free-tier keys are capped by Google at fixed rate limits and can't be
billed unless you've explicitly enabled billing on the underlying Cloud
project — a leaked key can burn your quota, not your money, as long as
billing stays off. See ../README.md for key-restriction steps.
"""

import os
import time

import requests

RETRY_STATUS_CODES = {502, 503, 504}
MAX_RETRIES = 3

GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")
CLAUDE_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"
CLAUDE_URL = "https://api.anthropic.com/v1/messages"

NO_KEY_MESSAGE = (
    "No LLM API key found. Copy .env.example to .env and set GEMINI_API_KEY "
    "(free — see README.md for setup) or ANTHROPIC_API_KEY."
)


class LLMError(RuntimeError):
    pass


def _provider() -> str:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    raise LLMError(NO_KEY_MESSAGE)


def complete(prompt: str, max_tokens: int = 1024) -> str:
    """Send a single prompt, return the model's text response."""
    provider = _provider()
    if provider == "anthropic":
        return _complete_claude(prompt, max_tokens)
    return _complete_gemini(prompt, max_tokens)


def _complete_gemini(prompt: str, max_tokens: int) -> str:
    api_key = os.environ["GEMINI_API_KEY"]

    resp = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(
                GEMINI_URL,
                params={"key": api_key},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": max_tokens},
                },
                timeout=60,
            )
        except requests.exceptions.RequestException as exc:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2**attempt)  # 1s, 2s
                continue
            raise LLMError(
                f"Couldn't reach Gemini after {MAX_RETRIES} attempts ({exc.__class__.__name__}) "
                "— likely a network issue or Google's API being unreachable right now. Try again in a bit."
            ) from exc
        if resp.status_code in RETRY_STATUS_CODES and attempt < MAX_RETRIES - 1:
            time.sleep(2**attempt)  # 1s, 2s
            continue
        break

    if resp.status_code == 429:
        raise LLMError(
            "Gemini free-tier rate limit hit. Wait a bit and retry, or reduce "
            "how many items/test cases you're processing in one run."
        )
    if resp.status_code == 404:
        raise LLMError(
            f"Gemini model '{GEMINI_MODEL}' wasn't found — Google retires model names "
            "over time. List current ones at "
            "https://generativelanguage.googleapis.com/v1beta/models?key=YOUR_KEY "
            "and set GEMINI_MODEL to one of them (in .env)."
        )
    if resp.status_code in RETRY_STATUS_CODES:
        raise LLMError(
            f"Gemini's servers returned {resp.status_code} after {MAX_RETRIES} attempts — "
            "this is on Google's end (overloaded/unavailable), not a problem with your "
            "key or prompt. Try again in a bit."
        )
    resp.raise_for_status()
    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Unexpected Gemini response shape: {data}") from exc


def _complete_claude(prompt: str, max_tokens: int) -> str:
    api_key = os.environ["ANTHROPIC_API_KEY"]
    resp = requests.post(
        CLAUDE_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=60,
    )
    resp.raise_for_status()
    data = resp.json()
    return "".join(block["text"] for block in data.get("content", []) if block.get("type") == "text")
