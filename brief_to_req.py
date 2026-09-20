"""Ask Qwen to convert the human brief into readable software requirements."""

from __future__ import annotations

import argparse
from pathlib import Path

from analyst_agent import ask_qwen


def build_requirements_prompt(brief_text: str) -> str:
    return f"""
Act as a professional software requirements engineer. Convert the following
human-language brief into a concise, testable list of functional requirements
for a mobile robot navigation component.

Include requirements for goal preference, blocked directions, stopping when no
safe direction exists, and the permitted navigation actions. Preserve the
meaning of the brief, do not invent sensors or features, and write clear
numbered requirements in plain text. Do not output JSON and do not add a
preface.

Brief:
---
{brief_text.strip()}
---
""".strip()


def generate_requirements_text(brief_text: str) -> str:
    """Return the raw plain-text requirements produced by Qwen."""
    response = ask_qwen(build_requirements_prompt(brief_text))
    if not response.strip():
        raise ValueError("Qwen returned an empty requirements response")
    return response.strip()


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
        default=Path(__file__).with_name("robot_requirements.txt"),
        help="Path for Qwen's plain-text requirements",
    )
    args = parser.parse_args()

    brief_text = args.brief.read_text(encoding="utf-8")
    requirements = generate_requirements_text(brief_text)
    args.output.write_text(requirements + "\n", encoding="utf-8")
    print(f"Saved Qwen requirements to {args.output}")


if __name__ == "__main__":
    main()
