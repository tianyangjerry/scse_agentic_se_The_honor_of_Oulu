"""Deterministic simulation for every boolean navigation state."""

from __future__ import annotations

import itertools
import json
from pathlib import Path
from typing import Callable, Any


ACTION_TO_BLOCKED_KEY = {
    "FORWARD": "front_blocked",
    "LEFT": "left_blocked",
    "RIGHT": "right_blocked",
}
VALID_ACTIONS = set(ACTION_TO_BLOCKED_KEY) | {"STOP"}
STATE_KEYS = (
    "goal_ahead",
    "goal_on_left",
    "goal_on_right",
    "front_blocked",
    "left_blocked",
    "right_blocked",
)


def expected_action(state: dict[str, bool]) -> str:
    """Return the independent expected result for the requirements."""
    for goal_key, blocked_key, action in (
        ("goal_ahead", "front_blocked", "FORWARD"),
        ("goal_on_left", "left_blocked", "LEFT"),
        ("goal_on_right", "right_blocked", "RIGHT"),
    ):
        if state[goal_key] and not state[blocked_key]:
            return action
    for blocked_key, action in (
        ("front_blocked", "FORWARD"),
        ("left_blocked", "LEFT"),
        ("right_blocked", "RIGHT"),
    ):
        if not state[blocked_key]:
            return action
    return "STOP"


def all_scenarios() -> list[dict[str, bool]]:
    """Generate all 2^6 combinations of goal and obstacle flags."""
    return [
        dict(zip(STATE_KEYS, values, strict=True))
        for values in itertools.product((False, True), repeat=len(STATE_KEYS))
    ]


def run_simulation(
    decide_next_move: Callable[[dict[str, bool]], str] | None = None,
) -> dict[str, Any]:
    """Run the navigation function against every scenario and summarize it."""
    if decide_next_move is None:
        from generated.navigation_logic import decide_next_move as generated_move

        decide_next_move = generated_move

    results: list[dict[str, Any]] = []
    for index, state in enumerate(all_scenarios(), start=1):
        expected = expected_action(state)
        actual: Any = None
        error = None
        try:
            actual = decide_next_move(state)
        except Exception as exc:  # Report a failed scenario instead of stopping all tests.
            error = f"{type(exc).__name__}: {exc}"

        safety_ok = actual == "STOP" or (
            actual in ACTION_TO_BLOCKED_KEY
            and not state[ACTION_TO_BLOCKED_KEY[actual]]
        )
        passed = actual == expected and actual in VALID_ACTIONS and safety_ok
        results.append(
            {
                "scenario": index,
                "state": state,
                "expected": expected,
                "actual": actual,
                "passed": passed,
                "safety_ok": safety_ok,
                "error": error,
            }
        )

    total = len(results)
    passed_count = sum(result["passed"] for result in results)
    return {
        "total_scenarios": total,
        "passed": passed_count,
        "failed": total - passed_count,
        "success_rate": passed_count / total if total else 0.0,
        "results": results,
    }


def save_simulation_report(report: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    output = Path(__file__).with_name("artifacts") / "simulation_report.json"
    report = run_simulation()
    save_simulation_report(report, output)
    print(json.dumps(report, indent=2))
    print(f"Saved simulation report to {output}")


if __name__ == "__main__":
    main()
