"""Run the Developer Agent and save validated navigation code."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from developer_agent import run_developer


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plan",
        type=Path,
        default=Path(__file__).with_name("artifacts") / "plan.json",
        help="Path to the validated plan JSON",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("generated") / "navigation_logic.py",
        help="Path for the generated navigation module",
    )
    args = parser.parse_args()

    plan: Any = json.loads(args.plan.read_text(encoding="utf-8"))
    code = run_developer(plan)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(code, encoding="utf-8")
    print(f"Saved validated navigation code to {args.output}")


if __name__ == "__main__":
    main()
