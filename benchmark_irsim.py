"""Run the supplied IR-SIM worlds and aggregate performance metrics."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parent
DEFAULT_WORLDS = (
    "world_easy.yaml",
    "world_medium.yaml",
    "world_hard.yaml",
    "world_custom.yaml",
)


def run_world(world_file: Path, timeout: int = 180) -> dict[str, Any]:
    """Run one world headlessly and return its report or an error result."""
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    command = [sys.executable, str(ROOT / "test_irsim_with_agent.py"), str(world_file)]
    try:
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return {
            "world": world_file.name,
            "reached_goal": False,
            "collision_or_done": True,
            "steps_taken": None,
            "efficiency_status": "failed",
            "error": f"Timed out after {timeout} seconds: {exc}",
        }

    report_path = ROOT / "artifacts" / "irsim_report.json"
    if completed.returncode == 0 and report_path.exists():
        report = json.loads(report_path.read_text(encoding="utf-8"))
        report["world"] = world_file.name
        report["returncode"] = completed.returncode
        return report

    return {
        "world": world_file.name,
        "reached_goal": False,
        "collision_or_done": True,
        "steps_taken": None,
        "efficiency_status": "failed",
        "returncode": completed.returncode,
        "error": (completed.stderr or completed.stdout)[-2000:],
    }


def build_benchmark_report(results: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(results)
    reached = sum(bool(item.get("reached_goal")) for item in results)
    efficient = sum(item.get("efficiency_status") == "efficient" for item in results)
    inefficient = sum(
        item.get("efficiency_status") == "acceptable_but_inefficient"
        for item in results
    )
    failed = total - reached
    steps = [item["steps_taken"] for item in results if item.get("steps_taken") is not None]
    safety_passed = all(
        not (item.get("collision_or_done") and not item.get("reached_goal"))
        for item in results
    )
    return {
        "total_worlds": total,
        "goals_reached": reached,
        "success_rate": reached / total if total else 0.0,
        "efficient_worlds": efficient,
        "inefficient_success_worlds": inefficient,
        "failed_worlds": failed,
        "efficiency_rate": efficient / total if total else 0.0,
        "average_steps_taken": sum(steps) / len(steps) if steps else 0.0,
        "safety_passed": safety_passed,
        "results": results,
    }


def run_benchmark(
    world_files: Iterable[Path] | None = None,
    output: Path | None = None,
) -> dict[str, Any]:
    worlds = list(world_files or (ROOT / "irsim_worlds" / name for name in DEFAULT_WORLDS))
    results = [run_world(world) for world in worlds]
    report = build_benchmark_report(results)
    output = output or ROOT / "artifacts" / "irsim_benchmark_report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> None:
    report = run_benchmark()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
