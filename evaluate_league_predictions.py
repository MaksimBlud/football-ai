"""Read-only canonical league prediction evaluator.

Joins immutable prediction-ledger rows with immutable finished results.

Evaluation views:
- ALL_SNAPSHOTS
- LATEST_PRE_KICKOFF_PER_FIXTURE

Metrics:
- accuracy
- multiclass log loss
- multiclass Brier score
- mean probability assigned to the realized result

No writes, no training, no promotion, no Structural V2 activation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from database import supabase
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
    return list(
        getattr(
            response,
            "data",
            None,
        )
        or []
    )


def load_ledger(
    league: str,
) -> pd.DataFrame:
    response = (
        supabase
        .table(LEDGER_TABLE)
        .select("*")
        .eq(
            "league",
            league,
        )
        .execute()
    )

    return pd.DataFrame(
        _response_rows(response)
    )


def load_results(
    league: str,
) -> pd.DataFrame:
    response = (
        supabase
        .table(RESULT_TABLE)
        .select("*")
        .eq(
            "league",
            league,
        )
        .execute()
    )

    return pd.DataFrame(
        _response_rows(response)
    )


def _team_key(
    value,
) -> str:
    return normalize_team_name(
        str(value)
    )


def _validate_ledger(
    ledger: pd.DataFrame,
) -> pd.DataFrame:
    if ledger.empty:
        return ledger.copy()

    required = {
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "snapshot_time_utc",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "market_pick",
        "prediction_mode",
        "structural_applied",
    }

    missing = required - set(
        ledger.columns
    )

    if missing:
        raise ValueError(
            "Ledger missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    work = ledger.copy()

    work["kickoff_utc"] = pd.to_datetime(
        work["kickoff_utc"],
        utc=True,
        errors="coerce",
    )

    work["snapshot_time_utc"] = pd.to_datetime(
        work["snapshot_time_utc"],
        utc=True,
        errors="coerce",
    )

    if work[
        [
            "kickoff_utc",
            "snapshot_time_utc",
        ]
    ].isna().any().any():
        raise ValueError(
            "Ledger contains invalid timestamps"
        )

    if not (
        work["snapshot_time_utc"]
        < work["kickoff_utc"]
    ).all():
        raise ValueError(
            "Ledger contains non-pre-kickoff predictions"
        )

    probabilities = work[
        [
            "market_home_prob",
            "market_draw_prob",
            "market_away_prob",
        ]
    ].apply(
        pd.to_numeric,
        errors="coerce",
    )

    matrix = probabilities.to_numpy(
        dtype=float
    )

    if not np.isfinite(
        matrix
    ).all():
        raise ValueError(
            "Ledger contains non-finite probabilities"
        )

    if (
        (matrix < 0.0).any()
        or
        (matrix > 1.0).any()
    ):
        raise ValueError(
            "Ledger probability outside [0,1]"
        )

    if not np.allclose(
        matrix.sum(axis=1),
        1.0,
        atol=1e-9,
    ):
        raise ValueError(
            "Ledger market probabilities do not sum to one"
        )

    work[
        [
            "market_home_prob",
            "market_draw_prob",
            "market_away_prob",
        ]
    ] = probabilities

    work["market_pick"] = (
        work["market_pick"]
        .astype(str)
        .str.upper()
    )

    if not work[
        "market_pick"
    ].isin(
        OUTCOMES
    ).all():
        raise ValueError(
            "Invalid market_pick"
        )

    derived = np.asarray(
        OUTCOMES
    )[
        np.argmax(
            matrix,
            axis=1,
        )
    ]

    if not np.array_equal(
        derived,
        work[
            "market_pick"
        ].to_numpy(),
    ):
        raise ValueError(
            "market_pick disagrees with probabilities"
        )

    return work


def _validate_results(
    results: pd.DataFrame,
) -> pd.DataFrame:
    if results.empty:
        return results.copy()

    required = {
        "league",
        "match_date",
        "home_team",
        "away_team",
        "result",
    }

    missing = required - set(
        results.columns
    )

    if missing:
        raise ValueError(
            "Results missing columns: "
            + ", ".join(
                sorted(missing)
            )
        )

    work = results.copy()

    work["match_date"] = (
        pd.to_datetime(
            work["match_date"],
            errors="coerce",
        )
        .dt
        .date
    )

    if work[
        "match_date"
    ].isna().any():
        raise ValueError(
            "Invalid result match_date"
        )

    work["result"] = (
        work["result"]
        .astype(str)
        .str.upper()
    )

    if not work[
        "result"
    ].isin(
        OUTCOMES
    ).all():
        raise ValueError(
            "Invalid finished result"
        )

    return work


def settle_predictions(
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> pd.DataFrame:
    ledger = _validate_ledger(
        ledger
    )

    results = _validate_results(
        results
    )

    if (
        ledger.empty
        or results.empty
    ):
        return pd.DataFrame()

    ledger = ledger.copy()
    results = results.copy()

    ledger["_match_date"] = (
        ledger[
            "kickoff_utc"
        ]
        .dt
        .tz_convert(
            "Europe/London"
        )
        .dt
        .date
    )

    ledger["_home_key"] = (
        ledger[
            "home_team"
        ]
        .map(
            _team_key
        )
    )

    ledger["_away_key"] = (
        ledger[
            "away_team"
        ]
        .map(
            _team_key
        )
    )

    results["_match_date"] = (
        results[
            "match_date"
        ]
    )

    results["_home_key"] = (
        results[
            "home_team"
        ]
        .map(
            _team_key
        )
    )

    results["_away_key"] = (
        results[
            "away_team"
        ]
        .map(
            _team_key
        )
    )

    result_view = results[
        [
            "_match_date",
            "_home_key",
            "_away_key",
            "result",
        ]
    ].copy()

    duplicate_results = (
        result_view
        .duplicated(
            subset=[
                "_match_date",
                "_home_key",
                "_away_key",
            ],
            keep=False,
        )
    )

    if duplicate_results.any():
        raise ValueError(
            "Duplicate finished-result fixture identity"
        )

    result_view = result_view.rename(
        columns={
            "result":
                "actual_result",
        }
    )

    settled = ledger.merge(
        result_view,
        on=[
            "_match_date",
            "_home_key",
            "_away_key",
        ],
        how="inner",
        validate="many_to_one",
    )

    if settled.empty:
        return settled

    settled[
        "prediction_correct"
    ] = (
        settled[
            "market_pick"
        ]
        == settled[
            "actual_result"
        ]
    )

    actual_probability = []

    for row in settled.itertuples(
        index=False
    ):
        outcome = row.actual_result

        column = (
            PROBABILITY_COLUMNS[
                outcome
            ]
        )

        actual_probability.append(
            float(
                getattr(
                    row,
                    column,
                )
            )
        )

    settled[
        "actual_result_probability"
    ] = actual_probability

    return settled


def latest_pre_kickoff(
    settled: pd.DataFrame,
) -> pd.DataFrame:
    if settled.empty:
        return settled.copy()

    if "event_id" not in settled.columns:
        raise ValueError(
            "event_id required for latest prediction view"
        )

    ordered = (
        settled
        .sort_values(
            [
                "event_id",
                "snapshot_time_utc",
            ]
        )
    )

    latest = (
        ordered
        .drop_duplicates(
            subset=[
                "event_id",
            ],
            keep="last",
        )
        .reset_index(
            drop=True
        )
    )

    return latest


def calculate_metrics(
    frame: pd.DataFrame,
    *,
    view: str,
) -> EvaluationMetrics:
    if frame.empty:
        return EvaluationMetrics(
            view=view,
            prediction_rows=0,
            fixtures=0,
            correct=0,
            accuracy=None,
            log_loss=None,
            brier=None,
            mean_actual_probability=None,
        )

    probs = frame[
        [
            "market_home_prob",
            "market_draw_prob",
            "market_away_prob",
        ]
    ].to_numpy(
        dtype=float
    )

    actual = (
        frame[
            "actual_result"
        ]
        .map(
            {
                "H": 0,
                "D": 1,
                "A": 2,
            }
        )
        .to_numpy(
            dtype=int
        )
    )

    one_hot = np.zeros_like(
        probs
    )

    one_hot[
        np.arange(
            len(frame)
        ),
        actual,
    ] = 1.0

    actual_probs = probs[
        np.arange(
            len(frame)
        ),
        actual,
    ]

    clipped = np.clip(
        actual_probs,
        1e-15,
        1.0,
    )

    correct = int(
        frame[
            "prediction_correct"
        ]
        .sum()
    )

    accuracy = (
        correct
        / len(frame)
    )

    log_loss = float(
        -np.mean(
            np.log(
                clipped
            )
        )
    )

    brier = float(
        np.mean(
            np.sum(
                (
                    probs
                    - one_hot
                )
                ** 2,
                axis=1,
            )
        )
    )

    mean_actual_probability = float(
        np.mean(
            actual_probs
        )
    )

    fixtures = int(
        frame[
            "event_id"
        ]
        .nunique()
    )

    return EvaluationMetrics(
        view=view,
        prediction_rows=len(frame),
        fixtures=fixtures,
        correct=correct,
        accuracy=float(
            accuracy
        ),
        log_loss=log_loss,
        brier=brier,
        mean_actual_probability=(
            mean_actual_probability
        ),
    )


def evaluate_frames(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> tuple[
    EvaluationReport,
    pd.DataFrame,
    pd.DataFrame,
]:
    ledger = _validate_ledger(
        ledger
    )

    results = _validate_results(
        results
    )

    settled = settle_predictions(
        ledger,
        results,
    )

    latest = latest_pre_kickoff(
        settled
    )

    market_only_rows = 0
    structural_rows = 0

    if not ledger.empty:
        market_only_rows = int(
            (
                ledger[
                    "prediction_mode"
                ]
                == "MARKET_ONLY"
            )
            .sum()
        )

        structural_rows = int(
            ledger[
                "structural_applied"
            ]
            .fillna(False)
            .astype(bool)
            .sum()
        )

    all_metrics = calculate_metrics(
        settled,
        view="ALL_SNAPSHOTS",
    )

    latest_metrics = calculate_metrics(
        latest,
        view=(
            "LATEST_PRE_KICKOFF_PER_FIXTURE"
        ),
    )

    report = EvaluationReport(
        league=league,
        ledger_rows=len(
            ledger
        ),
        result_rows=len(
            results
        ),
        settled_rows=len(
            settled
        ),
        settled_fixtures=int(
            settled[
                "event_id"
            ].nunique()
        )
        if not settled.empty
        else 0,
        market_only_rows=(
            market_only_rows
        ),
        structural_rows=(
            structural_rows
        ),
        all_snapshots=(
            all_metrics
        ),
        latest_pre_kickoff=(
            latest_metrics
        ),
    )

    return (
        report,
        settled,
        latest,
    )


def evaluate_league(
    league: str,
) -> tuple[
    EvaluationReport,
    pd.DataFrame,
    pd.DataFrame,
]:
    return evaluate_frames(
        league,
        load_ledger(
            league
        ),
        load_results(
            league
        ),
    )


def _print_metrics(
    metrics: EvaluationMetrics,
) -> None:
    print()
    print(
        "=" * 88
    )
    print(
        metrics.view
    )
    print(
        "=" * 88
    )

    print(
        "prediction rows:",
        metrics.prediction_rows,
    )

    print(
        "fixtures:",
        metrics.fixtures,
    )

    print(
        "correct:",
        metrics.correct,
    )

    print(
        "accuracy:",
        metrics.accuracy,
    )

    print(
        "log loss:",
        metrics.log_loss,
    )

    print(
        "multiclass brier:",
        metrics.brier,
    )

    print(
        "mean actual-result probability:",
        metrics.mean_actual_probability,
    )


def main() -> None:
    import argparse

    parser = (
        argparse
        .ArgumentParser()
    )

    parser.add_argument(
        "--league",
        default="EPL",
    )

    args = (
        parser
        .parse_args()
    )

    (
        report,
        settled,
        latest,
    ) = evaluate_league(
        args.league
    )

    print(
        "=" * 88
    )
    print(
        f"{report.league} CANONICAL PREDICTION EVALUATION"
    )
    print(
        "=" * 88
    )

    print(
        "ledger rows:",
        report.ledger_rows,
    )

    print(
        "finished result rows:",
        report.result_rows,
    )

    print(
        "settled rows:",
        report.settled_rows,
    )

    print(
        "settled fixtures:",
        report.settled_fixtures,
    )

    print(
        "MARKET_ONLY rows:",
        report.market_only_rows,
    )

    print(
        "Structural applied rows:",
        report.structural_rows,
    )

    _print_metrics(
        report.all_snapshots
    )

    _print_metrics(
        report.latest_pre_kickoff
    )

    if not latest.empty:
        print()
        print(
            "=" * 88
        )
        print(
            "LATEST SETTLED FIXTURES"
        )
        print(
            "=" * 88
        )

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

        print(
            latest[
                columns
            ]
            .sort_values(
                "kickoff_utc"
            )
            .to_string(
                index=False
            )
        )

    print()
    print(
        "PASS: READ-ONLY CANONICAL EVALUATION COMPLETE"
    )


if __name__ == "__main__":
    main()
