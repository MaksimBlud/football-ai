"""Scheduled La Liga live entrypoint.

Explicitly grants live Odds API collection only for the scheduled workflow,
then runs the durable La Liga cycle against the resulting/persisted snapshot
without permitting a second collection attempt. After the durable-cycle
attempt, the same pre-kickoff MARKET_ONLY state is mirrored into the
canonical append-only league prediction ledger when its immutable observation
linkage is available.

A downstream results/evaluation failure must not suppress an already-durable
pre-kickoff prediction. The durable-cycle return code remains authoritative
when that cycle fails; ledger persistence is best-effort in that failure case.
When the durable cycle succeeds, ledger persistence remains mandatory.
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

LEDGER_COMMAND = (
    "persist_la_liga_prediction_ledger.py",
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
            "La Liga live collection failed; durable cycle and ledger skipped "
            f"(exit code {collection_rc})."
        )
        return collection_rc

    cycle_rc = run_command(
        CYCLE_COMMAND,
        runner=runner,
    )

    # The durable La Liga cycle persists pre-kickoff observations before its
    # downstream results/evaluation stages. Always attempt the canonical
    # ledger after the cycle attempt so a later downstream failure cannot
    # leave an already-durable prediction without its canonical mirror.
    ledger_rc = run_command(
        LEDGER_COMMAND,
        runner=runner,
    )

    if cycle_rc != 0:
        if ledger_rc == 0:
            print(
                "La Liga durable cycle failed after/beside ledger attempt; "
                "canonical ledger completed where durable observation linkage "
                f"was available (cycle exit code {cycle_rc})."
            )
        else:
            print(
                "La Liga durable cycle failed and canonical ledger could not "
                "be completed; preserving durable-cycle failure "
                f"(cycle exit code {cycle_rc}, ledger exit code {ledger_rc})."
            )

        return cycle_rc

    if ledger_rc != 0:
        print(
            "La Liga canonical ledger persistence failed "
            f"(exit code {ledger_rc})."
        )

    return ledger_rc


if __name__ == "__main__":
    raise SystemExit(run_scheduled_cycle())
