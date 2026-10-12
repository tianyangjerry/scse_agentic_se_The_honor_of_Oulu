"""Reviewer Agent for the deterministic simulation report."""

from __future__ import annotations

import json
from typing import Any

from analyst_agent import _extract_json, ask_qwen


REVIEW_KEYS = ("issue", "likely_cause", "recommendation", "needs_revision")


def build_reviewer_prompt(report: dict[str, Any]) -> str:
    failed_examples = [
        result for result in report.get("results", []) if not result.get("passed")
    ][:5]
    review_input = {
        "total_scenarios": report.get("total_scenarios"),
        "passed": report.get("passed"),
        "failed": report.get("failed"),
        "success_rate": report.get("success_rate"),
        "failed_examples": failed_examples,
    }
    return f"""
You are reviewing a robot navigation simulation report.
Return one JSON object with exactly these keys:
- issue: string
- likely_cause: string
- recommendation: string
- needs_revision: boolean

Set needs_revision to true if any scenario failed or any unsafe action was
observed. Otherwise report that the simulation passed. Return JSON only.

Simulation summary and failed examples:
{json.dumps(review_input, indent=2)}
""".strip()


def validate_review(data: Any) -> dict[str, Any]:
    if not isinstance(data, dict) or set(data) != set(REVIEW_KEYS):
        raise ValueError(f"Review must contain exactly {list(REVIEW_KEYS)!r}")
    for key in REVIEW_KEYS[:3]:
        if not isinstance(data[key], str):
            raise ValueError(f"{key} must be a string")
    if not isinstance(data["needs_revision"], bool):
        raise ValueError("needs_revision must be a boolean")
    return {
        "issue": data["issue"].strip(),
        "likely_cause": data["likely_cause"].strip(),
        "recommendation": data["recommendation"].strip(),
        "needs_revision": data["needs_revision"],
    }


def deterministic_review(report: dict[str, Any]) -> dict[str, Any]:
    failed = int(report.get("failed", 1))
    if failed:
        return {
            "issue": "Simulation scenarios failed",
            "likely_cause": "The navigation function did not satisfy the full decision table.",
            "recommendation": "Revise decide_next_move and rerun the simulation.",
            "needs_revision": True,
        }
    return {
        "issue": "No simulation issues detected",
        "likely_cause": "All tested states matched the navigation requirements.",
        "recommendation": "Proceed to IR-SIM benchmarking.",
        "needs_revision": False,
    }


def run_reviewer(report: dict[str, Any]) -> dict[str, Any]:
    fallback = deterministic_review(report)
    try:
        review = validate_review(
            _extract_json(
                ask_qwen(
                    build_reviewer_prompt(report),
                    json_mode=True,
                    system_prompt="Return only the requested review JSON object.",
                )
            )
        )
        review["needs_revision"] = fallback["needs_revision"]
        return review
    except (RuntimeError, ValueError):
        return fallback


__all__ = [
    "REVIEW_KEYS",
    "build_reviewer_prompt",
    "deterministic_review",
    "run_reviewer",
    "validate_review",
]
