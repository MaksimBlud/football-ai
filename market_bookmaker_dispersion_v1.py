"""MARKET_BOOKMAKER_DISPERSION_V1.

Research-only test of multi-bookmaker consensus and pre-match bookmaker
disagreement as probability/closing-repricing signals.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import scipy

from market_devig_bookmaker_timing_v1 import (
    download_history,
)
from market_devig_methods_v1 import (
    multiplicative_probabilities,
)


EXPERIMENT_ID = "MARKET_BOOKMAKER_DISPERSION_V1"
OUTPUT_DIR = Path("artifacts/market_bookmaker_dispersion_v1")
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

BENCHMARK_COLUMNS = {
    "AVG_STANDARD": ("AvgH", "AvgD", "AvgA"),
    "AVG_CLOSING": ("AvgCH", "AvgCD", "AvgCA"),
}

BOOKMAKER_COLUMNS = {
    "BET365": ("B365H", "B365D", "B365A"),
    "BETWAY": ("BWH", "BWD", "BWA"),
    "INTERWETTEN": ("IWH", "IWD", "IWA"),
    "PINNACLE": ("PSH", "PSD", "PSA"),
    "WILLIAM_HILL": ("WHH", "WHD", "WHA"),
    "VCBET": ("VCH", "VCD", "VCA"),
}

MIN_SEASON_COVERAGE = 0.90
MIN_ELIGIBLE_BOOKMAKERS = 2
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
EPS = 1e-12


def valid_mask(frame: pd.DataFrame, columns: tuple[str, str, str]) -> pd.Series:
    if not all(column in frame.columns for column in columns):
        return pd.Series(False, index=frame.index, dtype=bool)
    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    return odds.gt(1.0).all(axis=1)


def availability(frame: pd.DataFrame, columns: tuple[str, str, str]) -> dict:
    present = all(column in frame.columns for column in columns)
    mask = valid_mask(frame, columns)
    by_season = {}
    eligible = present

    for season in SEASONS:
        season_mask = frame["season"].eq(season)
        total = int(season_mask.sum())
        valid = int((season_mask & mask).sum())
        coverage = valid / total if total else 0.0
        by_season[season] = {
            "rows": total,
            "valid_rows": valid,
            "coverage": coverage,
        }
        if coverage < MIN_SEASON_COVERAGE:
            eligible = False

    return {
        "columns": list(columns),
        "columns_present": present,
        "minimum_required_coverage": MIN_SEASON_COVERAGE,
        "by_season": by_season,
        "eligible": bool(eligible),
        "valid_rows_total": int(mask.sum()),
    }


def probabilities_for_columns(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> np.ndarray:
    odds = (
        frame[list(columns)]
        .apply(pd.to_numeric, errors="raise")
        .to_numpy(dtype=float)
    )
    probabilities = np.empty((len(frame), 3), dtype=float)
    for index, row in enumerate(odds):
        probabilities[index], _ = multiplicative_probabilities(row)
    return probabilities


def actual_indices(frame: pd.DataFrame) -> np.ndarray:
    return frame["FTR"].astype(str).map(
        {"H": 0, "D": 1, "A": 2}
    ).to_numpy(dtype=int)


def per_match_losses(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
) -> pd.DataFrame:
    y = actual_indices(frame)
    onehot = np.eye(3)[y]
    actual_p = np.clip(
        probabilities[np.arange(len(frame)), y],
        EPS,
        1.0,
    )
    return pd.DataFrame(
        {
            "logloss": -np.log(actual_p),
            "brier": np.sum(
                (probabilities - onehot) ** 2,
                axis=1,
            ),
        },
        index=frame.index,
    )


def score(
    frame: pd.DataFrame,
    probabilities: np.ndarray,
) -> dict:
    losses = per_match_losses(frame, probabilities)
    y = actual_indices(frame)
    return {
        "matches": int(len(frame)),
        "logloss": float(losses["logloss"].mean()),
        "brier": float(losses["brier"].mean()),
        "accuracy": float(
            (probabilities.argmax(axis=1) == y).mean()
        ),
    }


def stratified_paired_bootstrap(
    seasons: np.ndarray,
    delta: np.ndarray,
) -> dict:
    seasons = np.asarray(seasons)
    delta = np.asarray(delta, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    unique = list(SEASONS)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)

    index_by_season = {
        season: np.flatnonzero(seasons == season)
        for season in unique
    }

    for draw in range(BOOTSTRAP_SAMPLES):
        sampled = []
        for season in unique:
            indices = index_by_season[season]
            if len(indices):
                sampled.append(
                    rng.choice(
                        indices,
                        size=len(indices),
                        replace=True,
                    )
                )
        all_indices = np.concatenate(sampled)
        means[draw] = float(delta[all_indices].mean())

    return {
        "mean_delta": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_better": float((means < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def stratified_group_difference_bootstrap(
    frame: pd.DataFrame,
    value_column: str,
) -> dict:
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    draws = np.empty(BOOTSTRAP_SAMPLES, dtype=float)

    groups = {}
    for season in SEASONS:
        season_frame = frame[frame["season"].eq(season)]
        high = season_frame.loc[
            season_frame["dispersion_group"].eq("HIGH"),
            value_column,
        ].to_numpy(dtype=float)
        low = season_frame.loc[
            season_frame["dispersion_group"].eq("LOW"),
            value_column,
        ].to_numpy(dtype=float)
        if len(high) == 0 or len(low) == 0:
            raise RuntimeError(
                f"{season}: empty dispersion tail group"
            )
        groups[season] = (high, low)

    total_high = sum(len(v[0]) for v in groups.values())
    total_low = sum(len(v[1]) for v in groups.values())

    high_all = np.concatenate([v[0] for v in groups.values()])
    low_all = np.concatenate([v[1] for v in groups.values()])
    observed = float(high_all.mean() - low_all.mean())

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


def build_common_dataset(
    frame: pd.DataFrame,
    eligible_bookmakers: list[str],
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    mask = pd.Series(True, index=frame.index, dtype=bool)

    for columns in BENCHMARK_COLUMNS.values():
        mask &= valid_mask(frame, columns)

    for bookmaker in eligible_bookmakers:
        mask &= valid_mask(
            frame,
            BOOKMAKER_COLUMNS[bookmaker],
        )

    common = frame.loc[mask].copy().reset_index(drop=True)
    if common.empty:
        raise RuntimeError("No common fixtures across eligible sources")

    probabilities = {
        "AVG_STANDARD": probabilities_for_columns(
            common,
            BENCHMARK_COLUMNS["AVG_STANDARD"],
        ),
        "AVG_CLOSING": probabilities_for_columns(
            common,
            BENCHMARK_COLUMNS["AVG_CLOSING"],
        ),
    }

    bookmaker_matrices = []
    for bookmaker in eligible_bookmakers:
        matrix = probabilities_for_columns(
            common,
            BOOKMAKER_COLUMNS[bookmaker],
        )
        probabilities[bookmaker] = matrix
        bookmaker_matrices.append(matrix)

    stacked = np.stack(bookmaker_matrices, axis=1)
    consensus = stacked.mean(axis=1)
    consensus = consensus / consensus.sum(axis=1, keepdims=True)
    probabilities["CONSENSUS"] = consensus

    outcome_std = stacked.std(axis=1, ddof=0)
    dispersion = np.sqrt(
        np.mean(outcome_std**2, axis=1)
    )

    common["bookmaker_dispersion"] = dispersion
    common["closing_tv"] = (
        0.5
        * np.abs(
            probabilities["AVG_CLOSING"]
            - probabilities["AVG_STANDARD"]
        ).sum(axis=1)
    )

    avg_losses = per_match_losses(
        common,
        probabilities["AVG_STANDARD"],
    )
    common["avg_standard_brier"] = avg_losses[
        "brier"
    ].to_numpy(dtype=float)
    common["avg_standard_logloss"] = avg_losses[
        "logloss"
    ].to_numpy(dtype=float)

    labels = pd.Series(
        pd.NA,
        index=common.index,
        dtype="string",
    )

    for season in SEASONS:
        season_mask = common["season"].eq(season)
        values = common.loc[
            season_mask,
            "bookmaker_dispersion",
        ]
        if len(values) < 4:
            raise RuntimeError(
                f"{season}: insufficient common fixtures"
            )
        low = float(values.quantile(0.25))
        high = float(values.quantile(0.75))
        labels.loc[
            season_mask
            & common["bookmaker_dispersion"].le(low)
        ] = "LOW"
        labels.loc[
            season_mask
            & common["bookmaker_dispersion"].ge(high)
        ] = "HIGH"

    common["dispersion_group"] = labels
    return common, probabilities


def consensus_evaluation(
    common: pd.DataFrame,
    probabilities: dict[str, np.ndarray],
) -> dict:
    baseline_p = probabilities["AVG_STANDARD"]
    consensus_p = probabilities["CONSENSUS"]
    baseline_losses = per_match_losses(
        common,
        baseline_p,
    ).reset_index(drop=True)
    consensus_losses = per_match_losses(
        common,
        consensus_p,
    ).reset_index(drop=True)

    baseline = score(common, baseline_p)
    consensus = score(common, consensus_p)

    by_season = {}
    joint_wins = 0

    for season in SEASONS:
        mask = common["season"].eq(season).to_numpy()
        local = common.loc[mask].reset_index(drop=True)
        b = score(local, baseline_p[mask])
        c = score(local, consensus_p[mask])
        joint = bool(
            c["logloss"] < b["logloss"]
            and c["brier"] < b["brier"]
        )
        joint_wins += int(joint)
        by_season[season] = {
            "baseline": b,
            "consensus": c,
            "delta": {
                "logloss": c["logloss"] - b["logloss"],
                "brier": c["brier"] - b["brier"],
            },
            "joint_win": joint,
        }

    bootstrap = {}
    seasons = common["season"].astype(str).to_numpy()
    for metric in ("logloss", "brier"):
        delta = (
            consensus_losses[metric].to_numpy(dtype=float)
            - baseline_losses[metric].to_numpy(dtype=float)
        )
        bootstrap[metric] = stratified_paired_bootstrap(
            seasons,
            delta,
        )

    supported = bool(
        consensus["logloss"] < baseline["logloss"]
        and consensus["brier"] < baseline["brier"]
        and joint_wins >= 4
        and bootstrap["logloss"]["ci95_high"] < 0.0
        and bootstrap["brier"]["ci95_high"] < 0.0
    )

    return {
        "baseline": baseline,
        "consensus": consensus,
        "delta": {
            "logloss": consensus["logloss"] - baseline["logloss"],
            "brier": consensus["brier"] - baseline["brier"],
        },
        "joint_season_wins": joint_wins,
        "by_season": by_season,
        "paired_bootstrap": bootstrap,
        "supported": supported,
    }


def dispersion_evaluation(common: pd.DataFrame) -> dict:
    tails = common[
        common["dispersion_group"].isin(["HIGH", "LOW"])
    ].copy()

    by_season = {}
    repricing_positive = 0
    error_positive = 0

    for season in SEASONS:
        local = tails[tails["season"].eq(season)]
        high = local[
            local["dispersion_group"].eq("HIGH")
        ]
        low = local[
            local["dispersion_group"].eq("LOW")
        ]
        repricing_delta = float(
            high["closing_tv"].mean()
            - low["closing_tv"].mean()
        )
        error_delta = float(
            high["avg_standard_brier"].mean()
            - low["avg_standard_brier"].mean()
        )
        repricing_positive += int(repricing_delta > 0.0)
        error_positive += int(error_delta > 0.0)
        by_season[season] = {
            "high_matches": int(len(high)),
            "low_matches": int(len(low)),
            "high_mean_dispersion": float(
                high["bookmaker_dispersion"].mean()
            ),
            "low_mean_dispersion": float(
                low["bookmaker_dispersion"].mean()
            ),
            "high_mean_closing_tv": float(
                high["closing_tv"].mean()
            ),
            "low_mean_closing_tv": float(
                low["closing_tv"].mean()
            ),
            "closing_tv_high_minus_low": repricing_delta,
            "high_mean_avg_standard_brier": float(
                high["avg_standard_brier"].mean()
            ),
            "low_mean_avg_standard_brier": float(
                low["avg_standard_brier"].mean()
            ),
            "brier_high_minus_low": error_delta,
        }

    repricing_bootstrap = (
        stratified_group_difference_bootstrap(
            tails,
            "closing_tv",
        )
    )
    error_bootstrap = (
        stratified_group_difference_bootstrap(
            tails,
            "avg_standard_brier",
        )
    )

    repricing_supported = bool(
        repricing_positive >= 5
        and repricing_bootstrap["mean_high_minus_low"] > 0.0
        and repricing_bootstrap["ci95_low"] > 0.0
    )
    error_supported = bool(
        error_positive >= 5
        and error_bootstrap["mean_high_minus_low"] > 0.0
        and error_bootstrap["ci95_low"] > 0.0
    )

    return {
        "tail_rows": int(len(tails)),
        "repricing_positive_seasons": repricing_positive,
        "error_positive_seasons": error_positive,
        "by_season": by_season,
        "repricing_bootstrap": repricing_bootstrap,
        "error_bootstrap": error_bootstrap,
        "repricing_supported": repricing_supported,
        "error_supported": error_supported,
    }


def evaluate(frame: pd.DataFrame) -> dict:
    bookmaker_availability = {
        bookmaker: availability(frame, columns)
        for bookmaker, columns in BOOKMAKER_COLUMNS.items()
    }
    benchmark_availability = {
        name: availability(frame, columns)
        for name, columns in BENCHMARK_COLUMNS.items()
    }

    eligible = [
        bookmaker
        for bookmaker, info in bookmaker_availability.items()
        if info["eligible"]
    ]

    if len(eligible) < MIN_ELIGIBLE_BOOKMAKERS:
        return {
            "bookmaker_availability": bookmaker_availability,
            "benchmark_availability": benchmark_availability,
            "eligible_bookmakers": eligible,
            "common_rows": 0,
            "consensus": None,
            "dispersion": None,
            "signals_supported": [],
            "interpretation": "INSUFFICIENT_SOURCE_DIVERSITY",
        }

    if not all(
        benchmark_availability[name]["eligible"]
        for name in BENCHMARK_COLUMNS
    ):
        raise RuntimeError(
            "AVG standard/closing benchmark coverage failed"
        )

    common, probabilities = build_common_dataset(
        frame,
        eligible,
    )

    common_counts = (
        common.groupby("season")
        .size()
        .reindex(SEASONS, fill_value=0)
        .astype(int)
        .to_dict()
    )

    consensus = consensus_evaluation(
        common,
        probabilities,
    )
    dispersion = dispersion_evaluation(common)

    signals = []
    if consensus["supported"]:
        signals.append("CONSENSUS_PROBABILITY_SUPPORT")
    if dispersion["repricing_supported"]:
        signals.append("DISPERSION_REPRICING_SUPPORT")
    if dispersion["error_supported"]:
        signals.append("DISPERSION_ERROR_SUPPORT")

    return {
        "bookmaker_availability": bookmaker_availability,
        "benchmark_availability": benchmark_availability,
        "eligible_bookmakers": eligible,
        "common_rows": int(len(common)),
        "common_rows_by_season": common_counts,
        "consensus": consensus,
        "dispersion": dispersion,
        "signals_supported": signals,
        "interpretation": (
            "BOOKMAKER_DISPERSION_SIGNAL_FOUND"
            if signals
            else "NO_BOOKMAKER_DISPERSION_SIGNAL"
        ),
    }


def main() -> int:
    frame = download_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_MULTI_BOOKMAKER",
        "research_only": True,
        "production_promotion": False,
        "paid_odds_api_calls": False,
        "supabase_writes": False,
        "candidate_artifact_saved": False,
        "source": "Football-Data EPL CSV",
        "source_rows": int(len(frame)),
        "seasons": SEASONS,
        "bookmaker_columns": {
            key: list(value)
            for key, value in BOOKMAKER_COLUMNS.items()
        },
        "benchmark_columns": {
            key: list(value)
            for key, value in BENCHMARK_COLUMNS.items()
        },
        "minimum_season_coverage": MIN_SEASON_COVERAGE,
        "minimum_eligible_bookmakers": MIN_ELIGIBLE_BOOKMAKERS,
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
