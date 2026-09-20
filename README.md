# The honor of Oulu - Requirements Engineering

Suggested GitHub repository name: `scse_agentic_se_The_honor_of_Oulu`

## Files

- `brief_to_req.py` asks Qwen to produce the readable requirements in `robot_requirements.txt`.
- `analyst_agent.py` asks Qwen for the strict JSON object and validates its schema.
- `run_analyst.py` runs the analyst and writes `artifacts/requirements.json`.
- `robot_requirements.txt` is the readable requirements artifact.
- `artifacts/requirements.json` is the validated JSON artifact.

## Run with Ollama and Qwen

Make sure Ollama is running and the model is installed:

```powershell
ollama pull qwen2.5:3b
python brief_to_req.py
python run_analyst.py
```

The scripts call `http://127.0.0.1:11434/api/chat` directly, so no Python
client package or cloud API key is required. Optional environment variables are
`OLLAMA_HOST`, `OLLAMA_MODEL`, and `OLLAMA_TIMEOUT`.
