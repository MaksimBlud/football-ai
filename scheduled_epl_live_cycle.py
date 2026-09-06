"""Scheduled EPL live-cycle compatibility and dual-write safety entrypoint.

The historical EPL live cycle still contains a Phase 4D precondition requiring
zero finished results. That precondition is obsolete now that a separate EPL
Results Sync legitimately persists immutable finished results.

This wrapper masks only that obsolete precondition, preserves the finished-result
count, and hardens the append-only observation -> prediction-ledger sequence:
all deterministic observation/ledger conflicts are preflighted before the first
write; each append side gets one idempotent replay for a non-deterministic error;
and the canonical ledger plan is read-after-write verified.
"""

from __future__ import annotations

from collections.abc import Callable

import epl_dual_write_guard as dual_write_guard
import epl_live_cycle as cycle


Counts = tuple[int, int]


def run_scheduled_cycle(
    *,
    counts: Callable[[], Counts] | None = None,
):
    """Run EPL live cycle while permitting pre-existing immutable results."""

    original_counts = cycle.durable_counts
    original_observation_persist = cycle.persistence.persist_observations
    original_ledger_persist = cycle.persist_prediction_ledger
    real_counts = counts or original_counts

    observations_before, results_before = real_counts()
    prepared_plan = None

    def masked_counts() -> Counts:
        observations, _results = real_counts()
        return observations, 0

    def guarded_observation_persist(client, frame, config):
        nonlocal prepared_plan

        shadow = cycle.observation_mirror.load_market_shadow()
        prepared_plan = dual_write_guard.prepare_dual_write(
            client,
            shadow,
            frame,
            config,
        )

        return dual_write_guard.persist_observations_with_retry(
            client,
            frame,
            config,
            persist_fn=original_observation_persist,
        )

    def guarded_ledger_persist():
        if prepared_plan is None:
            raise RuntimeError(
                "EPL ledger persistence reached before dual-write preflight"
            )

        before = cycle.ledger_count()

        dual_write_guard.persist_predictions_with_retry(
            cycle.supabase,
            prepared_plan.predictions,
        )

        after = cycle.ledger_count()

        return (
            before,
            after,
            {
                "inserted": prepared_plan.prediction_missing,
                "unchanged": prepared_plan.prediction_present,
                "conflicts": 0,
            },
        )

    inner_error: BaseException | None = None
    result = None

    cycle.durable_counts = masked_counts
    cycle.persistence.persist_observations = guarded_observation_persist
    cycle.persist_prediction_ledger = guarded_ledger_persist

    try:
        result = cycle.run_cycle()
    except BaseException as exc:  # preserve the original failure after safety check
        inner_error = exc
    finally:
        cycle.durable_counts = original_counts
        cycle.persistence.persist_observations = original_observation_persist
        cycle.persist_prediction_ledger = original_ledger_persist

    observations_after, results_after = real_counts()

    if results_after != results_before:
        raise RuntimeError(
            "Scheduled EPL live cycle modified finished results: "
            f"before={results_before}, after={results_after}"
        ) from inner_error

    if inner_error is not None:
        raise inner_error

    if result is None:
        raise RuntimeError(
            "Scheduled EPL live cycle returned no result"
        )

    print(
        "EPL finished results preserved:",
        results_before,
    )
    print(
        "EPL durable observations:",
        observations_before,
        "->",
        observations_after,
    )

    if prepared_plan is not None:
        print(
            "EPL dual-write preflight observations present/missing:",
            prepared_plan.observation_present,
            prepared_plan.observation_missing,
        )
        print(
            "EPL dual-write preflight predictions present/missing:",
            prepared_plan.prediction_present,
            prepared_plan.prediction_missing,
        )

    return result


if __name__ == "__main__":
    run_scheduled_cycle()
