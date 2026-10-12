"""Generated tests for the navigation contract."""

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
