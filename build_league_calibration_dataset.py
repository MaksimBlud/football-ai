"""Research-only canonical calibration dataset builder.

Reuses the canonical prediction evaluator for settlement.  The primary
calibration unit is the latest pre-kickoff prediction per fixture; the
all-snapshots view is retained for diagnostics only.

No training, promotion, Structural V2 activation, model mutation, or
Supabase writes are performed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

import evaluate_league_predictions as evaluator


ALL_SNAPSHOTS = "ALL_SNAPSHOTS"
LATEST_PRE_KICKOFF = "LATEST_PRE_KICKOFF_PER_FIXTURE"
OUTCOMES = ("H", "D", "A")

DERIVED_COLUMNS = [
    "evaluation_view",
    "hours_to_kickoff",
    "actual_home",
    "actual_draw",
    "actual_away",
]


@dataclass(frozen=True)
class CalibrationDatasetReport:
    league: str
    settled_rows: int
    settled_fixtures: int
    all_snapshot_rows: int
    latest_rows: int
    latest_fixtures: int
    structural_applied_rows: int


def _empty_like(frame: pd.DataFrame) -> pd.DataFrame:
    columns = list(frame.columns)
    for column in DERIVED_COLUMNS:
        if column not in columns:
            columns.append(column)
    return pd.DataFrame(columns=columns)


def _prepare_frame(
    frame: pd.DataFrame,
    *,
    league: str,
    view: str,
) -> pd.DataFrame:
    if frame.empty:
        return _empty_like(frame)

    work = frame.copy()
    required = {
        "league",
        "event_id",
        "kickoff_utc",
        "snapshot_time_utc",
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
        "actual_result",
    }
    missing = required - set(work.columns)
    if missing:
        raise ValueError(
            "Settled frame missing columns: "
            + ", ".join(sorted(missing))
        )

    if not (work["league"].astype(str) == str(league)).all():
        raise ValueError("Settled frame contains wrong league")

    work["kickoff_utc"] = pd.to_datetime(
        work["kickoff_utc"], utc=True, errors="coerce"
    )
    work["snapshot_time_utc"] = pd.to_datetime(
        work["snapshot_time_utc"], utc=True, errors="coerce"
    )
    if work[["kickoff_utc", "snapshot_time_utc"]].isna().any().any():
        raise ValueError("Calibration frame contains invalid timestamps")
    if not (work["snapshot_time_utc"] < work["kickoff_utc"]).all():
        raise ValueError("Calibration frame contains non-pre-kickoff prediction")

    hours = (
        (work["kickoff_utc"] - work["snapshot_time_utc"])
        .dt.total_seconds()
        .div(3600.0)
    )
    if not np.isfinite(hours.to_numpy(dtype=float)).all() or (hours <= 0).any():
        raise ValueError("Invalid pre-kickoff horizon")
    work["hours_to_kickoff"] = hours.astype(float)

    prob_columns = [
        "market_home_prob",
        "market_draw_prob",
        "market_away_prob",
    ]
    probs = work[prob_columns].apply(pd.to_numeric, errors="coerce")
    matrix = probs.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError("Calibration frame contains non-finite probabilities")
    if (matrix < 0).any() or (matrix > 1).any():
        raise ValueError("Calibration probability outside [0,1]")
    if not np.allclose(matrix.sum(axis=1), 1.0, atol=1e-9):
        raise ValueError("Calibration probabilities do not sum to one")
    work[prob_columns] = probs

    work["actual_result"] = work["actual_result"].astype(str).str.upper()
    if not work["actual_result"].isin(OUTCOMES).all():
        raise ValueError("Invalid actual result")
    work["actual_home"] = (work["actual_result"] == "H").astype(int)
    work["actual_draw"] = (work["actual_result"] == "D").astype(int)
    work["actual_away"] = (work["actual_result"] == "A").astype(int)
    work["evaluation_view"] = view

    if "structural_applied" not in work.columns:
        work["structural_applied"] = False
    work["structural_applied"] = (
        work["structural_applied"].fillna(False).astype(bool)
    )

    return work.sort_values(
        ["kickoff_utc", "event_id", "snapshot_time_utc"],
        kind="stable",
    ).reset_index(drop=True)


def build_calibration_frames(
    league: str,
    ledger: pd.DataFrame,
    results: pd.DataFrame,
) -> tuple[CalibrationDatasetReport, pd.DataFrame, pd.DataFrame]:
    evaluation_report, settled, latest = evaluator.evaluate_frames(
        league, ledger, results
    )
    all_snapshots = _prepare_frame(
        settled, league=league, view=ALL_SNAPSHOTS
    )
    latest_frame = _prepare_frame(
        latest, league=league, view=LATEST_PRE_KICKOFF
    )

    if not latest_frame.empty:
        if latest_frame["event_id"].duplicated().any():
            raise ValueError("Latest calibration view contains duplicate event_id")
        expected = all_snapshots.groupby("event_id")["snapshot_time_utc"].max()
        actual = latest_frame.set_index("event_id")["snapshot_time_utc"]
        if not actual.sort_index().equals(expected.sort_index()):
            raise ValueError(
                "Latest calibration view is not latest pre-kickoff snapshot"
            )

    report = CalibrationDatasetReport(
        league=league,
        settled_rows=len(settled),
        settled_fixtures=(settled["event_id"].nunique() if not settled.empty else 0),
        all_snapshot_rows=len(all_snapshots),
        latest_rows=len(latest_frame),
        latest_fixtures=(
            latest_frame["event_id"].nunique() if not latest_frame.empty else 0
        ),
        structural_applied_rows=(
            int(all_snapshots["structural_applied"].sum())
            if not all_snapshots.empty
            else 0
        ),
    )
    if report.settled_rows != evaluation_report.settled_rows:
        raise ValueError("Calibration/evaluation settled-row mismatch")
    if report.settled_fixtures != evaluation_report.settled_fixtures:
        raise ValueError("Calibration/evaluation fixture mismatch")
    return report, all_snapshots, latest_frame


def build_league_calibration_dataset(
    league: str,
) -> tuple[CalibrationDatasetReport, pd.DataFrame, pd.DataFrame]:
    return build_calibration_frames(
        league,
        evaluator.load_ledger(league),
        evaluator.load_results(league),
    )


def export_frames(
    *,
    all_snapshots: pd.DataFrame,
    latest: pd.DataFrame,
    output_dir: Path,
    league: str,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    slug = league.strip().lower().replace(" ", "_")
    all_path = output_dir / f"{slug}_calibration_all_snapshots.csv"
    latest_path = output_dir / f"{slug}_calibration_latest_pre_kickoff.csv"
    all_snapshots.to_csv(all_path, index=False)
    latest.to_csv(latest_path, index=False)
    return all_path, latest_path


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--league", default="EPL")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    report, all_snapshots, latest = build_league_calibration_dataset(args.league)
    print("=" * 88)
    print(f"{report.league} CANONICAL CALIBRATION DATASET")
    print("=" * 88)
    print("settled rows:", report.settled_rows)
    print("settled fixtures:", report.settled_fixtures)
    print("all-snapshot rows:", report.all_snapshot_rows)
    print("latest rows:", report.latest_rows)
    print("latest fixtures:", report.latest_fixtures)
    print("Structural applied rows:", report.structural_applied_rows)

    if args.output_dir is None:
        print("CSV export: skipped (read-only mode)")
        return
    all_path, latest_path = export_frames(
        all_snapshots=all_snapshots,
        latest=latest,
        output_dir=args.output_dir,
        league=args.league,
    )
    print("all snapshots CSV:", all_path)
    print("latest pre-kickoff CSV:", latest_path)


if __name__ == "__main__":
    main()
