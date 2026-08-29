"""One-command research-only RPL MARKET_ONLY live cycle.

Stages:
1. export future RPL fixtures from existing odds snapshots;
2. generate MARKET_ONLY shadow;
3. persist generic durable MARKET_ONLY observations;
4. persist canonical prediction ledger;
5. verify durable counts and safety invariants.

No production model and no Structural V2 are used.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from database import supabase
import export_rpl_upcoming_matches as fixture_export
import generate_rpl_market_shadow as market_shadow
import league_supabase_persistence as persistence
import persist_rpl_market_observations as observation_mirror
import persist_rpl_prediction_ledger as prediction_ledger
from league_runtime_config import RPL_RUNTIME_CONFIG


@dataclass(frozen=True)
class RPLLiveCycleResult:
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
    structural = RPL_RUNTIME_CONFIG.structural_v2
    if structural.calibration_status != "CALIBRATION_REQUIRED":
        raise RuntimeError("RPL Structural V2 must remain CALIBRATION_REQUIRED")
    if structural.structural_alpha is not None:
        raise RuntimeError("RPL structural_alpha must remain unset")
    if structural.edge_threshold is not None:
        raise RuntimeError("RPL edge_threshold must remain unset")


def durable_counts() -> tuple[int, int]:
    observations = persistence.fetch_observations(
        supabase,
        RPL_RUNTIME_CONFIG,
    )
    results = persistence.fetch_results(
        supabase,
        RPL_RUNTIME_CONFIG,
    )
    return len(observations), len(results)


def ledger_count() -> int:
    response = (
        supabase
        .table(prediction_ledger.TABLE)
        .select("prediction_key", count="exact")
        .eq("league", RPL_RUNTIME_CONFIG.identity.identifier)
        .execute()
    )
    if response.count is not None:
        return int(response.count)
    return len(response.data or [])


def run_cycle() -> RPLLiveCycleResult:
    assert_market_only_runtime()

    schema = persistence.check_schema(supabase)
    if schema.status != "PASS":
        raise RuntimeError("Generic persistence unavailable: " + schema.detail)

    observations_before, results_before = durable_counts()
    ledger_before = ledger_count()

    fixture_snapshots = fixture_export.fetch_rpl_snapshots()
    upcoming = fixture_export.prepare_upcoming_fixtures(fixture_snapshots)
    if upcoming.empty:
        raise RuntimeError("No future RPL fixtures available")
    if upcoming["event_id"].duplicated().any():
        raise RuntimeError("Duplicate RPL fixture event_id")

    fixture_path = RPL_RUNTIME_CONFIG.paths.upcoming_fixtures
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    upcoming.to_csv(fixture_path, index=False)

    market_snapshots = market_shadow.fetch_rpl_snapshots()
    previous_history = market_shadow.load_previous_history()
    latest = market_shadow.build_market_shadow(
        market_shadow.load_upcoming(),
        market_snapshots,
        previous_history=previous_history,
    )
    if latest.empty:
        raise RuntimeError("RPL market shadow is empty")
    if latest["event_id"].duplicated().any():
        raise RuntimeError("Duplicate RPL market-shadow event_id")
    if not (latest["league"].astype(str) == "RPL").all():
        raise RuntimeError("Foreign league in RPL market shadow")
    if not (latest["market_only"].astype(str).str.lower() == "true").all():
        raise RuntimeError("Non-market-only state in RPL shadow")

    history = market_shadow.write_market_shadow_outputs(
        latest,
        latest_path=RPL_RUNTIME_CONFIG.paths.market_shadow,
        history_path=RPL_RUNTIME_CONFIG.paths.market_history,
    )

    ok = latest.loc[latest["market_shadow_status"] == "OK"].copy()
    if ok.empty:
        raise RuntimeError("No valid RPL market shadows")

    snapshot = pd.to_datetime(ok["snapshot_time_utc"], utc=True, errors="coerce")
    kickoff = pd.to_datetime(ok["commence_time_utc"], utc=True, errors="coerce")
    if snapshot.isna().any() or kickoff.isna().any():
        raise RuntimeError("Invalid RPL shadow timestamps")
    if not (snapshot < kickoff).all():
        raise RuntimeError("RPL market shadow contains non-pre-kickoff state")

    probabilities = ok[
        [
            "market_home_probability",
            "market_draw_probability",
            "market_away_probability",
        ]
    ].apply(pd.to_numeric, errors="coerce")
    if probabilities.isna().any().any():
        raise RuntimeError("Invalid RPL market probabilities")
    if not (probabilities.sum(axis=1).sub(1.0).abs() <= 1e-12).all():
        raise RuntimeError("RPL market probabilities do not sum to one")

    # Persist from the serialized CSV boundary to avoid float-representation
    # identity drift between in-memory and durable observations.
    persisted_shadow = observation_mirror.load_market_shadow()
    if len(persisted_shadow) != len(latest):
        raise RuntimeError("Persisted RPL shadow row count disagrees with generated state")
    if set(persisted_shadow["event_id"].astype(str)) != set(latest["event_id"].astype(str)):
        raise RuntimeError("Persisted RPL shadow event set disagrees with generated state")

    durable_input = observation_mirror.build_market_only_observations(persisted_shadow)
    if len(durable_input) != len(ok):
        raise RuntimeError("Durable RPL observation count disagrees with OK shadow")

    observation_metrics = persistence.persist_observations(
        supabase,
        durable_input,
        RPL_RUNTIME_CONFIG,
    )
    if int(observation_metrics["conflicts"]) != 0:
        raise RuntimeError("RPL observation persistence reported conflicts")
    if int(observation_metrics["inserted"]) + int(observation_metrics["unchanged"]) != len(durable_input):
        raise RuntimeError("RPL observation metrics do not cover input")

    observations_after, results_after = durable_counts()
    if results_after != results_before:
        raise RuntimeError("RPL live cycle modified finished results")
    if observations_after != observations_before + int(observation_metrics["inserted"]):
        raise RuntimeError("RPL durable observation count disagrees with metrics")

    ledger_metrics = prediction_ledger.persist_current_predictions()
    if int(ledger_metrics["conflicts"]) != 0:
        raise RuntimeError("RPL prediction ledger reported conflicts")
    ledger_after = ledger_count()
    if ledger_after != ledger_before + int(ledger_metrics["inserted"]):
        raise RuntimeError("RPL prediction ledger count disagrees with metrics")

    return RPLLiveCycleResult(
        fixture_source_rows=len(fixture_snapshots),
        fixture_rows=len(upcoming),
        market_snapshot_rows=len(market_snapshots),
        market_shadow_rows=len(latest),
        market_ok_rows=len(ok),
        history_rows=len(history),
        observations_before=observations_before,
        observations_after=observations_after,
        observations_inserted=int(observation_metrics["inserted"]),
        observations_unchanged=int(observation_metrics["unchanged"]),
        observation_conflicts=int(observation_metrics["conflicts"]),
        ledger_before=ledger_before,
        ledger_after=ledger_after,
        ledger_inserted=int(ledger_metrics["inserted"]),
        ledger_unchanged=int(ledger_metrics["unchanged"]),
        ledger_conflicts=int(ledger_metrics["conflicts"]),
        results_before=results_before,
        results_after=results_after,
    )


def main() -> None:
    result = run_cycle()
    print("=" * 72)
    print("RPL MARKET-ONLY LIVE CYCLE")
    print("=" * 72)
    for field, value in result.__dict__.items():
        print(field + ":", value)
    print("AI model used:", False)
    print("Structural V2 used:", False)
    print("production model used:", False)


if __name__ == "__main__":
    main()
