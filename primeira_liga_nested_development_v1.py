"""Execute the frozen Primeira Liga nested historical development V1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from league_model_sweep import FEATURE_SETS, MODEL_VARIANTS, make_model, market_probabilities, metrics
from primeira_liga_nested_support import (
    ADMITTED_SEASONS,
    CONFIGURED_SEASONS,
    CURRENT_FORBIDDEN_SEASON,
    LEAGUE,
    build_history,
    build_trainable_features,
    production_state,
    simplex,
)

PROTOCOL = "primeira_liga_nested_development_v1"
DEVELOPMENT_OOS_SEASONS = (
    "2020-2021", "2021-2022", "2022-2023",
    "2023-2024", "2024-2025", "2025-2026",
)
OUTER_TEST_SEASONS = ("2022-2023", "2023-2024", "2024-2025", "2025-2026")
FEATURE_SET_ORDER = ("core", "core_elo", "full_no_odds")
MODEL_ORDER = ("logistic_l2", "xgb_shallow", "xgb_base", "xgb_regularized")
ALPHAS = tuple(round(float(value), 2) for value in np.arange(0.05, 0.51, 0.05))
REQUIRED_OUTER_WINS = 3
OUTPUT = Path("experiments/primeira_liga_nested_development_v1/latest.json")


def assert_frozen_family() -> None:
    if tuple(name for name in FEATURE_SET_ORDER if name in FEATURE_SETS) != FEATURE_SET_ORDER:
        raise RuntimeError("Frozen feature family changed")
    if tuple(name for name in MODEL_ORDER if name in MODEL_VARIANTS) != MODEL_ORDER:
        raise RuntimeError("Frozen model family changed")


def hybrid_probability(market: np.ndarray, ai: np.ndarray, alpha: float) -> np.ndarray:
    return simplex((1.0 - float(alpha)) * market + float(alpha) * ai)


def build_variant_oos(frame: pd.DataFrame, feature_set: str, model_name: str) -> pd.DataFrame:
    columns = FEATURE_SETS[feature_set]
    rows = []
    for season in DEVELOPMENT_OOS_SEASONS:
        train = frame[frame["season"].astype(str) < season].copy()
        test = frame[frame["season"].astype(str) == season].copy()
        required = columns + ["target", "home_odds", "draw_odds", "away_odds"]
        train, test = train.dropna(subset=required), test.dropna(subset=required)
        if train.empty or test.empty:
            raise ValueError(f"Empty train/test fold for {feature_set}/{model_name}/{season}")
        model = make_model(model_name)
        model.fit(train[columns], train["target"].astype(int))
        ai = simplex(model.predict_proba(test[columns]))
        market = simplex(market_probabilities(test))
        rows.append(pd.DataFrame({
            "season": season,
            "target": test["target"].astype(int).to_numpy(),
            "ai_home_probability": ai[:, 0],
            "ai_draw_probability": ai[:, 1],
            "ai_away_probability": ai[:, 2],
            "market_home_probability": market[:, 0],
            "market_draw_probability": market[:, 1],
            "market_away_probability": market[:, 2],
        }))
    return pd.concat(rows, ignore_index=True)


def arrays(predictions: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y = predictions["target"].astype(int).to_numpy()
    ai = simplex(predictions[[
        "ai_home_probability", "ai_draw_probability", "ai_away_probability"
    ]].to_numpy(float))
    market = simplex(predictions[[
        "market_home_probability", "market_draw_probability", "market_away_probability"
    ]].to_numpy(float))
    return y, ai, market


def score_ai(predictions: pd.DataFrame, seasons: tuple[str, ...]) -> dict:
    selected = predictions[predictions["season"].isin(seasons)]
    y, ai, _ = arrays(selected)
    return metrics(y, ai)


def select_candidate(
    predictions: dict[tuple[str, str], pd.DataFrame], seasons: tuple[str, ...]
):
    rows = []
    for feature_set in FEATURE_SET_ORDER:
        for model_name in MODEL_ORDER:
            score = score_ai(predictions[(feature_set, model_name)], seasons)
            rows.append((
                score["logloss"], score["brier"], -score["accuracy"],
                feature_set, model_name, score,
            ))
    rows.sort(key=lambda row: row[:5])
    winner = rows[0]
    return (winner[3], winner[4]), winner[5]


def select_alpha(predictions: pd.DataFrame, seasons: tuple[str, ...]):
    selected = predictions[predictions["season"].isin(seasons)]
    y, ai, market = arrays(selected)
    rows = []
    for alpha in ALPHAS:
        score = metrics(y, hybrid_probability(market, ai, alpha))
        rows.append((score["logloss"], score["brier"], -score["accuracy"], alpha, score))
    rows.sort(key=lambda row: row[:4])
    return float(rows[0][3]), rows[0][4]


def inner_seasons(outer_season: str) -> tuple[str, ...]:
    if outer_season not in OUTER_TEST_SEASONS:
        raise ValueError(f"Unsupported outer season {outer_season}")
    result = tuple(season for season in DEVELOPMENT_OOS_SEASONS if season < outer_season)
    if len(result) < 2:
        raise ValueError("Nested outer fold requires at least two earlier OOS seasons")
    return result


def score_outer(predictions: pd.DataFrame, season: str, alpha: float):
    selected = predictions[predictions["season"] == season]
    y, ai, market = arrays(selected)
    hybrid = hybrid_probability(market, ai, alpha)
    market_score, hybrid_score = metrics(y, market), metrics(y, hybrid)
    wins = {
        "accuracy": hybrid_score["accuracy"] > market_score["accuracy"],
        "logloss": hybrid_score["logloss"] < market_score["logloss"],
        "brier": hybrid_score["brier"] < market_score["brier"],
    }
    return {
        "test_season": season,
        "matches": int(len(selected)),
        "hybrid_metrics": hybrid_score,
        "market_metrics": market_score,
        "wins": wins,
        "all_three_win": bool(all(wins.values())),
    }, y, market, hybrid


def evaluate_gate(
    outer_rows: list[dict], market_score: dict, hybrid_score: dict, final_all_three: bool
) -> dict:
    metric_counts = {
        metric: sum(bool(row["wins"][metric]) for row in outer_rows)
        for metric in ("accuracy", "logloss", "brier")
    }
    all_three_count = sum(bool(row["all_three_win"]) for row in outer_rows)
    checks = {
        "outer_aggregate_all_three": (
            hybrid_score["accuracy"] > market_score["accuracy"]
            and hybrid_score["logloss"] < market_score["logloss"]
            and hybrid_score["brier"] < market_score["brier"]
        ),
        "outer_accuracy_wins_at_least_3_of_4": metric_counts["accuracy"] >= REQUIRED_OUTER_WINS,
        "outer_logloss_wins_at_least_3_of_4": metric_counts["logloss"] >= REQUIRED_OUTER_WINS,
        "outer_brier_wins_at_least_3_of_4": metric_counts["brier"] >= REQUIRED_OUTER_WINS,
        "outer_all_three_wins_at_least_3_of_4": all_three_count >= REQUIRED_OUTER_WINS,
        "final_development_recipe_all_three": bool(final_all_three),
    }
    return {
        **checks,
        "metric_win_counts": metric_counts,
        "all_three_win_count": int(all_three_count),
        "passed": bool(all(checks.values())),
    }


def run(root: Path, work_dir: Path) -> dict:
    assert_frozen_family()
    before = production_state(root)
    history = build_history(work_dir)
    features = build_trainable_features(history)
    variants = {
        (feature_set, model_name): build_variant_oos(features, feature_set, model_name)
        for feature_set in FEATURE_SET_ORDER
        for model_name in MODEL_ORDER
    }

    outer_rows, targets, markets, hybrids = [], [], [], []
    for outer_season in OUTER_TEST_SEASONS:
        inner = inner_seasons(outer_season)
        candidate, candidate_score = select_candidate(variants, inner)
        alpha, alpha_score = select_alpha(variants[candidate], inner)
        fold, y, market, hybrid = score_outer(
            variants[candidate], outer_season, alpha
        )
        fold.update({
            "inner_oos_seasons": list(inner),
            "selected_candidate": f"{candidate[0]}::{candidate[1]}",
            "selected_alpha": alpha,
            "candidate_selection_metrics": candidate_score,
            "alpha_selection_metrics": alpha_score,
        })
        outer_rows.append(fold)
        targets.append(y)
        markets.append(market)
        hybrids.append(hybrid)

    y_outer = np.concatenate(targets)
    market_outer = np.vstack(markets)
    hybrid_outer = np.vstack(hybrids)
    outer_market = metrics(y_outer, market_outer)
    outer_hybrid = metrics(y_outer, hybrid_outer)

    final_candidate, candidate_score = select_candidate(
        variants, DEVELOPMENT_OOS_SEASONS
    )
    final_alpha, alpha_score = select_alpha(
        variants[final_candidate], DEVELOPMENT_OOS_SEASONS
    )
    y_final, ai_final, market_final = arrays(variants[final_candidate])
    hybrid_final = hybrid_probability(market_final, ai_final, final_alpha)
    final_market = metrics(y_final, market_final)
    final_hybrid = metrics(y_final, hybrid_final)
    final_wins = {
        "accuracy": final_hybrid["accuracy"] > final_market["accuracy"],
        "logloss": final_hybrid["logloss"] < final_market["logloss"],
        "brier": final_hybrid["brier"] < final_market["brier"],
    }
    gate = evaluate_gate(
        outer_rows, outer_market, outer_hybrid, all(final_wins.values())
    )
    after = production_state(root)
    if before != after:
        raise RuntimeError("Production artifact state changed during Primeira Liga research")

    return {
        "protocol": PROTOCOL,
        "league": LEAGUE,
        "status": (
            "ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE"
            if gate["passed"]
            else "REJECTED_NO_FREEZE_RECOMMENDATION"
        ),
        "configured_historical_seasons": list(CONFIGURED_SEASONS),
        "historical_seasons": list(ADMITTED_SEASONS),
        "structurally_excluded_seasons": [],
        "current_forbidden_season": CURRENT_FORBIDDEN_SEASON,
        "current_source_read": False,
        "development_oos_seasons": list(DEVELOPMENT_OOS_SEASONS),
        "outer_test_seasons": list(OUTER_TEST_SEASONS),
        "historical_rows": int(len(history)),
        "trainable_rows": int(len(features)),
        "candidate_count": len(FEATURE_SET_ORDER) * len(MODEL_ORDER),
        "alpha_grid": list(ALPHAS),
        "outer_folds": outer_rows,
        "outer_aggregate": {
            "hybrid": outer_hybrid,
            "market": outer_market,
            "metric_win_counts": gate["metric_win_counts"],
            "all_three_win_count": gate["all_three_win_count"],
        },
        "final_development_recipe": {
            "candidate": f"{final_candidate[0]}::{final_candidate[1]}",
            "alpha": final_alpha,
            "candidate_selection_metrics": candidate_score,
            "alpha_selection_metrics": alpha_score,
            "hybrid_metrics": final_hybrid,
            "market_metrics": final_market,
            "wins": final_wins,
        },
        "gate": {
            key: value for key, value in gate.items()
            if key not in {"metric_win_counts", "all_three_win_count", "passed"}
        },
        "all_admitted_historical_data_is_development_only": True,
        "untouched_holdout_claimed": False,
        "artifact_created": False,
        "model_ready": False,
        "prospective_ai_ready": False,
        "production_before": before,
        "production_after": after,
        "production_unchanged": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir",
        type=Path,
        default=Path("artifacts/primeira_liga_nested_development_v1"),
    )
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    result = run(root, args.work_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
