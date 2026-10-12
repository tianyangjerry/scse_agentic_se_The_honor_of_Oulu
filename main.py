"""Central orchestrator for the requirements-to-simulation pipeline."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analyst_agent import run_analyst
from benchmark_irsim import run_benchmark
from developer_agent import run_developer, run_developer_revision
from planner_agent import run_planner
from reviewer_agent import run_reviewer
from reviewer_benchmark_agent import run_benchmark_reviewer
from runner import run_simulation, save_simulation_report
from test_agent import run_test_agent


ROOT = Path(__file__).resolve().parent
ARTIFACTS = ROOT / "artifacts"
GENERATED = ROOT / "generated"
TRACE = ROOT / "trace.log"


def log_event(message: str) -> None:
    """Append one human-readable pipeline event to trace.log and stdout."""
    timestamp = datetime.now(timezone.utc).isoformat()
    line = f"{timestamp} | {message}"
    with TRACE.open("a", encoding="utf-8") as trace_file:
        trace_file.write(line + "\n")
    print(line)


def save_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def run_generated_tests(test_path: Path) -> dict[str, Any]:
    """Run the Test Agent's pytest source and return a compact result."""
    command = [sys.executable, "-m", "pytest", str(test_path), "-q"]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {
        "command": " ".join(command),
        "passed": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def write_navigation_code(code: str) -> None:
    """Keep both the artifact copy and the imported generated copy in sync."""
    for path in (
        ARTIFACTS / "navigation_logic.py",
        GENERATED / "navigation_logic.py",
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(code, encoding="utf-8")


def run_pipeline(skip_irsim: bool = False) -> dict[str, Any]:
    """Run all agents in sequence and optionally perform one revision cycle."""
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    GENERATED.mkdir(parents=True, exist_ok=True)
    log_event("Pipeline started")

    brief = (ROOT / "brief.txt").read_text(encoding="utf-8")
    requirements = run_analyst(brief)
    save_json(ARTIFACTS / "requirements.json", requirements)
    log_event("Analyst Agent created artifacts/requirements.json")

    plan = run_planner(requirements)
    save_json(ARTIFACTS / "plan.json", plan)
    log_event("Planner Agent created artifacts/plan.json")

    navigation_code = run_developer(plan)
    write_navigation_code(navigation_code)
    log_event("Developer Agent created navigation_logic.py")

    generated_tests = run_test_agent(requirements, plan)
    test_path = GENERATED / "test_navigation_logic.py"
    test_path.write_text(generated_tests, encoding="utf-8")
    test_report = run_generated_tests(test_path)
    save_json(ARTIFACTS / "test_agent_report.json", test_report)
    log_event(
        "Test Agent created generated/test_navigation_logic.py "
        f"(passed={test_report['passed']})"
    )

    simulation_report = run_simulation()
    save_simulation_report(simulation_report, ARTIFACTS / "simulation_report.json")
    log_event(
        "Simulation Runner created artifacts/simulation_report.json "
        f"(success_rate={simulation_report['success_rate']:.2f})"
    )

    simulation_review = run_reviewer(simulation_report)
    save_json(ARTIFACTS / "review.json", simulation_review)
    log_event("Reviewer Agent created artifacts/review.json")

    if skip_irsim:
        benchmark_report = {
            "total_worlds": 0,
            "goals_reached": 0,
            "success_rate": 0.0,
            "efficient_worlds": 0,
            "inefficient_success_worlds": 0,
            "failed_worlds": 0,
            "efficiency_rate": 0.0,
            "average_steps_taken": 0.0,
            "safety_passed": False,
            "results": [],
            "skipped": True,
        }
        save_json(ARTIFACTS / "irsim_benchmark_report.json", benchmark_report)
        log_event("IR-SIM benchmark skipped by command-line option")
    else:
        benchmark_report = run_benchmark()
        log_event(
            "IR-SIM benchmark created artifacts/irsim_benchmark_report.json "
            f"(success_rate={benchmark_report['success_rate']:.2f})"
        )

    benchmark_review = run_benchmark_reviewer(benchmark_report)
    save_json(ARTIFACTS / "benchmark_review.json", benchmark_review)
    log_event("Benchmark Reviewer created artifacts/benchmark_review.json")

    revision_performed = False
    if benchmark_review["needs_revision"] and not skip_irsim:
        revision_performed = True
        (ARTIFACTS / "navigation_logic_before_revision.py").write_text(
            navigation_code, encoding="utf-8"
        )
        revised_code = run_developer_revision(
            navigation_code,
            {**simulation_review, "benchmark_review": benchmark_review},
            benchmark_report,
            requirements,
            plan,
        )
        write_navigation_code(revised_code)
        log_event("Developer Agent created a reviewed navigation revision")

        # Re-run the evidence-producing stages after a revision.
        simulation_report = run_simulation()
        save_simulation_report(
            simulation_report, ARTIFACTS / "simulation_report.json"
        )
        simulation_review = run_reviewer(simulation_report)
        save_json(ARTIFACTS / "review.json", simulation_review)
        benchmark_report = run_benchmark()
        benchmark_review = run_benchmark_reviewer(benchmark_report)
        save_json(ARTIFACTS / "benchmark_review.json", benchmark_review)
        log_event("Simulation and IR-SIM benchmark rerun after revision")

    final_summary = {
        "simulation_passed": simulation_report["failed"] == 0,
        "test_agent_passed": test_report["passed"],
        "benchmark_review": benchmark_review,
        "revision_performed": revision_performed,
    }
    save_json(ARTIFACTS / "pipeline_summary.json", final_summary)
    log_event("Pipeline finished")
    return final_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--skip-irsim",
        action="store_true",
        help="Run the software pipeline without launching IR-SIM worlds",
    )
    args = parser.parse_args()
    summary = run_pipeline(skip_irsim=args.skip_irsim)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
