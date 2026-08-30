"""Advanced read-only OOS diagnostics for canonical league predictions.

No readiness threshold, training, promotion, writes, or Structural activation.
The canonical latest-pre-kickoff view from evaluate_league_predictions remains
the source of truth; this module only adds descriptive segmentation and
bootstrap uncertainty estimates.
"""

from __future__ import annotations

from dataclasses import asdict

import numpy as np
import pandas as pd

from evaluate_league_predictions import calculate_metrics, evaluate_league


PROB_COLS = ["market_home_prob", "market_draw_prob", "market_away_prob"]


def confidence_bucket(value: float) -> str:
    if value < 0.45:
        return "LT_045"
    if value < 0.60:
        return "045_060"
    if value < 0.75:
        return "060_075"
    return "GE_075"


def bootstrap_metrics(
    frame: pd.DataFrame,
    *,
    samples: int = 1000,
    seed: int = 20260830,
) -> dict[str, dict[str, float] | None]:
    if frame.empty:
        return {"accuracy": None, "log_loss": None, "brier": None}
    if samples <= 0:
        raise ValueError("samples must be positive")

    rng = np.random.default_rng(seed)
    values = {"accuracy": [], "log_loss": [], "brier": []}
    n = len(frame)
    for _ in range(samples):
        idx = rng.integers(0, n, size=n)
        sample = frame.iloc[idx].reset_index(drop=True)
        metrics = calculate_metrics(sample, view="BOOTSTRAP")
        values["accuracy"].append(metrics.accuracy)
        values["log_loss"].append(metrics.log_loss)
        values["brier"].append(metrics.brier)

    result: dict[str, dict[str, float]] = {}
    for key, data in values.items():
        arr = np.asarray(data, dtype=float)
        result[key] = {
            "low": float(np.quantile(arr, 0.025)),
            "median": float(np.quantile(arr, 0.5)),
            "high": float(np.quantile(arr, 0.975)),
        }
    return result


def segment_latest(frame: pd.DataFrame) -> dict[str, list[dict]]:
    if frame.empty:
        return {"market_pick": [], "confidence": [], "actual_result": []}

    work = frame.copy()
    work["market_confidence"] = work[PROB_COLS].max(axis=1)
    work["confidence_bucket"] = work["market_confidence"].map(confidence_bucket)

    output: dict[str, list[dict]] = {}
    for dimension, column in (
        ("market_pick", "market_pick"),
        ("confidence", "confidence_bucket"),
        ("actual_result", "actual_result"),
    ):
        rows = []
        for value, group in work.groupby(column, dropna=False):
            metrics = calculate_metrics(group, view=f"{dimension}:{value}")
            rows.append({"segment": str(value), **asdict(metrics)})
        output[dimension] = rows
    return output


def build_advanced_report(
    league: str,
    *,
    bootstrap_samples: int = 1000,
    seed: int = 20260830,
) -> dict:
    report, _settled, latest = evaluate_league(league)
    latest_metrics = calculate_metrics(latest, view="LATEST_PRE_KICKOFF_PER_FIXTURE")
    return {
        "league": league,
        "settled_fixtures": report.settled_fixtures,
        "latest_pre_kickoff": asdict(latest_metrics),
        "segments": segment_latest(latest),
        "bootstrap_95": bootstrap_metrics(
            latest,
            samples=bootstrap_samples,
            seed=seed,
        ),
        "decision_gate": None,
        "readiness_threshold": None,
        "research_only": True,
    }


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser()
    parser.add_argument("--league", required=True)
    parser.add_argument("--bootstrap-samples", type=int, default=1000)
    args = parser.parse_args()
    payload = build_advanced_report(
        args.league,
        bootstrap_samples=args.bootstrap_samples,
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    print("PASS: READ-ONLY ADVANCED OOS EVALUATION COMPLETE")


if __name__ == "__main__":
    main()
