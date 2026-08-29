"""Scheduled La Liga live entrypoint.

Explicitly grants live Odds API collection only for the scheduled workflow,
then runs the durable La Liga cycle against the resulting/persisted snapshot
without permitting a second collection attempt. After the durable-cycle
attempt, immutable La Liga state is mirrored into both canonical authorities:
the prediction ledger and generic finished-results table, then the shared
read-only evaluator validates the canonical settlement path.

A downstream legacy-cycle failure must not suppress canonical mirroring of
state already committed. The durable-cycle return code remains authoritative
when that cycle fails. When the durable cycle succeeds, both canonical
mirrors and the read-only canonical evaluator are mandatory.
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

RESULTS_BRIDGE_COMMAND = (
    "persist_la_liga_finished_results.py",
)

EVALUATION_COMMAND = (
    "evaluate_league_predictions.py",
    "--league",
    "LA_LIGA",
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
            "La Liga live collection failed; durable cycle and canonical "
            f"steps skipped (exit code {collection_rc})."
        )
        return collection_rc

    cycle_rc = run_command(
        CYCLE_COMMAND,
        runner=runner,
    )

    # A legacy cycle may commit immutable observations/results before a later
    # downstream step fails. Always attempt both one-way canonical mirrors.
    ledger_rc = run_command(
        LEDGER_COMMAND,
        runner=runner,
    )

    results_rc = run_command(
        RESULTS_BRIDGE_COMMAND,
        runner=runner,
    )

    # Evaluation is read-only. Run it after both mirror attempts so scheduled
    # logs expose whether the shared ledger/results authority is internally
    # readable and settleable. Zero settled fixtures is a valid evaluation.
    evaluation_rc = run_command(
        EVALUATION_COMMAND,
        runner=runner,
    )

    if cycle_rc != 0:
        print(
            "La Liga durable cycle failed; canonical steps were attempted "
            "against any immutable state already committed "
            f"(cycle={cycle_rc}, ledger={ledger_rc}, results={results_rc}, "
            f"evaluation={evaluation_rc})."
        )
        return cycle_rc

    if ledger_rc != 0:
        print(
            "La Liga canonical prediction-ledger persistence failed "
            f"(exit code {ledger_rc})."
        )
        return ledger_rc

    if results_rc != 0:
        print(
            "La Liga canonical finished-results bridge failed "
            f"(exit code {results_rc})."
        )
        return results_rc

    if evaluation_rc != 0:
        print(
            "La Liga canonical read-only evaluation failed "
            f"(exit code {evaluation_rc})."
        )
        return evaluation_rc

    return 0


if __name__ == "__main__":
    raise SystemExit(run_scheduled_cycle())
