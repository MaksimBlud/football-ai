"""Read-only canonical league prediction evaluator.

Joins immutable prediction-ledger rows with immutable finished results using
league-local match dates. No writes, training, promotion, or Structural V2
activation occur here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from database import supabase
from league_config import get_league_config
from team_names import normalize_team_name

LEDGER_TABLE = "league_prediction_ledger"
RESULT_TABLE = "league_finished_results"
OUTCOMES = ("H", "D", "A")
PROBABILITY_COLUMNS = {
    "H": "market_home_prob",
    "D": "market_draw_prob",
    "A": "market_away_prob",
}


@dataclass(frozen=True)
class EvaluationMetrics:
    view: str
    prediction_rows: int
    fixtures: int
    correct: int
    accuracy: float | None
    log_loss: float | None
    brier: float | None
    mean_actual_probability: float | None


@dataclass(frozen=True)
class EvaluationReport:
    league: str
    ledger_rows: int
    result_rows: int
    settled_rows: int
    settled_fixtures: int
    market_only_rows: int
    structural_rows: int
    all_snapshots: EvaluationMetrics
    latest_pre_kickoff: EvaluationMetrics


def _response_rows(response):
    return list(getattr(response, "data", None) or [])


def load_ledger(league: str) -> pd.DataFrame:
    response = (
        supabase.table(LEDGER_TABLE)
        .select("*")
        .eq("league", league)
        .execute()
    )
    return pd.DataFrame(_response_rows(response))


def load_results(league: str) -> pd.DataFrame:
    response = (
        supabase.table(RESULT_TABLE)
        .select("*")
        .eq("league", league)
        .execute()
    )
    return pd.DataFrame(_response_rows(response))


def _team_key(value) -> str:
    return normalize_team_name(str(value))


def _validate_ledger(ledger: pd.DataFrame) -> pd.DataFrame:
    if ledger.empty:
        return ledger.copy()

    required = {
        "league", "event_id", "home_team", "away_team", "kickoff_utc",
        "snapshot_time_utc", "market_home_prob", "market_draw_prob",
        "market_away_prob", "market_pick", "prediction_mode",
        "structural_applied",
    }
    missing = required - set(ledger.columns)
    if missing:
        raise ValueError("Ledger missing columns: " + ", ".join(sorted(missing)))

    work = ledger.copy()
    work["kickoff_utc"] = pd.to_datetime(work["kickoff_utc"], utc=True, errors="coerce")
    work["snapshot_time_utc"] = pd.to_datetime(
        work["snapshot_time_utc"], utc=True, errors="coerce"
    )
    if work[["kickoff_utc", "snapshot_time_utc"]].isna().any().any():
        raise ValueError("Ledger contains invalid timestamps")
    if not (work["snapshot_time_utc"] < work["kickoff_utc"]).all():
        raise ValueError("Ledger contains non-pre-kickoff predictions")

    columns = ["market_home_prob", "market_draw_prob", "market_away_prob"]
    probabilities = work[columns].apply(pd.to_numeric, errors="coerce")
    matrix = probabilities.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("Ledger contains non-finite probabilities")
    if (matrix < 0.0).any() or (matrix > 1.0).any():
        raise ValueError("Ledger probability outside [0,1]")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError("Ledger market probabilities do not sum to one")
    work[columns] = probabilities

    work["market_pick"] = work["market_pick"].astype(str).str.upper()
    if not work["market_pick"].isin(OUTCOMES).all():
        raise ValueError("Invalid market_pick")
    derived = np.asarray(OUTCOMES)[np.argmax(matrix, axis=1)]
    if not np.array_equal(derived, work["market_pick"].to_numpy()):
        raise ValueError("market_pick disagrees with probabilities")
    return work


def _validate_results(results: pd.DataFrame) -> pd.DataFrame:
    if results.empty:
        return results.copy()

    required = {"league", "match_date", "home_team", "away_team", "result"}
    missing = required - set(results.columns)
    if missing:
        raise ValueError("Results missing columns: " + ", ".join(sorted(missing)))

    work = results.copy()
    work["match_date"] = pd.to_datetime(work["match_date"], errors="coerce").dt.date
    if work["match_date"].isna().any():
        raise ValueError("Invalid result match_date")
    work["result"] = work["result"].astype(str).str.upper()
    if not work["result"].isin(OUTCOMES).all():
        raise ValueError("Invalid finished result")
    return work


def _assert_league(frame: pd.DataFrame, league: str, label: str) -> None:
    if frame.empty:
        return
    values = set(frame["league"].astype(str))
    if values != {league}:
        raise ValueError(f"{label} contains foreign league rows for {league}: {sorted(values)}")


def _resolve_league(ledger: pd.DataFrame, results: pd.DataFrame, league: str | None) -> str:
    if league is not None:
        return str(league)
    values: set[str] = set()
    if not ledger.empty:
        values.update(ledger["league"].astype(str).unique())
    if not results.empty:
        values.update(results["league"].astype(str).unique())
    if len(values) != 1:
        raise ValueError("Cannot infer a single league for settlement")
    return next(iter(values))


def settle_predictions(
    ledger: pd.DataFrame,
    results: pd.DataFrame,
    *,
    league: str | None = None,
    timezone: str | None = None,
) -> pd.DataFrame:
    ledger = _validate_ledger(ledger)
    results = _validate_results(results)
    if ledger.empty or results.empty:
        return pd.DataFrame()

    league = _resolve_league(ledger, results, league)
    _assert_league(ledger, league, "Ledger")
    _assert_league(results, league, "Results")
    timezone = timezone or get_league_config(league).timezone

    ledger = ledger.copy()
    results = results.copy()
    ledger["_match_date"] = ledger["kickoff_utc"].dt.tz_convert(timezone).dt.date
    ledger["_home_key"] = ledger["home_team"].map(_team_key)
    ledger["_away_key"] = ledger["away_team"].map(_team_key)
    results["_match_date"] = results["match_date"]
    results["_home_key"] = results["home_team"].map(_team_key)
    results["_away_key"] = results["away_team"].map(_team_key)

    identity = ["_match_date", "_home_key", "_away_key"]
    result_view = results[identity + ["result"]].copy()
    if result_view.duplicated(subset=identity, keep=False).any():
        raise ValueError("Duplicate finished-result fixture identity")
    result_view = result_view.rename(columns={"result": "actual_result"})

    settled = ledger.merge(result_view, on=identity, how="inner", validate="many_to_one")
    if settled.empty:
        return settled
    settled["prediction_correct"] = settled["market_pick"] == settled["actual_result"]
    settled["actual_result_probability"] = [
        float(getattr(row, PROBABILITY_COLUMNS[row.actual_result]))
        for row in settled.itertuples(index=False)
    ]
    return settled


def latest_pre_kickoff(settled: pd.DataFrame) -> pd.DataFrame:
    if settled.empty:
        return settled.copy()
    if "event_id" not in settled.columns:
        raise ValueError("event_id required for latest prediction view")
    return (
        settled.sort_values(["event_id", "snapshot_time_utc"])
        .drop_duplicates(subset=["event_id"], keep="last")
        .reset_index(drop=True)
    )


def calculate_metrics(frame: pd.DataFrame, *, view: str) -> EvaluationMetrics:
    if frame.empty:
        return EvaluationMetrics(view, 0, 0, 0, None, None, None, None)

    probs = frame[["market_home_prob", "market_draw_prob", "market_away_prob"]].to_numpy(dtype=float)
    actual = frame["actual_result"].map({"H": 0, "D": 1, "A": 2}).to_numpy(dtype=int)
    one_hot = np.zeros_like(probs)
    one_hot[np.arange(len(frame)), actual] = 1.0
    actual_probs = probs[np.arange(len(frame)), actual]
    correct = int(frame["prediction_correct"].sum())
    return EvaluationMetrics(
        view=view,
        prediction_rows=len(frame),
        fixtures=int(frame["event_id"].nunique()),
        correct=correct,
        accuracy=float(correct / len(frame)),
        log_loss=float(-np.mean(np.log(np.clip(actual_probs, 1e-15, 1.0)))),
        brier=float(np.mean(np.sum((probs - one_hot) ** 2, axis=1))),
        mean_actual_probability=float(np.mean(actual_probs)),
    )


def evaluate_frames(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> tuple[EvaluationReport, pd.DataFrame, pd.DataFrame]:
    ledger = _validate_ledger(ledger)
    results = _validate_results(results)
    _assert_league(ledger, league, "Ledger")
    _assert_league(results, league, "Results")

    settled = settle_predictions(ledger, results, league=league)
    latest = latest_pre_kickoff(settled)
    market_only_rows = int((ledger["prediction_mode"] == "MARKET_ONLY").sum()) if not ledger.empty else 0
    structural_rows = int(ledger["structural_applied"].fillna(False).astype(bool).sum()) if not ledger.empty else 0
    all_metrics = calculate_metrics(settled, view="ALL_SNAPSHOTS")
    latest_metrics = calculate_metrics(latest, view="LATEST_PRE_KICKOFF_PER_FIXTURE")

    report = EvaluationReport(
        league=league,
        ledger_rows=len(ledger),
        result_rows=len(results),
        settled_rows=len(settled),
        settled_fixtures=int(settled["event_id"].nunique()) if not settled.empty else 0,
        market_only_rows=market_only_rows,
        structural_rows=structural_rows,
        all_snapshots=all_metrics,
        latest_pre_kickoff=latest_metrics,
    )
    return report, settled, latest


def evaluate_league(league: str) -> tuple[EvaluationReport, pd.DataFrame, pd.DataFrame]:
    get_league_config(league)
    return evaluate_frames(league, load_ledger(league), load_results(league))


def _print_metrics(metrics: EvaluationMetrics) -> None:
    print()
    print("=" * 88)
    print(metrics.view)
    print("=" * 88)
    print("prediction rows:", metrics.prediction_rows)
    print("fixtures:", metrics.fixtures)
    print("correct:", metrics.correct)
    print("accuracy:", metrics.accuracy)
    print("log loss:", metrics.log_loss)
    print("multiclass brier:", metrics.brier)
    print("mean actual-result probability:", metrics.mean_actual_probability)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--league", default="EPL")
    args = parser.parse_args()
    report, settled, latest = evaluate_league(args.league)

    print("=" * 88)
    print(f"{report.league} CANONICAL PREDICTION EVALUATION")
    print("=" * 88)
    print("ledger rows:", report.ledger_rows)
    print("finished result rows:", report.result_rows)
    print("settled rows:", report.settled_rows)
    print("settled fixtures:", report.settled_fixtures)
    print("MARKET_ONLY rows:", report.market_only_rows)
    print("Structural applied rows:", report.structural_rows)
    _print_metrics(report.all_snapshots)
    _print_metrics(report.latest_pre_kickoff)

    if not latest.empty:
        columns = [
            "home_team", "away_team", "kickoff_utc", "snapshot_time_utc",
            "market_pick", "actual_result", "actual_result_probability",
            "prediction_correct",
        ]
        print()
        print(latest[columns].sort_values("kickoff_utc").to_string(index=False))

    print()
    print("PASS: READ-ONLY CANONICAL EVALUATION COMPLETE")


if __name__ == "__main__":
    main()
