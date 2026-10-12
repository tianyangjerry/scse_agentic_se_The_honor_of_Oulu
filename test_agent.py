"""Test Agent that asks Qwen for pytest-style navigation tests."""

from __future__ import annotations

import ast
import json
from typing import Any

from analyst_agent import ask_qwen
from planner_agent import validate_plan
from analyst_agent import validate_requirements


FALLBACK_TEST_CODE = '''"""Generated tests for the navigation contract."""

from generated.navigation_logic import decide_next_move


def test_goal_direction_is_preferred_when_safe():
    assert decide_next_move({
        "goal_ahead": True, "goal_on_left": False, "goal_on_right": False,
        "front_blocked": False, "left_blocked": False, "right_blocked": False,
    }) == "FORWARD"
    assert decide_next_move({
        "goal_ahead": False, "goal_on_left": True, "goal_on_right": False,
        "front_blocked": False, "left_blocked": False, "right_blocked": False,
    }) == "LEFT"


def test_blocked_goal_uses_safe_fallback():
    state = {
        "goal_ahead": True, "goal_on_left": False, "goal_on_right": False,
        "front_blocked": True, "left_blocked": False, "right_blocked": False,
    }
    assert decide_next_move(state) == "LEFT"


def test_all_directions_blocked_stops():
    state = {
        "goal_ahead": True, "goal_on_left": True, "goal_on_right": True,
        "front_blocked": True, "left_blocked": True, "right_blocked": True,
    }
    assert decide_next_move(state) == "STOP"
'''


def build_test_prompt(requirements: dict[str, Any], plan: dict[str, Any]) -> str:
    requirements = validate_requirements(requirements)
    plan = validate_plan(plan)
    return f"""
You are a Python test engineer. Generate pytest-style tests for a module that
exports decide_next_move(state). Return Python source code only: no Markdown
fences, no explanation, and no file-writing code.

The tests must cover safe goal preference, blocked goal fallback, all blocked
directions returning STOP, and invalid action prevention. Use assertions and
import decide_next_move from generated.navigation_logic.

Requirements:
{json.dumps(requirements, indent=2)}

Plan:
{json.dumps(plan, indent=2)}
""".strip()


def validate_test_code(code: Any) -> str:
    """Validate that Qwen returned executable pytest-style test source."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Test Agent output must be non-empty Python source")
    source = code.strip()
    if "```" in source:
        raise ValueError("Test Agent output must not contain Markdown fences")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Generated tests are not valid Python: {exc}") from exc
    function_names = {
        node.name for node in tree.body if isinstance(node, ast.FunctionDef)
    }
    if not any(name.startswith("test_") for name in function_names):
        raise ValueError("Generated tests must define at least one test_* function")
    required_state_keys = (
        "goal_ahead",
        "goal_on_left",
        "goal_on_right",
        "front_blocked",
        "left_blocked",
        "right_blocked",
    )
    if "decide_next_move" not in source or "assert" not in source:
        raise ValueError("Generated tests must call decide_next_move and assert results")
    missing_keys = [key for key in required_state_keys if key not in source]
    if missing_keys:
        raise ValueError(f"Generated tests omit state keys: {missing_keys}")
    compile(tree, "<generated_tests>", "exec")
    return source + "\n"


def run_test_agent(requirements: dict[str, Any], plan: dict[str, Any]) -> str:
    """Generate tests with Qwen, falling back to a safe deterministic suite."""
    try:
        raw = ask_qwen(
            build_test_prompt(requirements, plan),
            system_prompt=(
                "You are a careful test engineer. Return only valid pytest-style "
                "Python source without Markdown fences."
            ),
        )
        return validate_test_code(raw)
    except (RuntimeError, ValueError):
        return validate_test_code(FALLBACK_TEST_CODE)


__all__ = [
    "FALLBACK_TEST_CODE",
    "build_test_prompt",
    "run_test_agent",
    "validate_test_code",
]
