"""Read-only canonical ledger/result data-quality audit.

This audit validates research state before calibration. It performs no writes,
training, promotion, Structural V2 activation, or model loading.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

import evaluate_league_predictions as evaluator
from league_config import operational_collection_ready_leagues
from normalize_la_liga_history import normalize_team as normalize_la_liga_team


@dataclass(frozen=True)
class DataQualityReport:
    league: str
    ledger_rows: int
    result_rows: int
    settled_rows: int
    settled_fixtures: int
    duplicate_prediction_rows: int
    duplicate_result_identities: int
    alias_duplicate_result_rows: int
    pre_ledger_alias_duplicate_result_rows: int
    post_ledger_alias_duplicate_result_rows: int
    alias_conflicting_result_rows: int
    missing_event_ids: int
    ambiguous_event_identities: int
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


def _audit_team_key(league: str, value) -> str:
    """Normalize known source aliases only for duplicate-detection diagnostics.

    The evaluator's settlement identity remains unchanged. La Liga has legacy
    immutable Football-Data rows written before its market-canonical naming
    bridge was established; this audit must still recognize those rows as the
    same football fixture.
    """
    if league == "LA_LIGA":
        return evaluator._team_key(normalize_la_liga_team(str(value)))
    return evaluator._team_key(value)


def _alias_duplicate_result_metrics(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> tuple[int, int, int, int, int]:
    """Return total/pre-ledger/post-ledger/conflicting/critical alias rows."""
    if results.empty:
        return 0, 0, 0, 0, 0

    work = evaluator._validate_results(results)
    work["_home_key"] = work["home_team"].map(lambda value: _audit_team_key(league, value))
    work["_away_key"] = work["away_team"].map(lambda value: _audit_team_key(league, value))
    identity = ["league", "match_date", "_home_key", "_away_key"]
    duplicate_mask = work.duplicated(subset=identity, keep=False)
    total = int(duplicate_mask.sum())
    if total == 0:
        return 0, 0, 0, 0, 0

    duplicate_work = work.loc[duplicate_mask].copy()
    conflicting_keys: set[tuple] = set()
    for key, group in duplicate_work.groupby(identity, dropna=False, sort=False):
        outcome_columns = ["result"]
        if {"home_goals", "away_goals"}.issubset(group.columns):
            outcome_columns.extend(["home_goals", "away_goals"])
        if len(group[outcome_columns].drop_duplicates()) > 1:
            conflicting_keys.add(tuple(key) if isinstance(key, tuple) else (key,))

    conflict_mask = pd.Series(False, index=work.index)
    if conflicting_keys:
        row_keys = list(map(tuple, work[identity].to_numpy()))
        conflict_mask = pd.Series(
            [key in conflicting_keys for key in row_keys], index=work.index
        ) & duplicate_mask
    conflicting = int(conflict_mask.sum())

    first_ledger_date = None
    if not ledger.empty:
        ledger_work = evaluator._validate_ledger(ledger)
        timezone = evaluator.get_league_config(league).timezone
        first_ledger_date = ledger_work["kickoff_utc"].dt.tz_convert(timezone).dt.date.min()

    if first_ledger_date is None:
        post_mask = pd.Series(False, index=work.index)
    else:
        post_mask = duplicate_mask & work["match_date"].ge(first_ledger_date)
    post = int(post_mask.sum())
    pre = int(total - post)
    critical_mask = post_mask | conflict_mask
    critical = int(critical_mask.sum())
    return total, pre, post, conflicting, critical


def _missing_event_ids(ledger: pd.DataFrame) -> int:
    if ledger.empty:
        return 0
    if "event_id" not in ledger.columns:
        raise ValueError("Ledger missing event_id")
    values = ledger["event_id"]
    return int((values.isna() | values.astype(str).str.strip().eq("")).sum())


def _ambiguous_event_identities(ledger: pd.DataFrame) -> int:
    if ledger.empty:
        return 0
    validated = evaluator._validate_ledger(ledger)
    return len(evaluator.ambiguous_event_ids(validated))


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
    (
        alias_duplicates,
        pre_ledger_alias_duplicates,
        post_ledger_alias_duplicates,
        alias_conflicts,
        alias_critical,
    ) = _alias_duplicate_result_metrics(league, ledger, results)
    missing_event_ids = _missing_event_ids(ledger)
    ambiguous_events = _ambiguous_event_identities(ledger)
    unlinked_results = _unlinked_finished_results(league, ledger, results)
    # Exact duplicate identities remain critical. Alias-equivalent rows are
    # additionally critical only if they overlap the canonical ledger era or
    # disagree on the immutable outcome. Rescheduled event ids are visible as
    # diagnostics but are excluded from automatic evaluator settlement rather
    # than treated as corrupt immutable history.
    critical = duplicate_predictions + duplicate_results + missing_event_ids + alias_critical

    return DataQualityReport(
        league=league,
        ledger_rows=int(evaluation.ledger_rows),
        result_rows=int(evaluation.result_rows),
        settled_rows=len(settled),
        settled_fixtures=int(evaluation.settled_fixtures),
        duplicate_prediction_rows=duplicate_predictions,
        duplicate_result_identities=duplicate_results,
        alias_duplicate_result_rows=alias_duplicates,
        pre_ledger_alias_duplicate_result_rows=pre_ledger_alias_duplicates,
        post_ledger_alias_duplicate_result_rows=post_ledger_alias_duplicates,
        alias_conflicting_result_rows=alias_conflicts,
        missing_event_ids=missing_event_ids,
        ambiguous_event_identities=ambiguous_events,
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
            f"duplicate_results={row['duplicate_result_identities']}, "
            f"alias_duplicates={row['alias_duplicate_result_rows']}, "
            f"pre_ledger_alias_duplicates={row['pre_ledger_alias_duplicate_result_rows']}, "
            f"post_ledger_alias_duplicates={row['post_ledger_alias_duplicate_result_rows']}, "
            f"alias_conflicts={row['alias_conflicting_result_rows']}, "
            f"missing_event_ids={row['missing_event_ids']}, "
            f"ambiguous_event_ids={row['ambiguous_event_identities']}, "
            f"unlinked_results={row['unlinked_finished_results']}, critical={row['critical_failures']}"
        )
    print()
    print("PASS: READ-ONLY CANONICAL DATA QUALITY AUDIT COMPLETE")


if __name__ == "__main__":
    main()
