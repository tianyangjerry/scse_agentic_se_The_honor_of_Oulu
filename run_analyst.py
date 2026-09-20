"""Run the analyst agent and save validated requirements as JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from analyst_agent import run_analyst


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--brief",
        type=Path,
        default=Path(__file__).with_name("brief.txt"),
        help="Path to the human-language brief",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(__file__).with_name("artifacts") / "requirements.json",
        help="Path for the validated requirements JSON",
    )
    args = parser.parse_args()

    requirements = run_analyst(args.brief.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as output_file:
        json.dump(requirements, output_file, indent=2)
        output_file.write("\n")
    print(f"Saved validated requirements to {args.output}")


if __name__ == "__main__":
    main()
