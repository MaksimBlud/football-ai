"""Deterministic audit for CORNER_PRESSURE_SIGNAL_V3. Research only."""
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
PRIMARY_SIGNAL = "SHOTS"
SECONDARY_SIGNAL = "SHOTS_ON_TARGET"
MIN_PRIMARY_AUC = 0.52
MIN_POSITIVE_SEASONS = 5


def validate_reference(frame: pd.DataFrame) -> None:
    required = {"signal", "season", "matches", "n_pos", "n_neg", "auc_9_5", "pearson_corr"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"missing reference columns: {sorted(missing)}")
    if set(frame["signal"]) != {PRIMARY_SIGNAL, SECONDARY_SIGNAL}:
        raise ValueError("unexpected pressure signals")
    for signal in (PRIMARY_SIGNAL, SECONDARY_SIGNAL):
        seasons = tuple(frame.loc[frame.signal == signal, "season"].astype(str))
        if seasons != EXPECTED_SEASONS:
            raise ValueError(f"unexpected held-out seasons for {signal}: {seasons}")
    if (frame["matches"] <= 0).any() or (frame["n_pos"] <= 0).any() or (frame["n_neg"] <= 0).any():
        raise ValueError("invalid held-out coverage")


def _signal_summary(frame: pd.DataFrame, signal: str) -> dict[str, float | int]:
    g = frame[frame.signal == signal]
    weights = g["matches"].astype(float)
    return {
        "matches": int(weights.sum()),
        "weighted_auc_9_5": float((g["auc_9_5"] * weights).sum() / weights.sum()),
        "seasons_above_0_5": int((g["auc_9_5"] > 0.5).sum()),
        "weighted_pearson_corr": float((g["pearson_corr"] * weights).sum() / weights.sum()),
    }


def summarize(frame: pd.DataFrame) -> dict[str, float | int | str]:
    validate_reference(frame)
    primary = _signal_summary(frame, PRIMARY_SIGNAL)
    secondary = _signal_summary(frame, SECONDARY_SIGNAL)
    status = (
        "PORTABLE_PRESSURE_DISCRIMINATOR"
        if primary["weighted_auc_9_5"] > MIN_PRIMARY_AUC
        and primary["seasons_above_0_5"] >= MIN_POSITIVE_SEASONS
        else "NOT_PORTABLE_PRESSURE_DISCRIMINATOR"
    )
    return {
        "research_block": "CORNER_PRESSURE_SIGNAL_V3",
        "status": status,
        "matches": primary["matches"],
        "primary_weighted_auc_9_5": primary["weighted_auc_9_5"],
        "primary_seasons_above_0_5": primary["seasons_above_0_5"],
        "primary_weighted_pearson_corr": primary["weighted_pearson_corr"],
        "secondary_weighted_auc_9_5": secondary["weighted_auc_9_5"],
        "secondary_seasons_above_0_5": secondary["seasons_above_0_5"],
    }


def write_report(reference: Path, output_dir: Path) -> Path:
    frame = pd.read_csv(reference)
    report = pd.DataFrame([summarize(frame)])
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / "corner_pressure_signal_v3_summary.csv"
    report.to_csv(path, index=False)
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/corner_pressure_signal_v3"))
    args = parser.parse_args()
    out = write_report(args.reference, args.output_dir)
    print(pd.read_csv(out).to_string(index=False))


if __name__ == "__main__":
    main()
