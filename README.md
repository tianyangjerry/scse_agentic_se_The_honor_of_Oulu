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

## Run the complete Integration and Simulation pipeline

Install the declared dependencies into the project environment:

```powershell
uv sync
```

Then run the central orchestrator:

```powershell
.venv\Scripts\python.exe main.py
```

The orchestrator runs the Analyst, Planner, Developer, Test Agent, deterministic
simulation, Reviewer, all four IR-SIM worlds, and the Benchmark Reviewer. It
records every stage in `trace.log` and writes:

- `artifacts/simulation_report.json`
- `artifacts/review.json`
- `artifacts/irsim_benchmark_report.json`
- `artifacts/benchmark_review.json`
- `artifacts/pipeline_summary.json`
- `generated/test_navigation_logic.py`

The four supplied worlds are `world_easy.yaml`, `world_medium.yaml`,
`world_hard.yaml`, and `world_custom.yaml` under `irsim_worlds/`. For a visual
run, use `run_visual.sh` in Bash/WSL or run the Python simulator directly in
PowerShell:

```powershell
$env:MPLBACKEND = "Agg"
.venv\Scripts\python.exe test_irsim_with_agent.py irsim_worlds\world_easy.yaml
```

If the benchmark reviewer reports a measured failure, `main.py` asks the
Developer Agent for one evidence-based revision, updates the generated module,
and reruns the simulation and benchmark.

## Files

- `analyst_agent.py`, `run_analyst.py`, `brief_to_req.py`: requirements stage.
- `planner_agent.py`, `run_planner.py`: planning stage.
- `developer_agent.py`, `run_developer.py`: code-generation stage.
- `test_analyst.py`, `test_planner.py`, `test_developer.py`: pipeline smoke tests.
- `test_generated_navigation_logic.py`: navigation behavior tests.
- `test_developer_validation.py`: offline tests for the Developer Agent's code
  extraction and validation (`python -m unittest -v test_developer_validation.py`).
- `main.py`, `runner.py`: central orchestration and 64-state simulation.
- `test_agent.py`, `reviewer_agent.py`: generated tests and simulation review.
- `benchmark_irsim.py`, `reviewer_benchmark_agent.py`: IR-SIM benchmarking and
  measured benchmark review.
- `test_irsim_with_agent.py`, `run_visual.sh`, `irsim_worlds/`: supplied IR-SIM
  runner, visual launcher, and four simulation worlds.
- `artifacts/requirements.json`, `artifacts/plan.json`,
  `artifacts/navigation_logic.py`: validated pipeline data and generated code.
- `generated/navigation_logic.py`: generated robot navigation module.
