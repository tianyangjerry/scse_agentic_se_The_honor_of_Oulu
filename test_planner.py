"""Pipeline smoke test: run Planner on artifacts/requirements.json."""

from __future__ import annotations

import json
from pathlib import Path

from planner_agent import run_planner


ROOT = Path(__file__).resolve().parent


def test_planner_smoke() -> None:
    requirements_path = ROOT / "artifacts" / "requirements.json"
    requirements = json.loads(requirements_path.read_text(encoding="utf-8"))
    plan = run_planner(requirements)
    output = ROOT / "artifacts" / "plan.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"Planner output ({output}):\n{json.dumps(plan, indent=2)}")


if __name__ == "__main__":
    test_planner_smoke()
