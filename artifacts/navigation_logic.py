def decide_next_move(state):
    if state.get("goal_ahead") and not (state.get("front_blocked", True)):
        return "FORWARD"
    if state.get("goal_on_left") and not (state.get("left_blocked", True)):
        return "LEFT"
    if state.get("goal_on_right") and not (state.get("right_blocked", True)):
        return "RIGHT"
    if not state.get("front_blocked", True):
        return "FORWARD"
    if not state.get("left_blocked", True):
        return "LEFT"
    if not state.get("right_blocked", True):
        return "RIGHT"
    return "STOP"
