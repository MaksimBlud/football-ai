"""Deterministic audit for CORNER_TOTAL_CALIBRATED_V2. Research only."""
from __future__ import annotations

import argparse
from pathlib import Path
import pandas as pd

EXPECTED_SEASONS = (
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
    "2025/2026",
)
MIN_SEASON_WINS = 5


def validate_reference(frame: pd.DataFrame) -> None:
    required = {
        "season", "matches", "train_matches", "slope", "intercept",
        "calibrated_mae", "baseline_mae", "delta_mae", "auc_9_5", "hit_rate_9_5",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing reference columns: {sorted(missing)}")
    seasons = tuple(frame["season"].astype(str))
    if seasons != EXPECTED_SEASONS:
        raise ValueError(f"unexpected held-out seasons: {seasons}")
    if (frame["matches"] <= 0).any() or (frame["train_matches"] <= 0).any():
        raise ValueError("all seasons require positive train/test coverage")


def summarize(frame: pd.DataFrame) -> dict[str, float | int | str]:
    validate_reference(frame)
    weights = frame["matches"].astype(float)
    weighted_delta = float((frame["delta_mae"] * weights).sum() / weights.sum())
    wins = int((frame["delta_mae"] < 0).sum())
    weighted_auc = float((frame["auc_9_5"] * weights).sum() / weights.sum())
    weighted_hit = float((frame["hit_rate_9_5"] * weights).sum() / weights.sum())
    status = (
        "PORTABLE_CALIBRATED_TOTAL_SIGNAL"
        if weighted_delta < 0 and wins >= MIN_SEASON_WINS
        else "NOT_PORTABLE_CALIBRATED_TOTAL_SIGNAL"
    )
    return {
        "research_block": "CORNER_TOTAL_CALIBRATED_V2",
        "status": status,
        "matches": int(weights.sum()),
        "seasons": len(frame),
        "weighted_delta_mae": weighted_delta,
        "mae_season_wins": wins,
        "weighted_auc_9_5": weighted_auc,
        "weighted_hit_rate_9_5": weighted_hit,
        "min_slope": float(frame["slope"].min()),
        "max_slope": float(frame["slope"].max()),
    }


def write_report(reference: Path, output_dir: Path) -> Path:
    frame = pd.read_csv(reference)
    summary = pd.DataFrame([summarize(frame)])
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "corner_total_calibrated_v2_summary.csv"
    summary.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/corner_total_calibrated_v2"))
    args = parser.parse_args()
    out = write_report(args.reference, args.output_dir)
    print(pd.read_csv(out).to_string(index=False))


if __name__ == "__main__":
    main()
