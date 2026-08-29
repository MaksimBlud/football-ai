"""One-command research-only EPL live cycle.

Stages:
1. export future EPL fixtures from existing odds snapshots;
2. generate MARKET_ONLY shadow;
3. persist generic durable MARKET_ONLY observations;
4. verify resulting durable state.

Explicitly excluded:
- production model prediction;
- model training/promotion;
- Structural V2;
- finished-results persistence;
- migrations;
- Odds API collection.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from database import supabase

import export_epl_upcoming_matches as fixture_export
import generate_epl_market_shadow as market_shadow
import league_supabase_persistence as persistence
import persist_epl_market_observations as observation_mirror
import persist_epl_prediction_ledger as prediction_ledger

from league_runtime_config import (
    EPL_RUNTIME_CONFIG,
)


@dataclass(frozen=True)
class EPLLiveCycleResult:
    fixture_source_rows: int
    fixture_rows: int
    market_snapshot_rows: int
    market_shadow_rows: int
    market_ok_rows: int
    history_rows: int
    observations_before: int
    observations_after: int
    observations_inserted: int
    observations_unchanged: int
    observation_conflicts: int
    ledger_before: int
    ledger_after: int
    ledger_inserted: int
    ledger_unchanged: int
    ledger_conflicts: int
    results_before: int
    results_after: int


def assert_market_only_runtime() -> None:
    structural = (
        EPL_RUNTIME_CONFIG
        .structural_v2
    )

    if (
        structural.calibration_status
        != "CALIBRATION_REQUIRED"
    ):
        raise RuntimeError(
            "EPL Structural V2 must remain CALIBRATION_REQUIRED"
        )

    if structural.structural_alpha is not None:
        raise RuntimeError(
            "EPL structural_alpha must remain unset"
        )

    if structural.edge_threshold is not None:
        raise RuntimeError(
            "EPL edge_threshold must remain unset"
        )


def export_fixtures() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
]:
    snapshots = (
        fixture_export
        .fetch_epl_snapshots()
    )

    upcoming = (
        fixture_export
        .prepare_upcoming_fixtures(
            snapshots
        )
    )

    if upcoming.empty:
        raise RuntimeError(
            "No future EPL fixtures available"
        )

    if upcoming[
        "event_id"
    ].duplicated().any():
        raise RuntimeError(
            "Duplicate EPL fixture event_id"
        )

    path = (
        EPL_RUNTIME_CONFIG
        .paths
        .upcoming_fixtures
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    upcoming.to_csv(
        path,
        index=False,
    )

    return (
        snapshots,
        upcoming,
    )


def generate_market_shadow() -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    upcoming = (
        market_shadow
        .load_upcoming()
    )

    snapshots = (
        market_shadow
        .fetch_epl_snapshots()
    )

    previous_history = (
        market_shadow
        .load_previous_history()
    )

    latest = (
        market_shadow
        .build_market_shadow(
            upcoming,
            snapshots,
            previous_history=previous_history,
        )
    )

    if latest.empty:
        raise RuntimeError(
            "EPL market shadow is empty"
        )

    if latest[
        "event_id"
    ].duplicated().any():
        raise RuntimeError(
            "Duplicate EPL market-shadow event_id"
        )

    if not (
        latest["league"]
        == EPL_RUNTIME_CONFIG.identity.identifier
    ).all():
        raise RuntimeError(
            "Foreign league in EPL market shadow"
        )

    if not (
        latest["market_only"]
        .astype(str)
        .str.lower()
        == "true"
    ).all():
        raise RuntimeError(
            "Non-market-only state in EPL shadow"
        )

    history = (
        market_shadow
        .write_market_shadow_outputs(
            latest,
            latest_path=(
                EPL_RUNTIME_CONFIG
                .paths
                .market_shadow
            ),
            history_path=(
                EPL_RUNTIME_CONFIG
                .paths
                .market_history
            ),
        )
    )

    return (
        snapshots,
        latest,
        history,
    )


def validate_current_market_shadow(
    latest: pd.DataFrame,
) -> pd.DataFrame:
    ok = latest.loc[
        latest[
            "market_shadow_status"
        ]
        == "OK"
    ].copy()

    if ok.empty:
        raise RuntimeError(
            "No valid EPL market shadows"
        )

    snapshot = pd.to_datetime(
        ok[
            "snapshot_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    kickoff = pd.to_datetime(
        ok[
            "commence_time_utc"
        ],
        utc=True,
        errors="coerce",
    )

    if snapshot.isna().any():
        raise RuntimeError(
            "Invalid EPL shadow snapshot timestamp"
        )

    if kickoff.isna().any():
        raise RuntimeError(
            "Invalid EPL shadow kickoff timestamp"
        )

    if not (
        snapshot < kickoff
    ).all():
        raise RuntimeError(
            "EPL market shadow contains non-pre-kickoff state"
        )

    probabilities = ok[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    if probabilities.isna().any().any():
        raise RuntimeError(
            "Invalid EPL market probabilities"
        )

    sums = probabilities.sum(
        axis=1
    )

    if not (
        sums.sub(1.0)
        .abs()
        <= 1e-12
    ).all():
        raise RuntimeError(
            "EPL market probabilities do not sum to one"
        )

    return ok


def durable_counts() -> tuple[int, int]:
    observations = (
        persistence.fetch_observations(
            supabase,
            EPL_RUNTIME_CONFIG,
        )
    )

    results = (
        persistence.fetch_results(
            supabase,
            EPL_RUNTIME_CONFIG,
        )
    )

    return (
        len(observations),
        len(results),
    )


def ledger_count() -> int:
    response = (
        supabase
        .table(
            prediction_ledger.TABLE
        )
        .select(
            "prediction_key",
            count="exact",
        )
        .eq(
            "league",
            EPL_RUNTIME_CONFIG.identity.identifier,
        )
        .execute()
    )

    if response.count is not None:
        return int(
            response.count
        )

    return len(
        response.data
        or []
    )


def persist_prediction_ledger() -> tuple[
    int,
    int,
    dict[str, int],
]:
    """Persist canonical prediction state after durable observations."""

    before = ledger_count()

    predictions = (
        prediction_ledger
        .build_current_predictions()
    )

    if predictions.empty:
        raise RuntimeError(
            "EPL canonical prediction ledger input is empty"
        )

    if not (
        predictions[
            "prediction_mode"
        ]
        == "MARKET_ONLY"
    ).all():
        raise RuntimeError(
            "EPL prediction ledger contains non-MARKET_ONLY state"
        )

    if (
        predictions[
            "structural_applied"
        ]
        .astype(bool)
        .any()
    ):
        raise RuntimeError(
            "EPL prediction ledger unexpectedly applied Structural V2"
        )

    if predictions[
        "observation_key"
    ].isna().any():
        raise RuntimeError(
            "EPL prediction ledger contains unlinked observations"
        )

    metrics = (
        prediction_ledger
        .persist_predictions(
            supabase,
            predictions,
        )
    )

    after = ledger_count()

    inserted = int(
        metrics[
            "inserted"
        ]
    )

    unchanged = int(
        metrics[
            "unchanged"
        ]
    )

    conflicts = int(
        metrics[
            "conflicts"
        ]
    )

    if conflicts != 0:
        raise RuntimeError(
            "EPL prediction ledger reported conflicts"
        )

    if (
        inserted
        + unchanged
        != len(predictions)
    ):
        raise RuntimeError(
            "EPL prediction-ledger metrics do not cover input"
        )

    if after != (
        before
        + inserted
    ):
        raise RuntimeError(
            "EPL prediction-ledger count disagrees with metrics"
        )

    return (
        before,
        after,
        {
            "inserted": inserted,
            "unchanged": unchanged,
            "conflicts": conflicts,
        },
    )


def run_cycle() -> EPLLiveCycleResult:
    assert_market_only_runtime()

    schema = persistence.check_schema(
        supabase
    )

    if schema.status != "PASS":
        raise RuntimeError(
            "Generic persistence unavailable: "
            + schema.detail
        )

    (
        observations_before,
        results_before,
    ) = durable_counts()

    (
        fixture_snapshots,
        upcoming,
    ) = export_fixtures()

    (
        market_snapshots,
        latest,
        history,
    ) = generate_market_shadow()

    ok = validate_current_market_shadow(
        latest
    )

    # Canonical durable boundary:
    #
    # Persistence must consume the same serialized market-shadow
    # representation used by the standalone observation mirror.
    #
    # Passing the fresh in-memory probability frame directly here can
    # create representation-only observation identities because a CSV
    # float round-trip may differ at ~1e-17 while representing the same
    # market state.
    persisted_shadow = (
        observation_mirror
        .load_market_shadow()
    )

    if len(persisted_shadow) != len(latest):
        raise RuntimeError(
            "Persisted EPL market shadow disagrees with generated row count"
        )

    if set(
        persisted_shadow["event_id"].astype(str)
    ) != set(
        latest["event_id"].astype(str)
    ):
        raise RuntimeError(
            "Persisted EPL market shadow disagrees with generated event set"
        )

    durable_input = (
        observation_mirror
        .build_market_only_observations(
            persisted_shadow
        )
    )

    if len(durable_input) != len(ok):
        raise RuntimeError(
            "Durable EPL observation count disagrees with OK market shadow"
        )

    metrics = (
        persistence.persist_observations(
            supabase,
            durable_input,
            EPL_RUNTIME_CONFIG,
        )
    )

    (
        observations_after,
        results_after,
    ) = durable_counts()

    if results_after != results_before:
        raise RuntimeError(
            "EPL live cycle modified finished results"
        )

    expected_after = (
        observations_before
        + int(
            metrics[
                "inserted"
            ]
        )
    )

    if observations_after != expected_after:
        raise RuntimeError(
            "Durable observation count disagrees with persistence metrics"
        )

    if int(
        metrics[
            "conflicts"
        ]
    ) != 0:
        raise RuntimeError(
            "EPL live cycle reported persistence conflicts"
        )

    processed = (
        int(
            metrics[
                "inserted"
            ]
        )
        + int(
            metrics[
                "unchanged"
            ]
        )
    )

    if processed != len(
        durable_input
    ):
        raise RuntimeError(
            "Persistence metrics do not cover all incoming observations"
        )

    (
        ledger_before,
        ledger_after,
        ledger_metrics,
    ) = persist_prediction_ledger()

    return EPLLiveCycleResult(
        fixture_source_rows=len(
            fixture_snapshots
        ),
        fixture_rows=len(
            upcoming
        ),
        market_snapshot_rows=len(
            market_snapshots
        ),
        market_shadow_rows=len(
            latest
        ),
        market_ok_rows=len(
            ok
        ),
        history_rows=len(
            history
        ),
        observations_before=(
            observations_before
        ),
        observations_after=(
            observations_after
        ),
        observations_inserted=int(
            metrics[
                "inserted"
            ]
        ),
        observations_unchanged=int(
            metrics[
                "unchanged"
            ]
        ),
        observation_conflicts=int(
            metrics[
                "conflicts"
            ]
        ),
        ledger_before=(
            ledger_before
        ),
        ledger_after=(
            ledger_after
        ),
        ledger_inserted=int(
            ledger_metrics[
                "inserted"
            ]
        ),
        ledger_unchanged=int(
            ledger_metrics[
                "unchanged"
            ]
        ),
        ledger_conflicts=int(
            ledger_metrics[
                "conflicts"
            ]
        ),
        results_before=(
            results_before
        ),
        results_after=(
            results_after
        ),
    )


def main() -> None:
    result = run_cycle()

    print("=" * 72)
    print("EPL MARKET-ONLY LIVE CYCLE")
    print("=" * 72)

    print(
        "fixture source rows:",
        result.fixture_source_rows,
    )

    print(
        "future fixtures:",
        result.fixture_rows,
    )

    print(
        "market snapshot rows:",
        result.market_snapshot_rows,
    )

    print(
        "market shadow rows:",
        result.market_shadow_rows,
    )

    print(
        "market OK rows:",
        result.market_ok_rows,
    )

    print(
        "market history rows:",
        result.history_rows,
    )

    print(
        "durable observations before:",
        result.observations_before,
    )

    print(
        "durable observations after:",
        result.observations_after,
    )

    print(
        "inserted:",
        result.observations_inserted,
    )

    print(
        "unchanged:",
        result.observations_unchanged,
    )

    print(
        "conflicts:",
        result.observation_conflicts,
    )

    print(
        "prediction ledger before:",
        result.ledger_before,
    )

    print(
        "prediction ledger after:",
        result.ledger_after,
    )

    print(
        "ledger inserted:",
        result.ledger_inserted,
    )

    print(
        "ledger unchanged:",
        result.ledger_unchanged,
    )

    print(
        "ledger conflicts:",
        result.ledger_conflicts,
    )

    print(
        "EPL results before:",
        result.results_before,
    )

    print(
        "EPL results after:",
        result.results_after,
    )

    print(
        "AI model used:",
        False,
    )

    print(
        "Structural V2 used:",
        False,
    )

    print()
    print(
        "PASS: EPL MARKET-ONLY LIVE CYCLE COMPLETE"
    )


if __name__ == "__main__":
    main()