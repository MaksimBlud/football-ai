"""Read-only RPL canonical prediction evaluator.

Uses the shared validation/metric primitives but settles fixture dates in the
RPL runtime timezone (Europe/Moscow), avoiding the EPL-specific London date
assumption in the older generic evaluator.
"""

from __future__ import annotations

import pandas as pd

import evaluate_league_predictions as shared
from league_runtime_config import RPL_RUNTIME_CONFIG
from team_names import normalize_team_name


LEAGUE = RPL_RUNTIME_CONFIG.identity.identifier
TIMEZONE = RPL_RUNTIME_CONFIG.identity.timezone


def settle_rpl_predictions(
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> pd.DataFrame:
    ledger = shared._validate_ledger(ledger)
    results = shared._validate_results(results)
    if ledger.empty or results.empty:
        return pd.DataFrame()

    if not (ledger["league"].astype(str) == LEAGUE).all():
        raise ValueError("RPL evaluator received non-RPL ledger rows")
    if not (results["league"].astype(str) == LEAGUE).all():
        raise ValueError("RPL evaluator received non-RPL result rows")

    ledger = ledger.copy()
    results = results.copy()
    ledger["_match_date"] = (
        ledger["kickoff_utc"].dt.tz_convert(TIMEZONE).dt.date
    )
    ledger["_home_key"] = ledger["home_team"].map(
        lambda value: normalize_team_name(str(value))
    )
    ledger["_away_key"] = ledger["away_team"].map(
        lambda value: normalize_team_name(str(value))
    )

    results["_match_date"] = results["match_date"]
    results["_home_key"] = results["home_team"].map(
        lambda value: normalize_team_name(str(value))
    )
    results["_away_key"] = results["away_team"].map(
        lambda value: normalize_team_name(str(value))
    )

    result_view = results[
        ["_match_date", "_home_key", "_away_key", "result"]
    ].copy()
    identity = ["_match_date", "_home_key", "_away_key"]
    if result_view.duplicated(subset=identity, keep=False).any():
        raise ValueError("Duplicate RPL finished-result fixture identity")
    result_view = result_view.rename(columns={"result": "actual_result"})

    settled = ledger.merge(
        result_view,
        on=identity,
        how="inner",
        validate="many_to_one",
    )
    if settled.empty:
        return settled

    settled["prediction_correct"] = (
        settled["market_pick"] == settled["actual_result"]
    )
    settled["actual_result_probability"] = [
        float(getattr(row, shared.PROBABILITY_COLUMNS[row.actual_result]))
        for row in settled.itertuples(index=False)
    ]
    return settled


def evaluate_frames(
    ledger: pd.DataFrame,
    results: pd.DataFrame,
):
    ledger = shared._validate_ledger(ledger)
    results = shared._validate_results(results)
    settled = settle_rpl_predictions(ledger, results)
    latest = shared.latest_pre_kickoff(settled)

    all_metrics = shared.calculate_metrics(settled, view="ALL_SNAPSHOTS")
    latest_metrics = shared.calculate_metrics(
        latest,
        view="LATEST_PRE_KICKOFF_PER_FIXTURE",
    )
    return settled, latest, all_metrics, latest_metrics


def main() -> None:
    ledger = shared.load_ledger(LEAGUE)
    results = shared.load_results(LEAGUE)
    settled, latest, all_metrics, latest_metrics = evaluate_frames(
        ledger,
        results,
    )

    print("=" * 88)
    print("RPL CANONICAL PREDICTION EVALUATION")
    print("=" * 88)
    print("ledger rows:", len(ledger))
    print("finished result rows:", len(results))
    print("settled rows:", len(settled))
    print("settled fixtures:", settled["event_id"].nunique() if not settled.empty else 0)
    print("MARKET_ONLY rows:", int((ledger.get("prediction_mode", pd.Series(dtype=str)) == "MARKET_ONLY").sum()))
    print("Structural applied rows:", int(ledger.get("structural_applied", pd.Series(dtype=bool)).fillna(False).astype(bool).sum()))
    shared._print_metrics(all_metrics)
    shared._print_metrics(latest_metrics)

    if not latest.empty:
        columns = [
            "home_team",
            "away_team",
            "kickoff_utc",
            "snapshot_time_utc",
            "market_pick",
            "actual_result",
            "actual_result_probability",
            "prediction_correct",
        ]
        print()
        print(latest[columns].to_string(index=False))

    print()
    print("evaluation timezone:", TIMEZONE)
    print("Supabase writes:", False)
    print("production model used:", False)
    print("Structural V2 activation:", False)


if __name__ == "__main__":
    main()
