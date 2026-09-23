"""Planner agent for the robot-navigation requirements artifact."""

from __future__ import annotations

import json
from typing import Any

from analyst_agent import (
    ALLOWED_ACTIONS,
    _extract_json,
    ask_qwen,
    validate_requirements,
)


PLAN_KEYS = ("strategy", "decisions", "stop_condition")
DECISION_KEYS = ("condition", "action")


def build_planner_prompt(requirement: dict[str, Any]) -> str:
    """Build a prompt that passes only the validated requirements to Qwen."""
    requirement = validate_requirements(requirement)
    return f"""
You are a planner for a safe mobile-robot navigation system.

Use only the validated requirements below. Do not infer a different goal,
extra actions, sensors, or capabilities.

Return one JSON object with exactly these keys:
- strategy: a concise string describing the navigation strategy.
- decisions: a non-empty list of objects. Each object must have exactly
  condition (string) and action (one of FORWARD, LEFT, RIGHT, STOP).
- stop_condition: a concise string explaining when the robot must stop.

The plan must prefer the direction of the goal when it is safe, never choose a
blocked direction, and choose STOP when the goal has been reached or no safe
direction remains. Return JSON only, without Markdown fences or explanations.

Validated requirements:
---
{json.dumps(requirement, indent=2)}
---
""".strip()


def validate_plan(data: Any) -> dict[str, Any]:
    """Validate and normalize the Planner Agent's JSON output."""
    if not isinstance(data, dict):
        raise ValueError("Plan must be a JSON object")

    actual_keys = set(data)
    expected_keys = set(PLAN_KEYS)
    missing = expected_keys - actual_keys
    extra = actual_keys - expected_keys
    if missing:
        raise ValueError(f"Missing plan keys: {sorted(missing)}")
    if extra:
        raise ValueError(f"Unexpected plan keys: {sorted(extra)}")

    strategy = data["strategy"]
    stop_condition = data["stop_condition"]
    if not isinstance(strategy, str) or not strategy.strip():
        raise ValueError("strategy must be a non-empty string")
    if not isinstance(stop_condition, str) or not stop_condition.strip():
        raise ValueError("stop_condition must be a non-empty string")

    decisions = data["decisions"]
    if not isinstance(decisions, list) or not decisions:
        raise ValueError("decisions must be a non-empty list")

    normalized_decisions: list[dict[str, str]] = []
    for index, decision in enumerate(decisions):
        if not isinstance(decision, dict):
            raise ValueError(f"decisions[{index}] must be an object")
        if set(decision) != set(DECISION_KEYS):
            raise ValueError(
                f"decisions[{index}] must contain exactly {list(DECISION_KEYS)!r}"
            )
        condition = decision["condition"]
        action = decision["action"]
        if not isinstance(condition, str) or not condition.strip():
            raise ValueError(f"decisions[{index}].condition must be non-empty")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(
                f"decisions[{index}].action must be one of {ALLOWED_ACTIONS!r}"
            )
        normalized_decisions.append(
            {"condition": condition.strip(), "action": action}
        )

    if not any(decision["action"] == "STOP" for decision in normalized_decisions):
        raise ValueError("decisions must include a STOP action")

    return {
        "strategy": strategy.strip(),
        "decisions": normalized_decisions,
        "stop_condition": stop_condition.strip(),
    }


def run_planner(requirement: dict[str, Any]) -> dict[str, Any]:
    """Ask Qwen for a plan, parse it, validate it, and return it."""
    validated_requirement = validate_requirements(requirement)
    raw_response = ask_qwen(
        build_planner_prompt(validated_requirement),
        json_mode=True,
        system_prompt=(
            "You are a careful navigation planner. Follow the requested JSON "
            "schema exactly and preserve all safety constraints."
        ),
    )
    return validate_plan(_extract_json(raw_response))


__all__ = [
    "DECISION_KEYS",
    "PLAN_KEYS",
    "build_planner_prompt",
    "run_planner",
    "validate_plan",
]
