"""Offline tests for the Developer Agent's own output validation."""

from __future__ import annotations

import unittest

from developer_agent import REFERENCE_NAVIGATION_CODE, validate_code


HELPER_CODE = '''
SAFE_FALLBACK_ORDER = (
    ("front_blocked", "FORWARD"),
    ("left_blocked", "LEFT"),
    ("right_blocked", "RIGHT"),
)


def _is_clear(state, key):
    return not state.get(key, True)


def decide_next_move(state):
    if state.get("goal_ahead") and _is_clear(state, "front_blocked"):
        return "FORWARD"
    if state.get("goal_on_left") and _is_clear(state, "left_blocked"):
        return "LEFT"
    if state.get("goal_on_right") and _is_clear(state, "right_blocked"):
        return "RIGHT"
    for blocked_key, action in SAFE_FALLBACK_ORDER:
        if _is_clear(state, blocked_key):
            return action
    return "STOP"
'''


class DeveloperValidationTests(unittest.TestCase):
    def test_accepts_reference_code(self) -> None:
        self.assertIn("def decide_next_move", validate_code(REFERENCE_NAVIGATION_CODE))

    def test_accepts_code_after_unfenced_prose(self) -> None:
        source = validate_code("Here is the implementation:\n" + HELPER_CODE)
        self.assertTrue(source.startswith("SAFE_FALLBACK_ORDER"))
        self.assertNotIn("Here is the implementation", source)

    def test_accepts_helpers_and_module_constants(self) -> None:
        source = validate_code(f"```python\n{HELPER_CODE}\n```")
        self.assertIn("def _is_clear", source)

    def test_rejects_wrong_goal_direction(self) -> None:
        buggy = HELPER_CODE.replace(
            'if state.get("goal_on_left") and _is_clear(state, "left_blocked"):\n'
            '        return "LEFT"',
            'if state.get("goal_on_left") and _is_clear(state, "left_blocked"):\n'
            '        return "RIGHT"',
        )
        self.assertNotEqual(buggy, HELPER_CODE)
        with self.assertRaises(ValueError):
            validate_code(buggy)

    def test_rejects_missing_entry_point(self) -> None:
        with self.assertRaises(ValueError):
            validate_code("def choose_action(state):\n    return 'STOP'\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
