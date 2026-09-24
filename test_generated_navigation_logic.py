"""Behavioral tests for the generated public navigation entry point."""

from __future__ import annotations

import itertools
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "generated"))
from navigation_logic import decide_next_move  # noqa: E402


def expected_move(state: dict[str, bool]) -> str:
    """Independent specification used to calculate the expected action."""
    goal_priorities = (
        ("goal_ahead", "front_blocked", "FORWARD"),
        ("goal_on_left", "left_blocked", "LEFT"),
        ("goal_on_right", "right_blocked", "RIGHT"),
    )
    for goal_key, blocked_key, action in goal_priorities:
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


class NavigationBehaviorTests(unittest.TestCase):
    def test_all_64_sensor_state_combinations(self) -> None:
        keys = (
            "goal_ahead",
            "goal_on_left",
            "goal_on_right",
            "front_blocked",
            "left_blocked",
            "right_blocked",
        )
        for values in itertools.product((False, True), repeat=len(keys)):
            state = dict(zip(keys, values, strict=True))
            with self.subTest(state=state):
                action = decide_next_move(state)
                self.assertEqual(action, expected_move(state))
                self.assertIn(action, {"FORWARD", "LEFT", "RIGHT", "STOP"})
                if action != "STOP":
                    blocked_key = {
                        "FORWARD": "front_blocked",
                        "LEFT": "left_blocked",
                        "RIGHT": "right_blocked",
                    }[action]
                    self.assertFalse(state[blocked_key])

    def test_goal_direction_is_preferred_when_safe(self) -> None:
        states = (
            ({"goal_ahead": True}, "FORWARD", "front_blocked"),
            ({"goal_on_left": True}, "LEFT", "left_blocked"),
            ({"goal_on_right": True}, "RIGHT", "right_blocked"),
        )
        for goal, expected, blocked_key in states:
            state = {
                "goal_ahead": False,
                "goal_on_left": False,
                "goal_on_right": False,
                "front_blocked": False,
                "left_blocked": False,
                "right_blocked": False,
                **goal,
            }
            with self.subTest(goal=goal):
                self.assertFalse(state[blocked_key])
                self.assertEqual(decide_next_move(state), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
