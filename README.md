# The honor of Oulu - Agentic Software Engineering

Suggested GitHub repository name: `scse_agentic_se_The_honor_of_Oulu`

## Pipeline

- `brief_to_req.py` asks Qwen to produce the readable requirements in `robot_requirements.txt`.
- `analyst_agent.py` asks Qwen for the strict JSON object and validates its schema.
- `run_analyst.py` runs the analyst and writes `artifacts/requirements.json`.
- `planner_agent.py` converts the validated requirements into a navigation plan.
- `run_planner.py` runs the planner and writes `artifacts/plan.json`.
- `developer_agent.py` converts the plan into validated Python navigation code.
- `run_developer.py` runs the developer and writes `navigation_logic.py`.
- `robot_requirements.txt` is the readable requirements artifact.
- `artifacts/requirements.json` is the validated JSON artifact.
- `artifacts/plan.json` is the validated planner artifact.

The agents are intentionally isolated: Planner receives only the validated
requirements artifact, and Developer receives only the validated plan artifact.

## Run with Ollama and Qwen

Make sure Ollama is running and the model is installed:

```powershell
ollama pull qwen2.5:3b
python brief_to_req.py
python run_analyst.py
python run_planner.py
python run_developer.py
```

The scripts call `http://127.0.0.1:11434/api/chat` directly, so no Python
client package or cloud API key is required. Optional environment variables are
`OLLAMA_HOST`, `OLLAMA_MODEL`, and `OLLAMA_TIMEOUT`.

The planner and developer scripts support custom paths, for example:

```powershell
python run_planner.py --requirements artifacts/requirements.json --output artifacts/plan.json
python run_developer.py --plan artifacts/plan.json --output navigation_logic.py
```
