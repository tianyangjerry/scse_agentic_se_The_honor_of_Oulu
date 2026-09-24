"""Pipeline smoke test: run Developer and save the generated module."""

from __future__ import annotations

import json
from pathlib import Path

from developer_agent import run_developer


ROOT = Path(__file__).resolve().parent


def test_developer_smoke() -> None:
    plan_path = ROOT / "artifacts" / "plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    code = run_developer(plan)
    output_paths = (
        ROOT / "artifacts" / "navigation_logic.py",
        ROOT / "generated" / "navigation_logic.py",
    )
    for output in output_paths:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(code, encoding="utf-8")
    print(f"Developer output ({output_paths[-1]}):\n{code}")


if __name__ == "__main__":
    test_developer_smoke()
