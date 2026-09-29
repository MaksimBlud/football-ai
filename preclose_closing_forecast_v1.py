"""1X2_PRECLOSE_CLOSING_FORECAST_V1.

Research-only temporal test of whether Football-Data's first-set Bet365 1X2 market
contains a predictable mapping to the explicit closing Bet365 market.

No paid APIs, no Supabase access, no production model artifacts.
"""
from __future__ import annotations

import io
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import sklearn
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from market_devig_methods_v1 import multiplicative_probabilities


EXPERIMENT_ID = "1X2_PRECLOSE_CLOSING_FORECAST_V1"
OUTPUT_DIR = Path("artifacts/1x2_preclose_closing_forecast_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

SEASON_CODES = {
    "2019/2020": "1920",
    "2020/2021": "2021",
    "2021/2022": "2122",
    "2022/2023": "2223",
    "2023/2024": "2324",
    "2024/2025": "2425",
    "2025/2026": "2526",
}
SEASONS = list(SEASON_CODES)
DEVELOPMENT_SEASONS = SEASONS[:4]
SELECTION_SEASON = "2023/2024"
HOLDOUT_1 = "2024/2025"
HOLDOUT_2 = "2025/2026"

B365_FIRST = ("B365H", "B365D", "B365A")
B365_CLOSE = ("B365CH", "B365CD", "B365CA")
AVG_FIRST = ("AvgH", "AvgD", "AvgA")
REQUIRED_ODDS = (*B365_FIRST, *B365_CLOSE, *AVG_FIRST)

FEATURE_VARIANTS = ("STATE", "STATE_PLUS_CONSENSUS")
ALPHA_GRID = (0.01, 0.1, 1.0, 10.0, 100.0)
EPS = 1e-9
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"

OUTCOME_MAP = {"H": 0, "D": 1, "A": 2}


def download_history() -> pd.DataFrame:
    parts = []
    for season, code in SEASON_CODES.items():
        response = requests.get(BASE_URL.format(code=code), timeout=60)
        response.raise_for_status()
        frame = pd.read_csv(io.BytesIO(response.content))
        if len(frame) != 380:
            raise RuntimeError(
                f"{season}: expected exactly 380 EPL rows, got {len(frame)}"
            )
        missing = {"FTR", *REQUIRED_ODDS} - set(frame.columns)
        if missing:
            raise RuntimeError(
                f"{season}: missing required columns {sorted(missing)}"
            )
        frame = frame.copy()
        frame["season"] = season
        frame["_season_row"] = np.arange(len(frame), dtype=int)
        parts.append(frame)

    data = pd.concat(parts, ignore_index=True)
    if len(data) != 2660:
        raise RuntimeError(f"Expected 2660 rows, got {len(data)}")
    if not data["FTR"].astype(str).isin(OUTCOME_MAP).all():
        raise RuntimeError("Invalid historical match outcome")

    for column in REQUIRED_ODDS:
        data[column] = pd.to_numeric(data[column], errors="coerce")
    valid = data[list(REQUIRED_ODDS)].gt(1.0).all(axis=1)
    if not valid.all():
        counts = data.loc[~valid].groupby("season").size().to_dict()
        raise RuntimeError(
            f"Frozen sample requires complete Bet365/Avg first+close odds: {counts}"
        )

    return data.reset_index(drop=True)


def fair_probabilities_from_columns(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> tuple[np.ndarray, np.ndarray]:
    odds = frame[list(columns)].to_numpy(dtype=float)
    probs = np.empty_like(odds, dtype=float)
    overround = np.empty(len(frame), dtype=float)
    for index, row in enumerate(odds):
        p, details = multiplicative_probabilities(row)
        probs[index] = p
        overround[index] = float(details["overround"])
    return probs, overround


def entropy(probabilities: np.ndarray) -> np.ndarray:
    p = np.clip(np.asarray(probabilities, dtype=float), EPS, 1.0)
    return -np.sum(p * np.log(p), axis=1)


def prepare_dataset(raw: pd.DataFrame) -> pd.DataFrame:
    b365_first, b365_overround = fair_probabilities_from_columns(
        raw,
        B365_FIRST,
    )
    b365_close, _ = fair_probabilities_from_columns(raw, B365_CLOSE)
    avg_first, avg_overround = fair_probabilities_from_columns(raw, AVG_FIRST)

    top_sorted = np.sort(b365_first, axis=1)
    frame = pd.DataFrame(
        {
            "season": raw["season"].astype(str).to_numpy(),
            "_season_row": raw["_season_row"].to_numpy(dtype=int),
            "result": raw["FTR"].astype(str).to_numpy(),
            "first_p_home": b365_first[:, 0],
            "first_p_draw": b365_first[:, 1],
            "first_p_away": b365_first[:, 2],
            "first_overround": b365_overround,
            "first_entropy": entropy(b365_first),
            "first_top_probability": top_sorted[:, 2],
            "first_second_probability": top_sorted[:, 1],
            "first_top_second_gap": top_sorted[:, 2] - top_sorted[:, 1],
            "first_home_away_gap": b365_first[:, 0] - b365_first[:, 2],
            "avg_p_home": avg_first[:, 0],
            "avg_p_draw": avg_first[:, 1],
            "avg_p_away": avg_first[:, 2],
            "avg_overround": avg_overround,
            "book_vs_avg_home": b365_first[:, 0] - avg_first[:, 0],
            "book_vs_avg_draw": b365_first[:, 1] - avg_first[:, 1],
            "book_vs_avg_away": b365_first[:, 2] - avg_first[:, 2],
            "book_vs_avg_overround":
                b365_overround - avg_overround,
            "close_p_home": b365_close[:, 0],
            "close_p_draw": b365_close[:, 1],
            "close_p_away": b365_close[:, 2],
        }
    )

    for side in ("home", "draw", "away"):
        frame[f"move_{side}"] = (
            frame[f"close_p_{side}"] - frame[f"first_p_{side}"]
        )

    return frame


STATE_FEATURES = [
    "first_p_home",
    "first_p_draw",
    "first_p_away",
    "first_overround",
    "first_entropy",
    "first_top_probability",
    "first_second_probability",
    "first_top_second_gap",
    "first_home_away_gap",
]

CONSENSUS_FEATURES = STATE_FEATURES + [
    "avg_p_home",
    "avg_p_draw",
    "avg_p_away",
    "avg_overround",
    "book_vs_avg_home",
    "book_vs_avg_draw",
    "book_vs_avg_away",
    "book_vs_avg_overround",
]

FEATURES = {
    "STATE": STATE_FEATURES,
    "STATE_PLUS_CONSENSUS": CONSENSUS_FEATURES,
}

TARGET_COLUMNS = ["move_home", "move_draw", "move_away"]
FIRST_COLUMNS = ["first_p_home", "first_p_draw", "first_p_away"]
CLOSE_COLUMNS = ["close_p_home", "close_p_draw", "close_p_away"]


@dataclass
class Candidate:
    name: str
    feature_variant: str | None
    alpha: float | None
    model: Pipeline | None
    mean_delta: np.ndarray | None


def fit_candidate(
    train: pd.DataFrame,
    *,
    name: str,
    feature_variant: str | None = None,
    alpha: float | None = None,
) -> Candidate:
    if name == "ZERO":
        return Candidate(name, None, None, None, np.zeros(3, dtype=float))

    if name == "MEAN_DELTA":
        return Candidate(
            name,
            None,
            None,
            None,
            train[TARGET_COLUMNS].to_numpy(dtype=float).mean(axis=0),
        )

    if name != "RIDGE":
        raise ValueError(f"Unsupported candidate {name}")
    if feature_variant not in FEATURES or alpha is None:
        raise ValueError("RIDGE requires a frozen feature variant and alpha")

    model = Pipeline(
        [
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=float(alpha))),
        ]
    )
    model.fit(
        train[FEATURES[feature_variant]],
        train[TARGET_COLUMNS].to_numpy(dtype=float),
    )
    return Candidate(
        name=f"RIDGE_{feature_variant}",
        feature_variant=feature_variant,
        alpha=float(alpha),
        model=model,
        mean_delta=None,
    )


def predicted_delta(candidate: Candidate, frame: pd.DataFrame) -> np.ndarray:
    if candidate.name == "ZERO":
        return np.zeros((len(frame), 3), dtype=float)
    if candidate.name == "MEAN_DELTA":
        return np.tile(candidate.mean_delta, (len(frame), 1))
    assert candidate.model is not None
    assert candidate.feature_variant is not None
    return np.asarray(
        candidate.model.predict(frame[FEATURES[candidate.feature_variant]]),
        dtype=float,
    )


def predicted_close(
    candidate: Candidate,
    frame: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    first = frame[FIRST_COLUMNS].to_numpy(dtype=float)
    delta = predicted_delta(candidate, frame)
    p = np.clip(first + delta, EPS, None)
    p = p / p.sum(axis=1, keepdims=True)
    return p, delta


def per_match_metrics(
    frame: pd.DataFrame,
    candidate: Candidate,
) -> tuple[pd.DataFrame, dict]:
    predicted, delta = predicted_close(candidate, frame)
    first = frame[FIRST_COLUMNS].to_numpy(dtype=float)
    close = frame[CLOSE_COLUMNS].to_numpy(dtype=float)
    actual_move = close - first

    y = frame["result"].map(OUTCOME_MAP).to_numpy(dtype=int)
    onehot = np.eye(3)[y]

    close_mae = np.abs(predicted - close).mean(axis=1)
    close_ce = -np.sum(
        close * np.log(np.clip(predicted, EPS, 1.0)),
        axis=1,
    )
    outcome_ll = -np.log(
        np.clip(predicted[np.arange(len(frame)), y], EPS, 1.0)
    )
    outcome_brier = np.sum((predicted - onehot) ** 2, axis=1)

    first_outcome_ll = -np.log(
        np.clip(first[np.arange(len(frame)), y], EPS, 1.0)
    )
    first_outcome_brier = np.sum((first - onehot) ** 2, axis=1)

    close_outcome_ll = -np.log(
        np.clip(close[np.arange(len(frame)), y], EPS, 1.0)
    )
    close_outcome_brier = np.sum((close - onehot) ** 2, axis=1)

    movement_direction = np.sign(actual_move)
    predicted_direction = np.sign(delta)
    direction_correct = (movement_direction == predicted_direction).astype(float)

    actual_max_move = np.max(np.abs(actual_move), axis=1)
    predicted_max_move = np.max(np.abs(delta), axis=1)

    rows = pd.DataFrame(
        {
            "close_mae": close_mae,
            "close_cross_entropy": close_ce,
            "outcome_logloss": outcome_ll,
            "outcome_brier": outcome_brier,
            "first_outcome_logloss": first_outcome_ll,
            "first_outcome_brier": first_outcome_brier,
            "actual_close_outcome_logloss": close_outcome_ll,
            "actual_close_outcome_brier": close_outcome_brier,
            "max_move_mae": np.abs(predicted_max_move - actual_max_move),
            "direction_accuracy":
                direction_correct.mean(axis=1),
        },
        index=frame.index,
    )

    report = {
        "matches": int(len(frame)),
        **{
            column: float(rows[column].mean())
            for column in rows.columns
        },
        "actual_mean_max_abs_move": float(actual_max_move.mean()),
        "actual_argmax_change_rate": float(
            (
                first.argmax(axis=1)
                != close.argmax(axis=1)
            ).mean()
        ),
        "mean_actual_move": {
            side: float(actual_move[:, index].mean())
            for index, side in enumerate(("home", "draw", "away"))
        },
        "mean_predicted_move": {
            side: float(delta[:, index].mean())
            for index, side in enumerate(("home", "draw", "away"))
        },
    }
    return rows.reset_index(drop=True), report


def candidate_specs() -> list[dict]:
    specs = [{"name": "ZERO"}, {"name": "MEAN_DELTA"}]
    for feature_variant in FEATURE_VARIANTS:
        for alpha in ALPHA_GRID:
            specs.append(
                {
                    "name": "RIDGE",
                    "feature_variant": feature_variant,
                    "alpha": alpha,
                }
            )
    return specs


def spec_id(spec: dict) -> str:
    if spec["name"] != "RIDGE":
        return spec["name"]
    return f"RIDGE_{spec['feature_variant']}_A{spec['alpha']:g}"


def fit_from_spec(train: pd.DataFrame, spec: dict) -> Candidate:
    return fit_candidate(
        train,
        name=spec["name"],
        feature_variant=spec.get("feature_variant"),
        alpha=spec.get("alpha"),
    )


def select_on_validation(
    train: pd.DataFrame,
    validation: pd.DataFrame,
) -> tuple[dict, list[dict]]:
    scored = []
    zero_metrics = None

    for spec in candidate_specs():
        candidate = fit_from_spec(train, spec)
        _, metrics = per_match_metrics(validation, candidate)
        row = {
            "candidate_id": spec_id(spec),
            "spec": spec,
            "close_mae": metrics["close_mae"],
            "close_cross_entropy": metrics["close_cross_entropy"],
            "outcome_logloss": metrics["outcome_logloss"],
            "outcome_brier": metrics["outcome_brier"],
        }
        scored.append(row)
        if spec["name"] == "ZERO":
            zero_metrics = row

    assert zero_metrics is not None
    eligible = [
        row
        for row in scored
        if row["candidate_id"] != "ZERO"
        and row["close_mae"] < zero_metrics["close_mae"]
        and row["close_cross_entropy"]
        < zero_metrics["close_cross_entropy"]
    ]

    if not eligible:
        selected = next(row for row in scored if row["candidate_id"] == "ZERO")
    else:
        selected = min(
            eligible,
            key=lambda row: (
                row["close_cross_entropy"],
                row["close_mae"],
                row["candidate_id"],
            ),
        )

    return selected, scored


def paired_bootstrap(
    candidate_rows: pd.DataFrame,
    baseline_rows: pd.DataFrame,
    metric: str,
) -> dict:
    delta = (
        candidate_rows[metric].to_numpy(dtype=float)
        - baseline_rows[metric].to_numpy(dtype=float)
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)
    n = len(delta)
    for index in range(BOOTSTRAP_SAMPLES):
        sample = rng.integers(0, n, size=n)
        means[index] = float(delta[sample].mean())

    return {
        "mean_delta_candidate_minus_zero": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_candidate_better": float((means < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def evaluate(data: pd.DataFrame) -> dict:
    development = data[data["season"].isin(DEVELOPMENT_SEASONS)].copy()
    selection = data[data["season"].eq(SELECTION_SEASON)].copy()

    selected, validation_grid = select_on_validation(
        development,
        selection,
    )
    selected_spec = selected["spec"]

    holdout_reports = {}
    pooled_candidate = []
    pooled_zero = []

    # Holdout 1: coefficients may use selection season after hyperparameters freeze.
    train_1 = data[
        data["season"].isin(DEVELOPMENT_SEASONS + [SELECTION_SEASON])
    ].copy()
    test_1 = data[data["season"].eq(HOLDOUT_1)].copy()

    # Holdout 2: same selected spec; coefficients expand through holdout 1.
    train_2 = data[
        data["season"].isin(
            DEVELOPMENT_SEASONS + [SELECTION_SEASON, HOLDOUT_1]
        )
    ].copy()
    test_2 = data[data["season"].eq(HOLDOUT_2)].copy()

    for season, train, test in (
        (HOLDOUT_1, train_1, test_1),
        (HOLDOUT_2, train_2, test_2),
    ):
        zero = fit_candidate(train, name="ZERO")
        candidate = fit_from_spec(train, selected_spec)

        zero_rows, zero_metrics = per_match_metrics(test, zero)
        candidate_rows, candidate_metrics = per_match_metrics(test, candidate)

        delta = {
            key: float(candidate_metrics[key] - zero_metrics[key])
            for key in (
                "close_mae",
                "close_cross_entropy",
                "outcome_logloss",
                "outcome_brier",
                "max_move_mae",
            )
        }

        holdout_reports[season] = {
            "train_seasons": sorted(train["season"].unique().tolist()),
            "zero": zero_metrics,
            "candidate": candidate_metrics,
            "delta_candidate_minus_zero": delta,
            "passed_primary_gate": bool(
                delta["close_mae"] < 0.0
                and delta["close_cross_entropy"] < 0.0
            ),
        }

        zero_rows = zero_rows.copy()
        candidate_rows = candidate_rows.copy()
        zero_rows["season"] = season
        candidate_rows["season"] = season
        pooled_zero.append(zero_rows)
        pooled_candidate.append(candidate_rows)

    pooled_zero_df = pd.concat(pooled_zero, ignore_index=True)
    pooled_candidate_df = pd.concat(pooled_candidate, ignore_index=True)

    bootstrap = {
        metric: paired_bootstrap(
            pooled_candidate_df,
            pooled_zero_df,
            metric,
        )
        for metric in ("close_mae", "close_cross_entropy")
    }

    selected_nonzero = selected["candidate_id"] != "ZERO"
    validation_zero = next(
        row for row in validation_grid if row["candidate_id"] == "ZERO"
    )
    validation_pass = bool(
        selected_nonzero
        and selected["close_mae"] < validation_zero["close_mae"]
        and selected["close_cross_entropy"]
        < validation_zero["close_cross_entropy"]
    )
    holdouts_pass = all(
        report["passed_primary_gate"]
        for report in holdout_reports.values()
    )
    robust = bool(
        validation_pass
        and holdouts_pass
        and bootstrap["close_mae"]["ci95_high"] < 0.0
        and bootstrap["close_cross_entropy"]["ci95_high"] < 0.0
    )

    return {
        "development_seasons": DEVELOPMENT_SEASONS,
        "selection_season": SELECTION_SEASON,
        "holdout_seasons": [HOLDOUT_1, HOLDOUT_2],
        "selected_candidate": selected,
        "validation_zero": validation_zero,
        "validation_grid": validation_grid,
        "validation_passed": validation_pass,
        "holdouts": holdout_reports,
        "paired_bootstrap_760_holdout_matches": bootstrap,
        "robust_support": robust,
        "interpretation": (
            "ROBUST_PRECLOSE_TO_CLOSE_SIGNAL"
            if robust
            else "NO_ROBUST_PRECLOSE_TO_CLOSE_SIGNAL"
        ),
    }


def main() -> int:
    raw = download_history()
    data = prepare_dataset(raw)
    result = evaluate(data)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_HOLDOUT",
        "research_only": True,
        "production_promotion": False,
        "supabase_reads": False,
        "supabase_writes": False,
        "paid_api_calls": False,
        "candidate_artifact_saved": False,
        "source": "Football-Data EPL CSV",
        "source_rows": int(len(raw)),
        "seasons": SEASONS,
        "first_set_columns": list(B365_FIRST),
        "closing_columns": list(B365_CLOSE),
        "consensus_first_set_columns": list(AVG_FIRST),
        "feature_variants": {
            key: value
            for key, value in FEATURES.items()
        },
        "alpha_grid": list(ALPHA_GRID),
        "result": result,
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "requests": requests.__version__,
            "scikit_learn": sklearn.__version__,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Research only; no production state changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
