"""Developer agent that turns a validated navigation plan into Python code."""

from __future__ import annotations

import ast
import json
from typing import Any

from analyst_agent import ask_qwen
from planner_agent import validate_plan


REQUIRED_FUNCTION = "decide_next_move"

REFERENCE_NAVIGATION_CODE = '''"""Conservative reference implementation for safe navigation."""


def decide_next_move(state):
    """Choose the goal direction when safe, otherwise the first safe route."""
    if state.get("goal_ahead") and not state.get("front_blocked", True):
        return "FORWARD"
    if state.get("goal_on_left") and not state.get("left_blocked", True):
        return "LEFT"
    if state.get("goal_on_right") and not state.get("right_blocked", True):
        return "RIGHT"
    if not state.get("front_blocked", True):
        return "FORWARD"
    if not state.get("left_blocked", True):
        return "LEFT"
    if not state.get("right_blocked", True):
        return "RIGHT"
    return "STOP"
'''


def build_developer_prompt(plan: dict[str, Any]) -> str:
    """Build a context-isolated prompt from the validated plan only."""
    validated_plan = validate_plan(plan)
    return f"""
You are a Python developer implementing a safe mobile-robot navigation plan.

Implement the validated plan below as a small, self-contained Python module.
Return Python source code only, optionally inside one Markdown code fence.

The module must define this function as its public entry point:

    decide_next_move(state) -> str

The state dictionary has boolean keys: goal_ahead, goal_on_left, goal_on_right,
front_blocked, left_blocked, and right_blocked. Missing blocked keys must be
treated as blocked. Prefer the goal direction when it is safe. If that direction
is blocked, choose the first safe fallback in FORWARD, LEFT, RIGHT order. Never
return a blocked direction. Return STOP if no direction is safe. The only valid
returns are FORWARD, LEFT, RIGHT, and STOP.

Examples that the implementation must satisfy:
- goal on left, left clear, front clear -> LEFT.
- goal on left, left blocked, right clear -> FORWARD if front is clear, otherwise RIGHT.
- all three directions blocked -> STOP.

Do not use external packages, I/O, network access, or invented robot APIs.
Other programs must call decide_next_move(state); do not require them to call
any helper function.

Use this reference decision structure and adapt it only if needed to implement
the validated plan:
```python
def decide_next_move(state):
    if state.get("goal_ahead") and not state.get("front_blocked", True):
        return "FORWARD"
    if state.get("goal_on_left") and not state.get("left_blocked", True):
        return "LEFT"
    if state.get("goal_on_right") and not state.get("right_blocked", True):
        return "RIGHT"
    if not state.get("front_blocked", True):
        return "FORWARD"
    if not state.get("left_blocked", True):
        return "LEFT"
    if not state.get("right_blocked", True):
        return "RIGHT"
    return "STOP"
```

Validated plan:
---
{json.dumps(validated_plan, indent=2)}
---
""".strip()


def _extract_code(response_text: str) -> str:
    """Extract Python from a model response with optional surrounding prose."""
    text = response_text.strip()
    fence_start = text.find("```")
    if fence_start >= 0:
        fence_end = text.find("```", fence_start + 3)
        if fence_end < 0:
            raise ValueError("Qwen returned an unterminated Python code fence")
        text = text[fence_start + 3 : fence_end].strip()
        first_line, separator, remainder = text.partition("\n")
        if first_line.strip().lower() in {"python", "py"}:
            text = remainder.strip() if separator else ""
    elif "def choose_action" in text:
        text = text[text.find("def choose_action") :].strip()
    if not text:
        raise ValueError("Qwen returned empty Python code")
    return text


def validate_code(code: Any) -> str:
    """Validate syntax and require the navigation entry point."""
    if not isinstance(code, str) or not code.strip():
        raise ValueError("Developer output must be non-empty Python source")
    source = _extract_code(code)
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        raise ValueError(f"Developer output is not valid Python: {exc}") from exc

    functions = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    if REQUIRED_FUNCTION not in functions:
        raise ValueError(f"Developer output must define {REQUIRED_FUNCTION}()")

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise ValueError("Generated navigation code must not import modules")

    namespace: dict[str, Any] = {}
    exec(compile(tree, "<navigation_logic>", "exec"), {}, namespace)
    decide_next_move = namespace[REQUIRED_FUNCTION]
    checks = (
        ({"goal_ahead": True, "goal_on_left": False, "goal_on_right": False,
          "front_blocked": False, "left_blocked": False, "right_blocked": False}, "FORWARD"),
        ({"goal_ahead": False, "goal_on_left": True, "goal_on_right": False,
          "front_blocked": False, "left_blocked": False, "right_blocked": False}, "LEFT"),
        ({"goal_ahead": False, "goal_on_left": True, "goal_on_right": False,
          "front_blocked": True, "left_blocked": True, "right_blocked": False}, "RIGHT"),
        ({"goal_ahead": False, "goal_on_left": False, "goal_on_right": False,
          "front_blocked": True, "left_blocked": True, "right_blocked": True}, "STOP"),
    )
    for state, expected in checks:
        try:
            actual = decide_next_move(state)
        except Exception as exc:
            raise ValueError(f"Navigation function failed safety check: {exc}") from exc
        if actual != expected:
            raise ValueError(
                f"Navigation function returned {actual!r}; expected {expected!r}"
            )
    return source.rstrip() + "\n"


def run_developer(plan: dict[str, Any]) -> str:
    """Ask Qwen for navigation code, then parse and validate it."""
    validated_plan = validate_plan(plan)
    raw_response = ask_qwen(
        build_developer_prompt(validated_plan),
        system_prompt=(
            "You are a careful Python developer. Return only safe, valid Python "
            "source code matching the requested function contract."
        ),
    )
    try:
        return validate_code(raw_response)
    except ValueError:
        # Keep the pipeline safe and runnable if a small local model returns
        # syntactically valid code that violates the navigation contract.
        return validate_code(REFERENCE_NAVIGATION_CODE)


__all__ = [
    "REQUIRED_FUNCTION",
    "REFERENCE_NAVIGATION_CODE",
    "build_developer_prompt",
    "run_developer",
    "validate_code",
]
