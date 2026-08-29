"""One-command research-only Serie A MARKET_ONLY live cycle."""

from __future__ import annotations

from dataclasses import dataclass
import pandas as pd

from database import supabase
import export_serie_a_upcoming_matches as fixture_export
import generate_serie_a_market_shadow as market_shadow
import league_supabase_persistence as persistence
import persist_serie_a_market_observations as observation_mirror
import persist_serie_a_prediction_ledger as prediction_ledger
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG


@dataclass(frozen=True)
class SerieALiveCycleResult:
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
    s = SERIE_A_RUNTIME_CONFIG.structural_v2
    if s.calibration_status != "CALIBRATION_REQUIRED" or s.structural_alpha is not None or s.edge_threshold is not None:
        raise RuntimeError("Serie A Structural V2 must remain calibration-required")


def durable_counts() -> tuple[int, int]:
    observations = persistence.fetch_observations(supabase, SERIE_A_RUNTIME_CONFIG)
    results = persistence.fetch_results(supabase, SERIE_A_RUNTIME_CONFIG)
    return len(observations), len(results)


def ledger_count() -> int:
    response = (
        supabase.table(prediction_ledger.TABLE)
        .select("prediction_key", count="exact")
        .eq("league", SERIE_A_RUNTIME_CONFIG.identity.identifier)
        .execute()
    )
    return int(response.count) if response.count is not None else len(response.data or [])


def run_cycle() -> SerieALiveCycleResult:
    assert_market_only_runtime()
    schema = persistence.check_schema(supabase)
    if schema.status != "PASS":
        raise RuntimeError("Generic persistence unavailable: " + schema.detail)
    observations_before, results_before = durable_counts()
    ledger_before = ledger_count()

    fixture_snapshots = fixture_export.fetch_serie_a_snapshots()
    upcoming = fixture_export.prepare_upcoming_fixtures(fixture_snapshots)
    if upcoming.empty:
        raise RuntimeError("No future Serie A fixtures available")
    if upcoming["event_id"].duplicated().any():
        raise RuntimeError("Duplicate Serie A fixture event_id")
    fixture_path = SERIE_A_RUNTIME_CONFIG.paths.upcoming_fixtures
    fixture_path.parent.mkdir(parents=True, exist_ok=True)
    upcoming.to_csv(fixture_path, index=False)

    market_snapshots = market_shadow.fetch_serie_a_snapshots()
    latest = market_shadow.build_market_shadow(
        market_shadow.load_upcoming(),
        market_snapshots,
        previous_history=market_shadow.load_previous_history(),
    )
    if latest.empty or latest["event_id"].duplicated().any():
        raise RuntimeError("Invalid Serie A market shadow")
    if not (latest["league"].astype(str) == "SERIE_A").all():
        raise RuntimeError("Foreign league in Serie A market shadow")
    if not (latest["market_only"].astype(str).str.lower() == "true").all():
        raise RuntimeError("Non-market-only state in Serie A shadow")

    history = market_shadow.write_market_shadow_outputs(
        latest,
        latest_path=SERIE_A_RUNTIME_CONFIG.paths.market_shadow,
        history_path=SERIE_A_RUNTIME_CONFIG.paths.market_history,
    )
    ok = latest.loc[latest["market_shadow_status"] == "OK"].copy()
    if ok.empty:
        raise RuntimeError("No valid Serie A market shadows")
    snapshot = pd.to_datetime(ok["snapshot_time_utc"], utc=True, errors="coerce")
    kickoff = pd.to_datetime(ok["commence_time_utc"], utc=True, errors="coerce")
    if snapshot.isna().any() or kickoff.isna().any() or not (snapshot < kickoff).all():
        raise RuntimeError("Serie A market shadow timestamp safety failed")
    probabilities = ok[["market_home_probability", "market_draw_probability", "market_away_probability"]].apply(pd.to_numeric, errors="coerce")
    if probabilities.isna().any().any() or not (probabilities.sum(axis=1).sub(1.0).abs() <= 1e-12).all():
        raise RuntimeError("Serie A market probabilities invalid")

    persisted_shadow = observation_mirror.load_market_shadow()
    if len(persisted_shadow) != len(latest) or set(persisted_shadow["event_id"].astype(str)) != set(latest["event_id"].astype(str)):
        raise RuntimeError("Persisted Serie A shadow disagrees with generated state")
    durable_input = observation_mirror.build_market_only_observations(persisted_shadow)
    observation_metrics = persistence.persist_observations(
        supabase,
        durable_input,
        SERIE_A_RUNTIME_CONFIG,
    )
    if int(observation_metrics["conflicts"]) != 0:
        raise RuntimeError("Serie A observation conflict")
    observations_after, results_after = durable_counts()
    if results_after != results_before:
        raise RuntimeError("Serie A live cycle modified finished results")
    if observations_after != observations_before + int(observation_metrics["inserted"]):
        raise RuntimeError("Serie A durable observation count mismatch")

    ledger_metrics = prediction_ledger.persist_current_predictions()
    if int(ledger_metrics["conflicts"]) != 0:
        raise RuntimeError("Serie A ledger conflict")
    ledger_after = ledger_count()
    if ledger_after != ledger_before + int(ledger_metrics["inserted"]):
        raise RuntimeError("Serie A ledger count mismatch")

    return SerieALiveCycleResult(
        fixture_source_rows=len(fixture_snapshots), fixture_rows=len(upcoming),
        market_snapshot_rows=len(market_snapshots), market_shadow_rows=len(latest),
        market_ok_rows=len(ok), history_rows=len(history),
        observations_before=observations_before, observations_after=observations_after,
        observations_inserted=int(observation_metrics["inserted"]),
        observations_unchanged=int(observation_metrics["unchanged"]),
        observation_conflicts=int(observation_metrics["conflicts"]),
        ledger_before=ledger_before, ledger_after=ledger_after,
        ledger_inserted=int(ledger_metrics["inserted"]),
        ledger_unchanged=int(ledger_metrics["unchanged"]),
        ledger_conflicts=int(ledger_metrics["conflicts"]),
        results_before=results_before, results_after=results_after,
    )


def main() -> None:
    result = run_cycle()
    print("=" * 72)
    print("SERIE A MARKET-ONLY LIVE CYCLE")
    print("=" * 72)
    for field, value in result.__dict__.items():
        print(field + ":", value)
    print("AI model used:", False)
    print("Structural V2 used:", False)
    print("production model used:", False)


if __name__ == "__main__":
    main()
