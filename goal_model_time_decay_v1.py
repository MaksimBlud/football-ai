"""GOAL_MODEL_TIME_DECAY_V1 — research-only nested walk-forward test.

Question:
Does exponential recency weighting improve the current football-only XGBoost
home/away goal architecture, without changing features, model hyperparameters,
Poisson market conversion, or production artifacts?

Safety:
- reads live Supabase matches only;
- excludes the incomplete/open 2026/2027 season;
- performs no Supabase writes;
- creates no .pkl artifact;
- performs no production promotion;
- half-life selection for each outer fold uses only earlier seasons.
"""
from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.metrics import (
    log_loss,
    mean_absolute_error,
    mean_squared_error,
)
from xgboost import XGBRegressor

from add_elo_features import add_elo_features
from feature_engineering import build_features
from poisson_utils import calculate_markets


EXPERIMENT_ID = "GOAL_MODEL_TIME_DECAY_V1"
OUTPUT_DIR = Path("artifacts/goal_model_time_decay_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

EXPERIMENT_SEASONS = [
    "2016/2017",
    "2017/2018",
    "2018/2019",
    "2019/2020",
    "2020/2021",
    "2021/2022",
    "2022/2023",
    "2023/2024",
    "2024/2025",
    "2025/2026",
]
EXCLUDED_SEASONS = ["2026/2027"]

# Current train_goal_models_no_odds.py architecture, frozen for V1.
FEATURES = [
    "home_last5_points",
    "away_last5_points",
    "form_difference",
    "home_goals_scored_last5",
    "home_goals_conceded_last5",
    "away_goals_scored_last5",
    "away_goals_conceded_last5",
    "home_shots_last5",
    "away_shots_last5",
    "home_shots_target_last5",
    "away_shots_target_last5",
    "home_elo",
    "away_elo",
    "elo_difference",
    "home_venue_win_rate",
    "away_venue_win_rate",
    "home_venue_goals_scored",
    "away_venue_goals_scored",
]

MODEL_PARAMS = {
    "n_estimators": 300,
    "max_depth": 3,
    "learning_rate": 0.02,
    "min_child_weight": 1,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "objective": "reg:squarederror",
    "eval_metric": "rmse",
    "random_state": 42,
    "n_jobs": 2,
}

# NONE is the exact current-training baseline. A decay candidate is selected
# only when historical inner OOS evidence beats NONE on BOTH primary metrics.
HALF_LIFE_CANDIDATES_DAYS = [None, 180, 365, 730, 1460]
OUTER_START_INDEX = 4  # first outer test = 2020/2021
INNER_START_INDEX = 3  # first inner validation = 2019/2020
BOOTSTRAP_SAMPLES = 5000
BOOTSTRAP_SEED = 20260928


def candidate_label(half_life_days: int | None) -> str:
    return "NONE" if half_life_days is None else str(int(half_life_days))


def load_historical_matches() -> pd.DataFrame:
    """Read the frozen experiment seasons from live Supabase, without writes."""
    # Keep DB client construction off the import path so contract/unit tests can
    # run on pull_request events where repository secrets are intentionally absent.
    from database import supabase

    rows: list[dict] = []
    page_size = 1000
    start = 0

    while True:
        response = (
            supabase
            .table("matches")
            .select("*")
            .in_("season", EXPERIMENT_SEASONS)
            .order("match_date")
            .order("id")
            .range(start, start + page_size - 1)
            .execute()
        )
        batch = response.data or []
        if not batch:
            break
        rows.extend(batch)
        if len(batch) < page_size:
            break
        start += page_size

    if not rows:
        raise RuntimeError("No historical matches returned from Supabase.")

    frame = pd.DataFrame(rows)
    observed = sorted(frame["season"].dropna().astype(str).unique())
    if observed != EXPERIMENT_SEASONS:
        raise RuntimeError(
            f"Season contract mismatch: observed={observed}, "
            f"expected={EXPERIMENT_SEASONS}"
        )

    counts = frame.groupby("season").size().to_dict()
    expected_counts = {season: 380 for season in EXPERIMENT_SEASONS}
    if counts != expected_counts:
        raise RuntimeError(
            f"Historical row-count contract changed: {counts}"
        )

    if frame["season"].isin(EXCLUDED_SEASONS).any():
        raise RuntimeError("Excluded/open season entered the experiment.")

    required_outcomes = ["home_goals", "away_goals", "result"]
    if frame[required_outcomes].isna().any().any():
        raise RuntimeError("Historical outcome rows are incomplete.")

    return frame


def prepare_features(matches: pd.DataFrame) -> pd.DataFrame:
    """Use the same pre-match feature builders as the current goal pipeline."""
    features = build_features(matches.copy())
    features = add_elo_features(features)

    features["match_date"] = pd.to_datetime(
        features["match_date"],
        errors="coerce",
    )

    required = FEATURES + [
        "season",
        "match_date",
        "home_goals",
        "away_goals",
    ]
    features = features.dropna(subset=required).copy()
    features = features.sort_values(
        ["match_date", "match_time", "home_team", "away_team"],
        kind="stable",
    ).reset_index(drop=True)

    if features.empty:
        raise RuntimeError("Feature frame is empty.")

    return features


def temporal_weights(
    match_dates: pd.Series,
    cutoff_date: pd.Timestamp,
    half_life_days: int | None,
) -> np.ndarray:
    """Return mean-one exponential weights, preserving the requested half-life ratio."""
    if half_life_days is None:
        return np.ones(len(match_dates), dtype=float)

    if half_life_days <= 0:
        raise ValueError("half_life_days must be positive or None")

    dates = pd.to_datetime(match_dates, errors="raise")
    cutoff = pd.Timestamp(cutoff_date)
    ages = (cutoff - dates).dt.total_seconds().to_numpy(dtype=float) / 86400.0
    if (ages < -1e-9).any():
        raise ValueError("Training row occurs after the evaluation cutoff.")

    raw = np.power(0.5, np.maximum(ages, 0.0) / float(half_life_days))
    total = float(raw.sum())
    if not np.isfinite(total) or total <= 0:
        raise ValueError("Invalid temporal weights.")

    # Isolate relative recency weighting from a global change in effective
    # sample size / regularization scale.
    return raw * (len(raw) / total)


def fit_goal_models(
    train: pd.DataFrame,
    cutoff_date: pd.Timestamp,
    half_life_days: int | None,
) -> tuple[XGBRegressor, XGBRegressor, dict]:
    weights = temporal_weights(
        train["match_date"],
        cutoff_date,
        half_life_days,
    )

    x_train = train[FEATURES]
    y_home = train["home_goals"].to_numpy(dtype=float)
    y_away = train["away_goals"].to_numpy(dtype=float)

    home_model = XGBRegressor(**MODEL_PARAMS)
    away_model = XGBRegressor(**MODEL_PARAMS)

    home_model.fit(x_train, y_home, sample_weight=weights)
    away_model.fit(x_train, y_away, sample_weight=weights)

    meta = {
        "half_life_days": half_life_days,
        "weight_min": float(weights.min()),
        "weight_max": float(weights.max()),
        "weight_mean": float(weights.mean()),
        "weight_sum": float(weights.sum()),
    }
    return home_model, away_model, meta


def poisson_log_probability(actual: np.ndarray, expected: np.ndarray) -> np.ndarray:
    expected = np.clip(expected.astype(float), 1e-9, None)
    actual = actual.astype(int)
    log_factorial = np.array(
        [math.lgamma(int(value) + 1) for value in actual],
        dtype=float,
    )
    return -expected + actual * np.log(expected) - log_factorial


def binary_log_losses(actual: np.ndarray, probability: np.ndarray) -> np.ndarray:
    probability = np.clip(probability.astype(float), 1e-12, 1.0 - 1e-12)
    actual = actual.astype(float)
    return -(
        actual * np.log(probability)
        + (1.0 - actual) * np.log(1.0 - probability)
    )


def evaluate_models(
    home_model: XGBRegressor,
    away_model: XGBRegressor,
    test: pd.DataFrame,
) -> tuple[dict, pd.DataFrame]:
    x_test = test[FEATURES]
    expected_home = np.clip(home_model.predict(x_test), 0.0, None)
    expected_away = np.clip(away_model.predict(x_test), 0.0, None)

    actual_home = test["home_goals"].to_numpy(dtype=int)
    actual_away = test["away_goals"].to_numpy(dtype=int)

    p_home: list[float] = []
    p_draw: list[float] = []
    p_away: list[float] = []
    p_over: list[float] = []
    p_btts: list[float] = []

    for home_xg, away_xg in zip(expected_home, expected_away):
        markets = calculate_markets(
            expected_home_goals=float(home_xg),
            expected_away_goals=float(away_xg),
        )
        p_home.append(float(markets["home_win_probability"]))
        p_draw.append(float(markets["draw_probability"]))
        p_away.append(float(markets["away_win_probability"]))
        p_over.append(float(markets["over_2_5_probability"]))
        p_btts.append(float(markets["btts_yes_probability"]))

    p_1x2 = np.column_stack([p_home, p_draw, p_away])
    p_1x2 = p_1x2 / p_1x2.sum(axis=1, keepdims=True)

    actual_1x2 = np.where(
        actual_home > actual_away,
        0,
        np.where(actual_home == actual_away, 1, 2),
    )
    one_hot = np.eye(3)[actual_1x2]

    actual_over = ((actual_home + actual_away) >= 3).astype(int)
    actual_btts = ((actual_home > 0) & (actual_away > 0)).astype(int)

    p_over_arr = np.asarray(p_over, dtype=float)
    p_btts_arr = np.asarray(p_btts, dtype=float)

    score_nll_per_match = -(
        poisson_log_probability(actual_home, expected_home)
        + poisson_log_probability(actual_away, expected_away)
    )
    logloss_1x2_per_match = -np.log(
        np.clip(p_1x2[np.arange(len(actual_1x2)), actual_1x2], 1e-12, 1.0)
    )
    brier_1x2_per_match = np.sum((p_1x2 - one_hot) ** 2, axis=1)
    over_logloss_per_match = binary_log_losses(actual_over, p_over_arr)
    over_brier_per_match = (p_over_arr - actual_over) ** 2
    btts_logloss_per_match = binary_log_losses(actual_btts, p_btts_arr)
    btts_brier_per_match = (p_btts_arr - actual_btts) ** 2

    metrics = {
        "matches": int(len(test)),
        "home_mae": float(mean_absolute_error(actual_home, expected_home)),
        "away_mae": float(mean_absolute_error(actual_away, expected_away)),
        "home_rmse": float(mean_squared_error(actual_home, expected_home) ** 0.5),
        "away_rmse": float(mean_squared_error(actual_away, expected_away) ** 0.5),
        "score_nll": float(score_nll_per_match.mean()),
        "logloss_1x2": float(log_loss(actual_1x2, p_1x2, labels=[0, 1, 2])),
        "brier_1x2": float(brier_1x2_per_match.mean()),
        "over_2_5_logloss": float(over_logloss_per_match.mean()),
        "over_2_5_brier": float(over_brier_per_match.mean()),
        "btts_logloss": float(btts_logloss_per_match.mean()),
        "btts_brier": float(btts_brier_per_match.mean()),
    }

    losses = pd.DataFrame(
        {
            "score_nll": score_nll_per_match,
            "logloss_1x2": logloss_1x2_per_match,
            "brier_1x2": brier_1x2_per_match,
            "over_2_5_logloss": over_logloss_per_match,
            "over_2_5_brier": over_brier_per_match,
            "btts_logloss": btts_logloss_per_match,
            "btts_brier": btts_brier_per_match,
        },
        index=test.index,
    )
    return metrics, losses


def weighted_metric_average(rows: list[dict], key: str) -> float:
    weights = np.asarray([row["matches"] for row in rows], dtype=float)
    values = np.asarray([row[key] for row in rows], dtype=float)
    return float(np.average(values, weights=weights))


def select_half_life(candidate_summaries: dict[str, dict]) -> int | None:
    """Fail closed to NONE unless a decay beats baseline on both primary metrics."""
    baseline = candidate_summaries["NONE"]
    eligible: list[tuple[float, float, int]] = []

    for half_life in (180, 365, 730, 1460):
        row = candidate_summaries[str(half_life)]
        if (
            row["score_nll"] < baseline["score_nll"]
            and row["logloss_1x2"] < baseline["logloss_1x2"]
        ):
            eligible.append(
                (
                    float(row["score_nll"]),
                    float(row["logloss_1x2"]),
                    half_life,
                )
            )

    if not eligible:
        return None

    eligible.sort()
    return int(eligible[0][2])


def fit_and_evaluate(
    train: pd.DataFrame,
    test: pd.DataFrame,
    half_life_days: int | None,
) -> tuple[dict, pd.DataFrame, dict]:
    cutoff = pd.Timestamp(test["match_date"].min())
    home_model, away_model, weight_meta = fit_goal_models(
        train,
        cutoff,
        half_life_days,
    )
    metrics, losses = evaluate_models(home_model, away_model, test)
    return metrics, losses, weight_meta


def bootstrap_delta(delta: np.ndarray) -> dict:
    delta = np.asarray(delta, dtype=float)
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(delta)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)

    for index in range(BOOTSTRAP_SAMPLES):
        sample = rng.integers(0, n, size=n)
        means[index] = float(delta[sample].mean())

    return {
        "mean_delta_candidate_minus_baseline": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_candidate_better": float((means < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def run_nested_walk_forward(features: pd.DataFrame) -> dict:
    seasons = EXPERIMENT_SEASONS
    inner_cache: dict[tuple[int, str], dict] = {}
    outer_rows: list[dict] = []
    pooled_baseline_losses: list[pd.DataFrame] = []
    pooled_candidate_losses: list[pd.DataFrame] = []

    for outer_index in range(OUTER_START_INDEX, len(seasons)):
        test_season = seasons[outer_index]

        candidate_inner_rows: dict[str, list[dict]] = {
            candidate_label(value): []
            for value in HALF_LIFE_CANDIDATES_DAYS
        }

        for inner_index in range(INNER_START_INDEX, outer_index):
            inner_test_season = seasons[inner_index]
            inner_train_seasons = seasons[:inner_index]
            inner_train = features[
                features["season"].isin(inner_train_seasons)
            ].copy()
            inner_test = features[
                features["season"] == inner_test_season
            ].copy()

            for half_life in HALF_LIFE_CANDIDATES_DAYS:
                label = candidate_label(half_life)
                cache_key = (inner_index, label)

                if cache_key not in inner_cache:
                    metrics, _, _ = fit_and_evaluate(
                        inner_train,
                        inner_test,
                        half_life,
                    )
                    inner_cache[cache_key] = metrics

                candidate_inner_rows[label].append(inner_cache[cache_key])

        summaries: dict[str, dict] = {}
        for label, rows in candidate_inner_rows.items():
            summaries[label] = {
                "folds": len(rows),
                "matches": int(sum(row["matches"] for row in rows)),
                "score_nll": weighted_metric_average(rows, "score_nll"),
                "logloss_1x2": weighted_metric_average(rows, "logloss_1x2"),
                "brier_1x2": weighted_metric_average(rows, "brier_1x2"),
                "over_2_5_logloss": weighted_metric_average(
                    rows,
                    "over_2_5_logloss",
                ),
                "btts_logloss": weighted_metric_average(rows, "btts_logloss"),
            }

        selected_half_life = select_half_life(summaries)

        outer_train = features[
            features["season"].isin(seasons[:outer_index])
        ].copy()
        outer_test = features[
            features["season"] == test_season
        ].copy()

        baseline_metrics, baseline_losses, baseline_weights = fit_and_evaluate(
            outer_train,
            outer_test,
            None,
        )

        if selected_half_life is None:
            candidate_metrics = dict(baseline_metrics)
            candidate_losses = baseline_losses.copy()
            candidate_weights = dict(baseline_weights)
        else:
            candidate_metrics, candidate_losses, candidate_weights = fit_and_evaluate(
                outer_train,
                outer_test,
                selected_half_life,
            )

        delta = {
            key: float(candidate_metrics[key] - baseline_metrics[key])
            for key in (
                "home_mae",
                "away_mae",
                "home_rmse",
                "away_rmse",
                "score_nll",
                "logloss_1x2",
                "brier_1x2",
                "over_2_5_logloss",
                "over_2_5_brier",
                "btts_logloss",
                "btts_brier",
            )
        }

        outer_rows.append(
            {
                "test_season": test_season,
                "train_seasons": seasons[:outer_index],
                "inner_validation_seasons": seasons[
                    INNER_START_INDEX:outer_index
                ],
                "selected_half_life_days": selected_half_life,
                "inner_candidate_summary": summaries,
                "baseline": baseline_metrics,
                "candidate": candidate_metrics,
                "delta_candidate_minus_baseline": delta,
                "baseline_weight_meta": baseline_weights,
                "candidate_weight_meta": candidate_weights,
            }
        )

        tagged_baseline = baseline_losses.copy()
        tagged_baseline["test_season"] = test_season
        tagged_candidate = candidate_losses.copy()
        tagged_candidate["test_season"] = test_season
        pooled_baseline_losses.append(tagged_baseline)
        pooled_candidate_losses.append(tagged_candidate)

        print(
            test_season,
            "selected=",
            candidate_label(selected_half_life),
            "score_nll_delta=",
            f"{delta['score_nll']:+.6f}",
            "1x2_ll_delta=",
            f"{delta['logloss_1x2']:+.6f}",
            "brier_delta=",
            f"{delta['brier_1x2']:+.6f}",
        )

    baseline_loss = pd.concat(pooled_baseline_losses, ignore_index=True)
    candidate_loss = pd.concat(pooled_candidate_losses, ignore_index=True)

    metric_keys = [
        "score_nll",
        "logloss_1x2",
        "brier_1x2",
        "over_2_5_logloss",
        "over_2_5_brier",
        "btts_logloss",
        "btts_brier",
    ]

    pooled = {}
    bootstrap = {}
    for key in metric_keys:
        baseline_value = float(baseline_loss[key].mean())
        candidate_value = float(candidate_loss[key].mean())
        pooled[key] = {
            "baseline": baseline_value,
            "candidate": candidate_value,
            "delta_candidate_minus_baseline": candidate_value - baseline_value,
        }
        bootstrap[key] = bootstrap_delta(
            candidate_loss[key].to_numpy(dtype=float)
            - baseline_loss[key].to_numpy(dtype=float)
        )

    selection_counts = Counter(
        candidate_label(row["selected_half_life_days"])
        for row in outer_rows
    )

    positive_folds = {
        key: int(
            sum(
                row["delta_candidate_minus_baseline"][key] < 0.0
                for row in outer_rows
            )
        )
        for key in metric_keys
    }

    signal_supported = bool(
        pooled["score_nll"]["delta_candidate_minus_baseline"] < 0.0
        and pooled["logloss_1x2"]["delta_candidate_minus_baseline"] < 0.0
        and pooled["brier_1x2"]["delta_candidate_minus_baseline"] < 0.0
    )

    return {
        "outer_fold_count": len(outer_rows),
        "outer_test_seasons": [
            row["test_season"]
            for row in outer_rows
        ],
        "selection_counts": dict(sorted(selection_counts.items())),
        "positive_folds": positive_folds,
        "pooled": pooled,
        "paired_bootstrap": bootstrap,
        "folds": outer_rows,
        "signal_supported": signal_supported,
        "interpretation": (
            "HISTORICAL_NESTED_OOS_SUPPORT"
            if signal_supported
            else "NO_ROBUST_DECAY_SUPPORT"
        ),
    }


def main() -> int:
    matches = load_historical_matches()
    features = prepare_features(matches)
    result = run_nested_walk_forward(features)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "production_promotion": False,
        "candidate_artifact_saved": False,
        "supabase_writes": False,
        "betting_enabled": False,
        "source": "live Supabase public.matches",
        "source_rows": int(len(matches)),
        "feature_rows": int(len(features)),
        "experiment_seasons": EXPERIMENT_SEASONS,
        "excluded_seasons": EXCLUDED_SEASONS,
        "feature_contract": FEATURES,
        "model_params": MODEL_PARAMS,
        "half_life_candidates_days": HALF_LIFE_CANDIDATES_DAYS,
        "weight_formula": "0.5 ** (age_days / half_life_days), normalized to mean 1",
        "selection_contract": (
            "nested expanding-season OOS; fail closed to NONE unless a decay "
            "beats NONE on both inner score_nll and inner 1x2 LogLoss"
        ),
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
            "xgboost": xgboost.__version__,
        },
        "result": result,
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print()
    print("=" * 90)
    print(EXPERIMENT_ID)
    print("=" * 90)
    print("source_rows:", report["source_rows"])
    print("feature_rows:", report["feature_rows"])
    print("outer_folds:", result["outer_fold_count"])
    print("selection_counts:", result["selection_counts"])
    print("signal_supported:", result["signal_supported"])
    print("interpretation:", result["interpretation"])
    print("report:", OUTPUT_PATH)
    print("Research only; no production artifact was changed or created.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
