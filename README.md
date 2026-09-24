# SCSE '26 Robot Navigation Agent Pipeline

This repository combines the Requirements Engineering, Plan and Develop, and
Testing course projects into one runnable robot-navigation pipeline.

## Pipeline artifacts

```text
brief.txt
  -> Analyst Agent -> artifacts/requirements.json
  -> Planner Agent -> artifacts/plan.json
  -> Developer Agent -> generated/navigation_logic.py
  -> behavior tests -> decide_next_move(state)
```

The Analyst converts the original brief into validated requirements. The
Planner receives only that requirements artifact. The Developer receives only
the validated plan and generates a module whose public function is
`decide_next_move(state)`. The state dictionary contains `goal_ahead`,
`goal_on_left`, `goal_on_right`, `front_blocked`, `left_blocked`, and
`right_blocked` booleans. Safe goal directions take priority; if the goal
direction is blocked, the fallback order is FORWARD, LEFT, RIGHT. Missing
blocked-state values are treated as blocked, and the robot returns STOP when
no safe direction remains.

## Run the pipeline smoke tests

Install and start Ollama, then make sure Qwen is available:

```powershell
ollama pull qwen2.5:3b
python test_analyst.py
python test_planner.py
python test_developer.py
```

Each smoke test runs its real agent, lets the agent validate its output, saves
the resulting artifact, and displays it. Run the tests in order because each
stage consumes the preceding stage's artifact.

The Developer smoke test saves the same validated module to
`artifacts/navigation_logic.py` (the stage artifact) and
`generated/navigation_logic.py` (the module used by behavior tests).

The agents call Ollama's local HTTP API. Optional environment variables are
`OLLAMA_HOST`, `OLLAMA_MODEL`, and `OLLAMA_TIMEOUT`.

## Run behavior tests

After generating `generated/navigation_logic.py`, run:

```powershell
python -m unittest -v test_generated_navigation_logic.py
```

The behavior suite checks all 64 combinations of the three goal indicators and
three blocked-path indicators. It also checks goal preference, legal actions,
obstacle avoidance, and stopping when every direction is blocked.

To demonstrate bug detection for the course exercise, temporarily change a
goal-direction decision in `generated/navigation_logic.py` to return an
incorrect action and rerun the behavior suite. At least one test must fail.
Restore the correct implementation and rerun the suite; all tests should pass.

## Files

- `analyst_agent.py`, `run_analyst.py`, `brief_to_req.py`: requirements stage.
- `planner_agent.py`, `run_planner.py`: planning stage.
- `developer_agent.py`, `run_developer.py`: code-generation stage.
- `test_analyst.py`, `test_planner.py`, `test_developer.py`: pipeline smoke tests.
- `test_generated_navigation_logic.py`: navigation behavior tests.
- `artifacts/requirements.json`, `artifacts/plan.json`,
  `artifacts/navigation_logic.py`: validated pipeline data and generated code.
- `generated/navigation_logic.py`: generated robot navigation module.
