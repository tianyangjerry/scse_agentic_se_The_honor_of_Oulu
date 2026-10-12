"""Reviewer for measured IR-SIM benchmark quality."""

from __future__ import annotations

import json
from typing import Any

from analyst_agent import _extract_json, ask_qwen


REVIEW_KEYS = (
    "issue",
    "likely_cause",
    "recommendation",
    "safety_passed",
    "goal_completion_passed",
    "efficiency_passed",
    "needs_revision",
)
BOOLEAN_KEYS = (
    "safety_passed",
    "goal_completion_passed",
    "efficiency_passed",
    "needs_revision",
)


def build_benchmark_review_prompt(report: dict[str, Any], deterministic: dict[str, Any]) -> str:
    return f"""
You are reviewing an IR-SIM benchmark report. Return JSON only with exactly
these keys: issue, likely_cause, recommendation, safety_passed,
goal_completion_passed, efficiency_passed, needs_revision.
The first three values are strings and the last four values are booleans.
Preserve the measured boolean decisions in the deterministic assessment below.

Benchmark report:
{json.dumps(report, indent=2)}

Deterministic assessment:
{json.dumps(deterministic, indent=2)}
""".strip()


def validate_benchmark_review(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != set(REVIEW_KEYS):
        raise ValueError(f"Benchmark review must contain exactly {list(REVIEW_KEYS)!r}")
    for key in REVIEW_KEYS[:3]:
        if not isinstance(data[key], str):
            raise ValueError(f"{key} must be a string")
    for key in BOOLEAN_KEYS:
        if not isinstance(data[key], bool):
            raise ValueError(f"{key} must be a boolean")
    return data


def deterministic_benchmark_review(report: dict[str, Any]) -> dict[str, Any]:
    """Compute pass/fail flags directly from measured benchmark fields."""
    total = report.get("total_worlds")
    success_rate = report.get("success_rate")
    efficiency_rate = report.get("efficiency_rate")
    inefficient = report.get("inefficient_success_worlds")
    results = report.get("results")

    valid_metrics = all(
        isinstance(value, (int, float))
        for value in (total, success_rate, efficiency_rate, inefficient)
    ) and isinstance(results, list)
    if not valid_metrics:
        safety_passed = goal_passed = efficiency_passed = False
    else:
        safety_passed = all(
            not (item.get("collision_or_done") and not item.get("reached_goal"))
            for item in results
            if isinstance(item, dict)
        )
        goal_passed = total > 0 and success_rate >= 1.0
        efficiency_passed = inefficient == 0 and efficiency_rate >= 1.0

    issues = []
    if not safety_passed:
        issues.append("Unsafe benchmark behavior detected")
    if not goal_passed:
        issues.append("Goal completion failure")
    if not efficiency_passed:
        issues.append("Successful but inefficient navigation")
    issue = "; ".join(issues) if issues else "No benchmark issues detected"
    return {
        "issue": issue,
        "likely_cause": (
            "One or more measured worlds did not satisfy the safety, completion, "
            "or efficiency thresholds."
            if issues
            else "All measured worlds satisfied the benchmark thresholds."
        ),
        "recommendation": (
            "Review failed worlds, revise decide_next_move, and rerun the full pipeline."
            if issues
            else "Keep the navigation logic and record the successful benchmark."
        ),
        "safety_passed": safety_passed,
        "goal_completion_passed": goal_passed,
        "efficiency_passed": efficiency_passed,
        "needs_revision": bool(issues),
    }


def run_benchmark_reviewer(report: dict[str, Any]) -> dict[str, Any]:
    deterministic = deterministic_benchmark_review(report)
    try:
        review = validate_benchmark_review(
            _extract_json(
                ask_qwen(
                    build_benchmark_review_prompt(report, deterministic),
                    json_mode=True,
                    system_prompt="Return only the requested benchmark review JSON.",
                )
            )
        )
        for key in BOOLEAN_KEYS:
            review[key] = deterministic[key]
        return review
    except (RuntimeError, ValueError):
        return deterministic


__all__ = [
    "REVIEW_KEYS",
    "build_benchmark_review_prompt",
    "deterministic_benchmark_review",
    "run_benchmark_reviewer",
    "validate_benchmark_review",
]
