"""Read-only canonical ledger/result data-quality audit.

This audit validates research state before calibration. It performs no writes,
training, promotion, Structural V2 activation, or model loading.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

import evaluate_league_predictions as evaluator
from league_config import operational_collection_ready_leagues


@dataclass(frozen=True)
class DataQualityReport:
    league: str
    ledger_rows: int
    result_rows: int
    settled_rows: int
    settled_fixtures: int
    duplicate_prediction_rows: int
    duplicate_result_identities: int
    missing_event_ids: int
    unlinked_finished_results: int
    critical_failures: int


def _duplicate_prediction_rows(ledger: pd.DataFrame) -> int:
    if ledger.empty:
        return 0
    required = ["league", "event_id", "snapshot_time_utc", "prediction_mode"]
    missing = set(required) - set(ledger.columns)
    if missing:
        raise ValueError("Ledger missing audit columns: " + ", ".join(sorted(missing)))
    return int(ledger.duplicated(subset=required, keep=False).sum())


def _duplicate_result_identities(results: pd.DataFrame) -> int:
    if results.empty:
        return 0
    required = ["league", "match_date", "home_team", "away_team"]
    missing = set(required) - set(results.columns)
    if missing:
        raise ValueError("Results missing audit columns: " + ", ".join(sorted(missing)))
    work = evaluator._validate_results(results)
    work["_home_key"] = work["home_team"].map(evaluator._team_key)
    work["_away_key"] = work["away_team"].map(evaluator._team_key)
    identity = ["league", "match_date", "_home_key", "_away_key"]
    return int(work.duplicated(subset=identity, keep=False).sum())


def _missing_event_ids(ledger: pd.DataFrame) -> int:
    if ledger.empty:
        return 0
    if "event_id" not in ledger.columns:
        raise ValueError("Ledger missing event_id")
    values = ledger["event_id"]
    return int((values.isna() | values.astype(str).str.strip().eq("")).sum())


def _unlinked_finished_results(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> int:
    if results.empty:
        return 0
    if ledger.empty:
        return len(results)

    ledger_work = evaluator._validate_ledger(ledger)
    result_work = evaluator._validate_results(results)
    timezone = evaluator.get_league_config(league).timezone

    ledger_work["_match_date"] = ledger_work["kickoff_utc"].dt.tz_convert(timezone).dt.date
    ledger_work["_home_key"] = ledger_work["home_team"].map(evaluator._team_key)
    ledger_work["_away_key"] = ledger_work["away_team"].map(evaluator._team_key)
    result_work["_match_date"] = result_work["match_date"]
    result_work["_home_key"] = result_work["home_team"].map(evaluator._team_key)
    result_work["_away_key"] = result_work["away_team"].map(evaluator._team_key)

    identity = ["_match_date", "_home_key", "_away_key"]
    prediction_ids = set(map(tuple, ledger_work[identity].drop_duplicates().to_numpy()))
    result_ids = list(map(tuple, result_work[identity].to_numpy()))
    return sum(identity_row not in prediction_ids for identity_row in result_ids)


def audit_frames(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> DataQualityReport:
    # Reuse canonical validators so post-kickoff rows, invalid probabilities,
    # foreign-league rows and invalid results fail closed.
    evaluation, settled, _latest = evaluator.evaluate_frames(league, ledger, results)

    duplicate_predictions = _duplicate_prediction_rows(ledger)
    duplicate_results = _duplicate_result_identities(results)
    missing_event_ids = _missing_event_ids(ledger)
    unlinked_results = _unlinked_finished_results(league, ledger, results)
    critical = duplicate_predictions + duplicate_results + missing_event_ids

    return DataQualityReport(
        league=league,
        ledger_rows=int(evaluation.ledger_rows),
        result_rows=int(evaluation.result_rows),
        settled_rows=len(settled),
        settled_fixtures=int(evaluation.settled_fixtures),
        duplicate_prediction_rows=duplicate_predictions,
        duplicate_result_identities=duplicate_results,
        missing_event_ids=missing_event_ids,
        unlinked_finished_results=int(unlinked_results),
        critical_failures=int(critical),
    )


def audit_league(league: str) -> DataQualityReport:
    return audit_frames(
        league,
        evaluator.load_ledger(league),
        evaluator.load_results(league),
    )


def build_audit_report() -> list[dict]:
    return [asdict(audit_league(config.identifier)) for config in operational_collection_ready_leagues()]


def main() -> None:
    rows = build_audit_report()
    print("CANONICAL LEAGUE DATA QUALITY AUDIT")
    print("Read-only: no writes, training, promotion, or Structural activation.")
    print()
    for row in rows:
        print(
            f"{row['league']}: ledger={row['ledger_rows']}, results={row['result_rows']}, "
            f"settled={row['settled_fixtures']}, duplicate_predictions={row['duplicate_prediction_rows']}, "
            f"duplicate_results={row['duplicate_result_identities']}, missing_event_ids={row['missing_event_ids']}, "
            f"unlinked_results={row['unlinked_finished_results']}, critical={row['critical_failures']}"
        )
    print()
    print("PASS: READ-ONLY CANONICAL DATA QUALITY AUDIT COMPLETE")


if __name__ == "__main__":
    main()
