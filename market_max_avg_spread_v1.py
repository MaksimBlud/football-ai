"""MARKET_MAX_AVG_SPREAD_V1.

Research-only test of Football-Data Max-vs-Avg price spread as a pre-match
market-breadth signal for closing repricing and market uncertainty.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from market_devig_bookmaker_timing_v1 import download_history
from market_devig_methods_v1 import multiplicative_probabilities


EXPERIMENT_ID = "MARKET_MAX_AVG_SPREAD_V1"
OUTPUT_DIR = Path("artifacts/market_max_avg_spread_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

SEASONS = [
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
    "2025/2026",
]
DISCOVERY_SEASONS = SEASONS[:5]
VALIDATION_SEASON = "2024/2025"
TEST_SEASON = "2025/2026"

AVG_STANDARD = ("AvgH", "AvgD", "AvgA")
MAX_STANDARD = ("MaxH", "MaxD", "MaxA")
AVG_CLOSING = ("AvgCH", "AvgCD", "AvgCA")

MIN_SEASON_COVERAGE = 0.90
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
EPS = 1e-12


def numeric_odds(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.DataFrame:
    if not all(column in frame.columns for column in columns):
        return pd.DataFrame(
            np.nan,
            index=frame.index,
            columns=list(columns),
        )
    return frame[list(columns)].apply(pd.to_numeric, errors="coerce")


def basic_valid_mask(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.Series:
    odds = numeric_odds(frame, columns)
    return odds.gt(1.0).all(axis=1)


def spread_valid_mask(frame: pd.DataFrame) -> pd.Series:
    avg = numeric_odds(frame, AVG_STANDARD)
    maximum = numeric_odds(frame, MAX_STANDARD)
    valid = avg.gt(1.0).all(axis=1) & maximum.gt(1.0).all(axis=1)
    coherent = maximum.to_numpy(dtype=float) >= avg.to_numpy(dtype=float)
    coherent_rows = pd.Series(
        np.all(coherent, axis=1),
        index=frame.index,
        dtype=bool,
    )
    return valid & coherent_rows


def availability(frame: pd.DataFrame) -> dict:
    standard = basic_valid_mask(frame, AVG_STANDARD)
    maximum = basic_valid_mask(frame, MAX_STANDARD)
    closing = basic_valid_mask(frame, AVG_CLOSING)
    spread = spread_valid_mask(frame)
    combined = standard & maximum & closing & spread

    by_season = {}
    eligible = True
    for season in SEASONS:
        season_mask = frame["season"].eq(season)
        total = int(season_mask.sum())
        valid = int((season_mask & combined).sum())
        coverage = valid / total if total else 0.0
        by_season[season] = {
            "rows": total,
            "valid_rows": valid,
            "coverage": coverage,
        }
        if coverage < MIN_SEASON_COVERAGE:
            eligible = False

    return {
        "avg_standard_columns_present": all(c in frame.columns for c in AVG_STANDARD),
        "max_standard_columns_present": all(c in frame.columns for c in MAX_STANDARD),
        "avg_closing_columns_present": all(c in frame.columns for c in AVG_CLOSING),
        "minimum_required_coverage": MIN_SEASON_COVERAGE,
        "by_season": by_season,
        "valid_rows_total": int(combined.sum()),
        "eligible": bool(eligible),
    }


def probabilities_for_columns(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> np.ndarray:
    odds = numeric_odds(frame, columns).to_numpy(dtype=float)
    probabilities = np.empty((len(frame), 3), dtype=float)
    for index, row in enumerate(odds):
        probabilities[index], _ = multiplicative_probabilities(row)
    return probabilities


def actual_indices(frame: pd.DataFrame) -> np.ndarray:
    return frame["FTR"].astype(str).map(
        {"H": 0, "D": 1, "A": 2}
    ).to_numpy(dtype=int)


def brier_losses(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
) -> np.ndarray:
    y = actual_indices(frame)
    onehot = np.eye(3)[y]
    return np.sum((probabilities - onehot) ** 2, axis=1)


def build_dataset(frame: pd.DataFrame) -> pd.DataFrame:
    mask = (
        basic_valid_mask(frame, AVG_STANDARD)
        & basic_valid_mask(frame, MAX_STANDARD)
        & basic_valid_mask(frame, AVG_CLOSING)
        & spread_valid_mask(frame)
    )
    data = frame.loc[mask].copy().reset_index(drop=True)

    avg = numeric_odds(data, AVG_STANDARD).to_numpy(dtype=float)
    maximum = numeric_odds(data, MAX_STANDARD).to_numpy(dtype=float)
    gaps = maximum / avg - 1.0
    if (gaps < -1e-12).any():
        raise RuntimeError("Max-vs-Avg spread contains negative gap")

    data["market_spread"] = np.sqrt(np.mean(gaps**2, axis=1))
    data["gap_home"] = gaps[:, 0]
    data["gap_draw"] = gaps[:, 1]
    data["gap_away"] = gaps[:, 2]

    open_p = probabilities_for_columns(data, AVG_STANDARD)
    close_p = probabilities_for_columns(data, AVG_CLOSING)

    data["closing_tv"] = 0.5 * np.abs(close_p - open_p).sum(axis=1)
    data["avg_standard_brier"] = brier_losses(data, open_p)
    return data


def freeze_thresholds(data: pd.DataFrame) -> dict:
    discovery = data[data["season"].isin(DISCOVERY_SEASONS)]
    if discovery.empty:
        raise RuntimeError("Discovery spread sample is empty")
    low = float(discovery["market_spread"].quantile(0.25))
    high = float(discovery["market_spread"].quantile(0.75))
    if not (0.0 <= low < high):
        raise RuntimeError(
            f"Invalid discovery thresholds: low={low}, high={high}"
        )
    return {
        "low_q25": low,
        "high_q75": high,
        "discovery_rows": int(len(discovery)),
    }


def assign_groups(data: pd.DataFrame, thresholds: dict) -> pd.DataFrame:
    out = data.copy()
    labels = pd.Series(pd.NA, index=out.index, dtype="string")
    labels.loc[
        out["market_spread"].le(thresholds["low_q25"])
    ] = "LOW"
    labels.loc[
        out["market_spread"].ge(thresholds["high_q75"])
    ] = "HIGH"
    out["spread_group"] = labels
    return out


def season_effects(tails: pd.DataFrame, value_column: str) -> dict:
    rows = {}
    positive = 0
    for season in SEASONS:
        local = tails[tails["season"].eq(season)]
        high = local.loc[
            local["spread_group"].eq("HIGH"),
            value_column,
        ]
        low = local.loc[
            local["spread_group"].eq("LOW"),
            value_column,
        ]
        if len(high) == 0 or len(low) == 0:
            raise RuntimeError(
                f"{season}: frozen threshold produced empty tail"
            )
        delta = float(high.mean() - low.mean())
        positive += int(delta > 0.0)
        rows[season] = {
            "high_matches": int(len(high)),
            "low_matches": int(len(low)),
            "high_mean": float(high.mean()),
            "low_mean": float(low.mean()),
            "high_minus_low": delta,
        }
    return {
        "by_season": rows,
        "positive_seasons_all": positive,
        "positive_discovery_seasons": int(
            sum(
                rows[season]["high_minus_low"] > 0.0
                for season in DISCOVERY_SEASONS
            )
        ),
    }


def stratified_bootstrap_high_minus_low(
    tails: pd.DataFrame,
    value_column: str,
) -> dict:
    groups = {}
    for season in SEASONS:
        local = tails[tails["season"].eq(season)]
        high = local.loc[
            local["spread_group"].eq("HIGH"),
            value_column,
        ].to_numpy(dtype=float)
        low = local.loc[
            local["spread_group"].eq("LOW"),
            value_column,
        ].to_numpy(dtype=float)
        if len(high) == 0 or len(low) == 0:
            raise RuntimeError(
                f"{season}: missing bootstrap tail"
            )
        groups[season] = (high, low)

    total_high = sum(len(pair[0]) for pair in groups.values())
    total_low = sum(len(pair[1]) for pair in groups.values())

    observed_high = np.concatenate(
        [pair[0] for pair in groups.values()]
    )
    observed_low = np.concatenate(
        [pair[1] for pair in groups.values()]
    )
    observed = float(
        observed_high.mean() - observed_low.mean()
    )

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.empty(BOOTSTRAP_SAMPLES, dtype=float)
    for draw in range(BOOTSTRAP_SAMPLES):
        high_sum = 0.0
        low_sum = 0.0
        for high, low in groups.values():
            high_sum += float(
                rng.choice(
                    high,
                    size=len(high),
                    replace=True,
                ).sum()
            )
            low_sum += float(
                rng.choice(
                    low,
                    size=len(low),
                    replace=True,
                ).sum()
            )
        draws[draw] = (
            high_sum / total_high
            - low_sum / total_low
        )

    return {
        "mean_high_minus_low": observed,
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "bootstrap_probability_positive": float(
            (draws > 0.0).mean()
        ),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def signal_decision(
    effects: dict,
    bootstrap: dict,
) -> bool:
    by = effects["by_season"]
    discovery_rows = pd.concat(
        []
    ) if False else None
    discovery_positive = (
        effects["positive_discovery_seasons"] >= 3
    )
    validation_positive = (
        by[VALIDATION_SEASON]["high_minus_low"] > 0.0
    )
    test_positive = (
        by[TEST_SEASON]["high_minus_low"] > 0.0
    )

    discovery_high_sum = 0.0
    discovery_low_sum = 0.0
    discovery_high_n = 0
    discovery_low_n = 0
    for season in DISCOVERY_SEASONS:
        row = by[season]
        discovery_high_sum += row["high_mean"] * row["high_matches"]
        discovery_low_sum += row["low_mean"] * row["low_matches"]
        discovery_high_n += row["high_matches"]
        discovery_low_n += row["low_matches"]
    discovery_delta = (
        discovery_high_sum / discovery_high_n
        - discovery_low_sum / discovery_low_n
    )

    return bool(
        discovery_delta > 0.0
        and discovery_positive
        and validation_positive
        and test_positive
        and bootstrap["ci95_low"] > 0.0
    )


def evaluate(frame: pd.DataFrame) -> dict:
    info = availability(frame)
    if not info["eligible"]:
        return {
            "availability": info,
            "usable_rows": 0,
            "thresholds": None,
            "repricing": None,
            "error": None,
            "signals_supported": [],
            "interpretation": "SPREAD_SOURCE_UNAVAILABLE",
        }

    data = build_dataset(frame)
    thresholds = freeze_thresholds(data)
    grouped = assign_groups(data, thresholds)
    tails = grouped[
        grouped["spread_group"].isin(["HIGH", "LOW"])
    ].copy()

    repricing_effects = season_effects(
        tails,
        "closing_tv",
    )
    repricing_bootstrap = (
        stratified_bootstrap_high_minus_low(
            tails,
            "closing_tv",
        )
    )
    repricing_supported = signal_decision(
        repricing_effects,
        repricing_bootstrap,
    )

    error_effects = season_effects(
        tails,
        "avg_standard_brier",
    )
    error_bootstrap = (
        stratified_bootstrap_high_minus_low(
            tails,
            "avg_standard_brier",
        )
    )
    error_supported = signal_decision(
        error_effects,
        error_bootstrap,
    )

    signals = []
    if repricing_supported:
        signals.append("MAX_AVG_REPRICING_SIGNAL")
    if error_supported:
        signals.append("MAX_AVG_ERROR_SIGNAL")

    return {
        "availability": info,
        "usable_rows": int(len(data)),
        "thresholds": thresholds,
        "tail_rows": int(len(tails)),
        "spread_summary": {
            "mean": float(data["market_spread"].mean()),
            "median": float(data["market_spread"].median()),
            "min": float(data["market_spread"].min()),
            "max": float(data["market_spread"].max()),
        },
        "repricing": {
            "effects": repricing_effects,
            "bootstrap": repricing_bootstrap,
            "supported": repricing_supported,
        },
        "error": {
            "effects": error_effects,
            "bootstrap": error_bootstrap,
            "supported": error_supported,
        },
        "signals_supported": signals,
        "interpretation": (
            "MAX_AVG_SPREAD_SIGNAL_FOUND"
            if signals
            else "NO_MAX_AVG_SPREAD_SIGNAL"
        ),
    }


def main() -> int:
    frame = download_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_SPREAD_HOLDOUT",
        "research_only": True,
        "production_promotion": False,
        "paid_odds_api_calls": False,
        "supabase_reads": False,
        "supabase_writes": False,
        "candidate_artifact_saved": False,
        "source": "Football-Data EPL CSV",
        "source_rows": int(len(frame)),
        "seasons": SEASONS,
        "discovery_seasons": DISCOVERY_SEASONS,
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "avg_standard_columns": list(AVG_STANDARD),
        "max_standard_columns": list(MAX_STANDARD),
        "avg_closing_columns": list(AVG_CLOSING),
        "minimum_season_coverage": MIN_SEASON_COVERAGE,
        "result": result,
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Research only; zero paid API calls; production unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
