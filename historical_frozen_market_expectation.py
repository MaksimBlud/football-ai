"""Compare frozen-rule OOS wins with the no-vig market expectation.

Research only. Frozen rule identity and first test season come from the already-created
frozen summary. Test rows are never used to re-select or tune the rule. The diagnostic
reports expected wins from each row's no-vig market confidence, observed-minus-expected
wins, a calibration gap, and an exact Poisson-binomial upper-tail probability under the
conditional independent Bernoulli benchmark implied by those probabilities.
"""
from __future__ import annotations

import argparse
import math
from pathlib import Path

import numpy as np
import pandas as pd

BOUNDS = {
    "<40%": (0.0, 0.40),
    "40–50%": (0.40, 0.50),
    "50–60%": (0.50, 0.60),
    "60–70%": (0.60, 0.70),
    "≥70%": (0.70, 1.0000001),
}


def poisson_binomial_upper_tail(probabilities: np.ndarray, observed_wins: int) -> float:
    """Exact P(X >= observed_wins) for independent Bernoulli probabilities."""
    probabilities = np.asarray(probabilities, dtype=float)
    if probabilities.ndim != 1:
        raise ValueError("probabilities must be one-dimensional")
    if len(probabilities) == 0:
        return float("nan")
    if observed_wins < 0 or observed_wins > len(probabilities):
        raise ValueError("observed_wins outside valid range")
    if np.any(~np.isfinite(probabilities)) or np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError("probabilities must be finite values in [0, 1]")

    pmf = np.zeros(len(probabilities) + 1, dtype=float)
    pmf[0] = 1.0
    for index, probability in enumerate(probabilities, start=1):
        previous = pmf.copy()
        pmf[: index + 1] = 0.0
        pmf[:index] += previous[:index] * (1.0 - probability)
        pmf[1 : index + 1] += previous[:index] * probability
    return float(pmf[observed_wins:].sum())


def _selected_test_rows(prepared: pd.DataFrame, rule: pd.Series) -> pd.DataFrame:
    bucket = str(rule["confidence_bucket"])
    if bucket not in BOUNDS:
        raise ValueError(f"Unsupported confidence bucket: {bucket}")
    required = {"league", "season", "market_pick", "market_confidence", "won"}
    missing = required - set(prepared.columns)
    if missing:
        raise ValueError("Missing prepared columns: " + ", ".join(sorted(missing)))

    low, high = BOUNDS[bucket]
    confidence = pd.to_numeric(prepared["market_confidence"], errors="coerce")
    selected = prepared[
        (prepared["league"].astype(str) == str(rule["league"]))
        & (prepared["season"].astype(str) >= str(rule["first_test_season"]))
        & (prepared["market_pick"].astype(str) == str(rule["market_pick"]))
        & confidence.ge(low)
        & confidence.lt(high)
    ].copy()
    selected["market_confidence"] = pd.to_numeric(selected["market_confidence"], errors="coerce")
    selected = selected.dropna(subset=["market_confidence"])
    selected = selected[selected["market_confidence"].between(0.0, 1.0, inclusive="both")]
    selected["won"] = selected["won"].astype(bool)
    return selected


def _metrics(selected: pd.DataFrame) -> dict[str, float | int | bool | None]:
    n = len(selected)
    if not n:
        return {
            "matches": 0,
            "wins": 0,
            "observed_accuracy": None,
            "mean_market_probability": None,
            "expected_wins": None,
            "excess_wins": None,
            "calibration_gap": None,
            "expected_variance": None,
            "standardized_excess_wins": None,
            "poisson_binomial_upper_tail": None,
        }
    probabilities = selected["market_confidence"].to_numpy(dtype=float)
    wins = int(selected["won"].sum())
    expected_wins = float(probabilities.sum())
    variance = float(np.sum(probabilities * (1.0 - probabilities)))
    excess = wins - expected_wins
    return {
        "matches": n,
        "wins": wins,
        "observed_accuracy": wins / n,
        "mean_market_probability": expected_wins / n,
        "expected_wins": expected_wins,
        "excess_wins": excess,
        "calibration_gap": wins / n - expected_wins / n,
        "expected_variance": variance,
        "standardized_excess_wins": excess / math.sqrt(variance) if variance > 0 else None,
        "poisson_binomial_upper_tail": poisson_binomial_upper_tail(probabilities, wins),
    }


def evaluate_frozen_market_expectation(
    prepared: pd.DataFrame,
    frozen_summary: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    summary_rows = []
    season_rows = []
    for _, rule in frozen_summary.iterrows():
        selected = _selected_test_rows(prepared, rule)
        identity = {
            "league": str(rule["league"]),
            "market_pick": str(rule["market_pick"]),
            "confidence_bucket": str(rule["confidence_bucket"]),
            "first_test_season": str(rule["first_test_season"]),
        }
        summary_rows.append({**identity, **_metrics(selected)})
        for season, group in selected.groupby(selected["season"].astype(str), sort=True):
            season_rows.append({**identity, "season": season, **_metrics(group)})
    return pd.DataFrame(summary_rows), pd.DataFrame(season_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Frozen-rule market expectation diagnostic")
    parser.add_argument("prepared_matches", type=Path)
    parser.add_argument("frozen_summary", type=Path)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/historical_strategy_market_expectation"),
    )
    args = parser.parse_args()

    summary, by_season = evaluate_frozen_market_expectation(
        pd.read_csv(args.prepared_matches),
        pd.read_csv(args.frozen_summary),
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(args.output_dir / "market_expectation_summary.csv", index=False)
    by_season.to_csv(args.output_dir / "market_expectation_by_season.csv", index=False)
    print("FROZEN RULE MARKET EXPECTATION — RESEARCH ONLY")
    print(summary.to_string(index=False))
    print("Upper-tail probability uses the exact Poisson-binomial benchmark conditional on market probabilities.")
    print("Match independence is a benchmark assumption, not a claim about football outcomes.")
    print("No rule selection, tuning, training, Supabase writes, live activation, or .pkl changes performed.")


if __name__ == "__main__":
    main()
