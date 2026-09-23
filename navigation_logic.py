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
