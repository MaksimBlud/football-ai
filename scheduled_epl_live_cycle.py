"""Scheduled EPL live-cycle compatibility entrypoint.

The historical EPL live cycle still contains a Phase 4D precondition requiring
zero finished results. That precondition is obsolete now that a separate EPL
Results Sync legitimately persists immutable finished results.

This wrapper masks only that obsolete precondition from the legacy cycle while
preserving the actual safety invariant externally: the EPL live cycle must not
change the finished-results count. The check is performed even when the inner
cycle raises.
"""

from __future__ import annotations

from collections.abc import Callable

import epl_live_cycle as cycle


Counts = tuple[int, int]


def run_scheduled_cycle(
    *,
    counts: Callable[[], Counts] | None = None,
):
    """Run EPL live cycle while permitting pre-existing immutable results."""

    original_counts = cycle.durable_counts
    real_counts = counts or original_counts

    observations_before, results_before = real_counts()

    def masked_counts() -> Counts:
        observations, _results = real_counts()
        return observations, 0

    inner_error: BaseException | None = None
    result = None

    cycle.durable_counts = masked_counts

    try:
        result = cycle.run_cycle()
    except BaseException as exc:  # preserve the original failure after safety check
        inner_error = exc
    finally:
        cycle.durable_counts = original_counts

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

    return result


if __name__ == "__main__":
    run_scheduled_cycle()
