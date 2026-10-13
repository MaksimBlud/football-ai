"""Read-only Serie A canonical prediction evaluator using Europe/Rome dates."""

from __future__ import annotations

import pandas as pd

import evaluate_league_predictions as shared
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG
from team_names import normalize_team_name

LEAGUE = SERIE_A_RUNTIME_CONFIG.identity.identifier
TIMEZONE = SERIE_A_RUNTIME_CONFIG.identity.timezone


def settle_serie_a_predictions(ledger: pd.DataFrame, results: pd.DataFrame) -> pd.DataFrame:
    ledger = shared._validate_ledger(ledger)
    results = shared._validate_results(results)
    if ledger.empty or results.empty:
        return pd.DataFrame()
    if not (ledger["league"].astype(str) == LEAGUE).all():
        raise ValueError("Serie A evaluator received foreign ledger rows")
    if not (results["league"].astype(str) == LEAGUE).all():
        raise ValueError("Serie A evaluator received foreign result rows")
    ledger = ledger.copy()
    results = results.copy()
    ledger["_match_date"] = ledger["kickoff_utc"].dt.tz_convert(TIMEZONE).dt.date
    ledger["_home_key"] = ledger["home_team"].map(lambda value: normalize_team_name(str(value)))
    ledger["_away_key"] = ledger["away_team"].map(lambda value: normalize_team_name(str(value)))
    results["_match_date"] = results["match_date"]
    results["_home_key"] = results["home_team"].map(lambda value: normalize_team_name(str(value)))
    results["_away_key"] = results["away_team"].map(lambda value: normalize_team_name(str(value)))
    identity = ["_match_date", "_home_key", "_away_key"]
    result_view = results[identity + ["result"]].copy()
    duplicate_mask = result_view.duplicated(subset=identity, keep=False)
    if duplicate_mask.any():
        # Legacy provider rows sometimes carry two raw spellings of the
        # same club. Never multiply one settlement or choose between
        # inconsistent scores; source/provenance rows stay immutable.
        score_columns = ("home_goals", "away_goals")
        if not set(score_columns).issubset(results.columns):
            raise ValueError("Duplicate Serie A result cannot be verified without goals")
        check = results.loc[duplicate_mask, identity + [
            "home_team", "away_team", "result", *score_columns,
        ]].copy()
        for field in score_columns:
            check[field] = pd.to_numeric(check[field], errors="coerce")
        if check[list(score_columns)].isna().any().any():
            raise ValueError("Duplicate Serie A result has unknown goals")
        for _, group in check.groupby(identity, sort=False, dropna=False):
            distinct_raw_teams = group[["home_team", "away_team"]].drop_duplicates()
            distinct_outcomes = group[["result", *score_columns]].drop_duplicates()
            if len(distinct_raw_teams) < 2 or len(distinct_outcomes) != 1:
                raise ValueError("Conflicting duplicate Serie A finished-result fixture identity")
        result_view = result_view.drop_duplicates(subset=identity, keep="first")
    result_view = result_view.rename(columns={"result": "actual_result"})
    settled = ledger.merge(result_view, on=identity, how="inner", validate="many_to_one")
    if settled.empty:
        return settled
    settled["prediction_correct"] = settled["market_pick"] == settled["actual_result"]
    settled["actual_result_probability"] = [
        float(getattr(row, shared.PROBABILITY_COLUMNS[row.actual_result]))
        for row in settled.itertuples(index=False)
    ]
    return settled


def evaluate_frames(ledger: pd.DataFrame, results: pd.DataFrame):
    ledger = shared._validate_ledger(ledger)
    results = shared._validate_results(results)
    settled = settle_serie_a_predictions(ledger, results)
    latest = shared.latest_pre_kickoff(settled)
    all_metrics = shared.calculate_metrics(settled, view="ALL_SNAPSHOTS")
    latest_metrics = shared.calculate_metrics(latest, view="LATEST_PRE_KICKOFF_PER_FIXTURE")
    return settled, latest, all_metrics, latest_metrics


def main() -> None:
    ledger = shared.load_ledger(LEAGUE)
    results = shared.load_results(LEAGUE)
    settled, latest, all_metrics, latest_metrics = evaluate_frames(ledger, results)
    print("=" * 88)
    print("SERIE A CANONICAL PREDICTION EVALUATION")
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
            "home_team", "away_team", "kickoff_utc", "snapshot_time_utc",
            "market_pick", "actual_result", "actual_result_probability", "prediction_correct",
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
