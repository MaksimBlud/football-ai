"""Scheduled La Liga live entrypoint.

Explicitly grants live Odds API collection only for the scheduled workflow,
then runs the durable La Liga cycle against the resulting/persisted snapshot
without permitting a second collection attempt.
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable, Sequence


COLLECTION_COMMAND = (
    "la_liga_collection_runner.py",
    "--live",
    "--skip-downstream",
)

CYCLE_COMMAND = (
    "la_liga_live_cycle.py",
    "--skip-collection",
    "--persistence",
    "supabase",
)


def run_command(
    command: Sequence[str],
    *,
    runner: Callable = subprocess.run,
) -> int:
    completed = runner(
        [sys.executable, *command],
        check=False,
    )
    return int(completed.returncode)


def run_scheduled_cycle(
    *,
    runner: Callable = subprocess.run,
) -> int:
    collection_rc = run_command(
        COLLECTION_COMMAND,
        runner=runner,
    )

    if collection_rc != 0:
        print(
            "La Liga live collection failed; durable cycle skipped "
            f"(exit code {collection_rc})."
        )
        return collection_rc

    cycle_rc = run_command(
        CYCLE_COMMAND,
        runner=runner,
    )

    if cycle_rc != 0:
        print(
            "La Liga durable cycle failed "
            f"(exit code {cycle_rc})."
        )

    return cycle_rc


if __name__ == "__main__":
    raise SystemExit(run_scheduled_cycle())
