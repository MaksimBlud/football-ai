"""Deterministic audit for CORNER_TOTAL_SIGNAL_V1. Research only."""
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
        "season",
        "matches",
        "signal_mae",
        "baseline_mae",
        "delta_mae",
        "auc_9_5",
        "hit_rate_9_5",
    }
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing reference columns: {sorted(missing)}")
    seasons = tuple(frame["season"].astype(str))
    if seasons != EXPECTED_SEASONS:
        raise ValueError(f"unexpected held-out seasons: {seasons}")
    if any(s.startswith("2026/") or s > "2025/2026" for s in seasons):
        raise ValueError("current/future season outcomes are forbidden")
    if (frame["matches"] <= 0).any():
        raise ValueError("all held-out seasons must contain matches")


def summarize(frame: pd.DataFrame) -> dict[str, float | int | str]:
    validate_reference(frame)
    weights = frame["matches"].astype(float)
    weighted_delta = float((frame["delta_mae"] * weights).sum() / weights.sum())
    mae_wins = int((frame["delta_mae"] < 0).sum())
    weighted_auc = float((frame["auc_9_5"] * weights).sum() / weights.sum())
    auc_above_half = int((frame["auc_9_5"] > 0.5).sum())
    status = (
        "PORTABLE_TOTAL_SIGNAL"
        if weighted_delta < 0 and mae_wins >= MIN_SEASON_WINS
        else "NOT_PORTABLE_TOTAL_SIGNAL"
    )
    return {
        "research_block": "CORNER_TOTAL_SIGNAL_V1",
        "status": status,
        "matches": int(weights.sum()),
        "seasons": len(frame),
        "weighted_delta_mae": weighted_delta,
        "mae_season_wins": mae_wins,
        "weighted_auc_9_5": weighted_auc,
        "auc_seasons_above_0_5": auc_above_half,
    }


def write_report(reference: Path, output_dir: Path) -> Path:
    frame = pd.read_csv(reference)
    summary = pd.DataFrame([summarize(frame)])
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "corner_total_signal_v1_summary.csv"
    summary.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/corner_total_signal_v1"))
    args = parser.parse_args()
    out = write_report(args.reference, args.output_dir)
    print(pd.read_csv(out).to_string(index=False))


if __name__ == "__main__":
    main()
