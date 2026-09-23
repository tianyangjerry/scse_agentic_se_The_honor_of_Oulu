"""Run the Planner Agent and save a validated navigation plan."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from planner_agent import run_planner


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--requirements",
        type=Path,
        default=Path(__file__).with_name("artifacts") / "requirements.json",
        help="Path to the validated requirements JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("artifacts") / "plan.json",
        help="Path for the validated plan JSON",
    )
    args = parser.parse_args()

    requirement: Any = json.loads(args.requirements.read_text(encoding="utf-8"))
    plan = run_planner(requirement)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    print(f"Saved validated plan to {args.output}")


if __name__ == "__main__":
    main()
