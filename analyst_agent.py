"""Requirements analyst agent for the robot-navigation brief.

The model is responsible for producing the JSON values.  This module only
prompts Qwen, parses its response, and validates the agreed contract.
"""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen



REQUIRED_KEYS = ("goal", "allowed_actions", "safe_stop", "avoid_obstacles")
ALLOWED_ACTIONS = ["FORWARD", "LEFT", "RIGHT", "STOP"]


def build_analyst_prompt(brief_text: str) -> str:
    """Build the user prompt sent to Qwen."""
    return f"""
You are a requirements analyst for a mobile robot navigation system.

Read the human-language brief below and convert it into the exact software
requirements object requested by the system prompt.

Rules:
- The robot must prefer moving toward its goal when that direction is safe.
- The robot must never move in a blocked direction.
- If no direction is safe, the robot must stop.
- The only navigation actions are FORWARD, LEFT, RIGHT, and STOP.
- Return a JSON object with exactly these four keys and no others:
  goal (string), allowed_actions (array), safe_stop (boolean),
  avoid_obstacles (boolean).
- goal must be a concise human-readable sentence describing safe navigation
  toward the goal while avoiding blocked directions; do not use placeholders
  such as "goal_position".
- allowed_actions must be exactly ["FORWARD", "LEFT", "RIGHT", "STOP"].
- Return JSON only. Do not add Markdown fences, comments, or explanations.

Human-language brief:
---
{brief_text.strip()}
---
""".strip()


def validate_requirements(result: Any) -> dict[str, Any]:
    """Validate and return a requirements object matching the exact schema."""
    if not isinstance(result, dict):
        raise ValueError("Qwen output must be a JSON object")

    actual_keys = set(result)
    expected_keys = set(REQUIRED_KEYS)
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    if missing:
        raise ValueError(f"Missing requirement keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected requirement keys: {sorted(extra)}")

    if not isinstance(result["goal"], str) or not result["goal"].strip():
        raise ValueError("goal must be a non-empty string")
    if not isinstance(result["allowed_actions"], list):
        raise ValueError("allowed_actions must be a list")
    if result["allowed_actions"] != ALLOWED_ACTIONS:
        raise ValueError(
            f"allowed_actions must be exactly {ALLOWED_ACTIONS!r}"
        )
    if not isinstance(result["safe_stop"], bool):
        raise ValueError("safe_stop must be a boolean")
    if not isinstance(result["avoid_obstacles"], bool):
        raise ValueError("avoid_obstacles must be a boolean")

    # Return a fresh object so callers cannot accidentally retain extra data.
    return {
        "goal": result["goal"].strip(),
        "allowed_actions": list(result["allowed_actions"]),
        "safe_stop": result["safe_stop"],
        "avoid_obstacles": result["avoid_obstacles"],
    }


def _extract_json(response_text: str) -> dict[str, Any]:
    """Parse JSON from Qwen, tolerating fences or short surrounding text."""
    text = response_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        # Small local models occasionally add one sentence before the object.
        start = text.find("{")
        if start < 0:
            raise ValueError("Qwen did not return valid JSON") from None
        try:
            parsed, _ = json.JSONDecoder().raw_decode(text[start:])
        except json.JSONDecodeError as exc:
            raise ValueError("Qwen did not return valid JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Qwen JSON must be an object")
    return parsed


def _ollama_settings() -> tuple[str, str, float]:
    """Read the local Ollama endpoint, model, and request timeout."""
    base_url = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    model = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
    timeout = float(os.getenv("OLLAMA_TIMEOUT", "120"))
    return base_url, model, timeout


def ask_qwen(
    prompt: str,
    *,
    json_mode: bool = False,
    system_prompt: str = (
        "You are a careful requirements analyst. Follow the user's "
        "requested output format exactly."
    ),
) -> str:
    """Ask the locally running Qwen model through Ollama's HTTP API."""
    base_url, model, timeout = _ollama_settings()
    payload: dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system_prompt,
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }
    if json_mode:
        payload["format"] = "json"

    request = Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            response_data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama returned HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(
            f"Could not connect to Ollama at {base_url}. Start Ollama and try again."
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError("Ollama returned an invalid JSON response") from exc

    try:
        content = response_data["message"]["content"]
    except (KeyError, TypeError) as exc:
        raise RuntimeError("Unexpected response shape from Ollama") from exc
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama returned empty message content")
    return content.strip()


def run_analyst(brief_text: str) -> dict[str, Any]:
    """Ask Qwen to analyze the brief, parse JSON, validate it, and return it."""
    if not isinstance(brief_text, str) or not brief_text.strip():
        raise ValueError("brief_text must be a non-empty string")
    raw_response = ask_qwen(build_analyst_prompt(brief_text), json_mode=True)
    return validate_requirements(_extract_json(raw_response))


__all__ = [
    "ALLOWED_ACTIONS",
    "REQUIRED_KEYS",
    "ask_qwen",
    "build_analyst_prompt",
    "run_analyst",
    "validate_requirements",
]
