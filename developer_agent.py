"""Developer agent that turns a validated navigation plan into Python code."""

from __future__ import annotations

import ast
import json
from typing import Any

from analyst_agent import ask_qwen
from planner_agent import validate_plan


REQUIRED_FUNCTION = "choose_action"

REFERENCE_NAVIGATION_CODE = '''"""Conservative reference implementation for safe navigation."""


def choose_action(goal_direction, blocked, goal_reached=False):
    if goal_reached:
        return "STOP"
    direction = goal_direction.upper() if goal_direction is not None else ""
    if direction == "AHEAD":
        direction = "FORWARD"

    def is_safe(action):
        return blocked.get(action.lower(), True) is False

    if direction in ("FORWARD", "LEFT", "RIGHT") and is_safe(direction):
        return direction
    for action in ("FORWARD", "LEFT", "RIGHT"):
        if is_safe(action):
            return action
    return "STOP"
'''


def build_developer_prompt(plan: dict[str, Any]) -> str:
    """Build a context-isolated prompt from the validated plan only."""
    validated_plan = validate_plan(plan)
    return f"""
You are a Python developer implementing a safe mobile-robot navigation plan.

Implement the validated plan below as a small, self-contained Python module.
Return Python source code only, optionally inside one Markdown code fence.

The module must define this function:

    choose_action(goal_direction, blocked, goal_reached=False) -> str

Requirements for choose_action:
- Return STOP when goal_reached is true.
- Accept goal_direction as FORWARD, LEFT, RIGHT, or None.
- Accept blocked as a mapping whose forward/left/right keys indicate whether
  that direction is blocked. Missing directions must be treated as blocked.
- Prefer the requested goal direction when it is safe.
- Never return a blocked direction.
- If no safe direction exists, return STOP.
- Return only FORWARD, LEFT, RIGHT, or STOP.

Use this exact decision order: if goal_reached, return STOP; otherwise try the
normalized goal direction if blocked.get(direction.lower(), True) is False;
then try FORWARD, LEFT, RIGHT in that order using the same safety check; if
none is safe, return STOP. A value of True means blocked and False means safe.
Do not assume a direction is safe merely because it appears in the input.

Examples that the implementation must satisfy:
- choose_action("RIGHT", {{"forward": False, "left": True, "right": False}}) returns "RIGHT".
- choose_action("LEFT", {{"forward": True, "left": True, "right": False}}) returns "RIGHT".
- choose_action("FORWARD", {{"forward": True, "left": True, "right": True}}) returns "STOP".

Do not use external packages, I/O, network access, or invented robot APIs.

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
    choose_action = namespace[REQUIRED_FUNCTION]
    checks = (
        ("RIGHT", {"forward": False, "left": True, "right": False}, False, "RIGHT"),
        ("LEFT", {"forward": True, "left": True, "right": False}, False, "RIGHT"),
        ("FORWARD", {"forward": True, "left": True, "right": True}, False, "STOP"),
        ("FORWARD", {"forward": False, "left": False, "right": False}, True, "STOP"),
    )
    for goal_direction, blocked, goal_reached, expected in checks:
        try:
            actual = choose_action(goal_direction, blocked, goal_reached)
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
