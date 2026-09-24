"""Pipeline smoke test: run Analyst on the original brief artifact."""

from __future__ import annotations

import json
from pathlib import Path

from analyst_agent import run_analyst


ROOT = Path(__file__).resolve().parent


def test_analyst_smoke() -> None:
    brief = (ROOT / "brief.txt").read_text(encoding="utf-8")
    requirements = run_analyst(brief)
    output = ROOT / "artifacts" / "requirements.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(requirements, indent=2) + "\n", encoding="utf-8")
    print(f"Analyst output ({output}):\n{json.dumps(requirements, indent=2)}")


if __name__ == "__main__":
    test_analyst_smoke()
