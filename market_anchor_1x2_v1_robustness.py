"""Post-selection robustness diagnostics for frozen MARKET_ANCHOR_1X2_V1.

This module never searches features/lambda or changes the V1 decision. It replays the
frozen Serie A ALL_FOOTBALL/lambda=1 configuration for paired bootstrap uncertainty
on the untouched 2025-2026 test and for descriptive expanding-season trajectory.
Earlier-season trajectory is explicitly retrospective/post-selection diagnostic only.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from historical_football_signal_lab import FEATURE_SETS, RESULT_TO_INT
from historical_football_signal_runner import LEAGUES, download
from market_anchor_1x2_v1 import (
    TEST_SEASON,
    TRAIN_SEASONS,
    VALIDATION_SEASON,
    _market,
    _prepare,
    fit_residual_model,
    market_anchored_probabilities,
    score_probabilities,
)

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1_ROBUSTNESS"
TARGET_LEAGUE = "SERIE_A"
FROZEN_FEATURE_VARIANT = "ALL_FOOTBALL"
FROZEN_LAMBDA = 1.0
BOOTSTRAP_SEED = 20260915
BOOTSTRAP_DRAWS = 20000
EPS = 1e-12


def per_match_deltas(y: np.ndarray, candidate: np.ndarray, market: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    y = np.asarray(y, dtype=int)
    onehot = np.eye(3)[y]
    brier_candidate = np.sum((candidate - onehot) ** 2, axis=1)
    brier_market = np.sum((market - onehot) ** 2, axis=1)
    log_candidate = -np.log(np.clip(candidate[np.arange(len(y)), y], EPS, 1.0))
    log_market = -np.log(np.clip(market[np.arange(len(y)), y], EPS, 1.0))
    return brier_candidate - brier_market, log_candidate - log_market


def paired_bootstrap(delta: np.ndarray, *, seed: int = BOOTSTRAP_SEED, draws: int = BOOTSTRAP_DRAWS) -> dict[str, float]:
    delta = np.asarray(delta, dtype=float)
    if delta.ndim != 1 or len(delta) == 0 or not np.isfinite(delta).all():
        raise ValueError("delta must be a finite non-empty vector")
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(delta), size=(draws, len(delta)))
    boot = delta[indices].mean(axis=1)
    lo, hi = np.quantile(boot, [0.025, 0.975])
    return {
        "mean_delta": float(delta.mean()),
        "bootstrap_ci95_low": float(lo),
        "bootstrap_ci95_high": float(hi),
        "bootstrap_probability_better_than_market": float((boot < 0.0).mean()),
        "draws": int(draws),
        "seed": int(seed),
    }


def _fit_predict(train: pd.DataFrame, test: pd.DataFrame) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    features = list(FEATURE_SETS[FROZEN_FEATURE_VARIANT])
    y_train = train["result"].map(RESULT_TO_INT).to_numpy()
    y_test = test["result"].map(RESULT_TO_INT).to_numpy()
    market_train = _market(train)
    market_test = _market(test)
    model = fit_residual_model(train[features], y_train, market_train)
    candidate = market_anchored_probabilities(
        market_test,
        model.residual_logits(test[features]),
        FROZEN_LAMBDA,
    )
    return y_test, market_test, candidate


def frozen_final_split(league: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the exact training/test split used by frozen V1 final OOT.

    Validation selected feature/lambda but was not used to refit residual weights.
    Including 2024-2025 here would create a different post-hoc model.
    """
    train = league[league["season"].isin(TRAIN_SEASONS)].copy()
    test = league[league["season"] == TEST_SEASON].copy()
    if len(train) == 0 or len(test) == 0:
        raise RuntimeError("frozen V1 final split is incomplete")
    if VALIDATION_SEASON in set(train["season"]):
        raise RuntimeError("validation season must not refit frozen V1 residual weights")
    if set(train["season"]) - set(TRAIN_SEASONS):
        raise RuntimeError("unexpected season entered frozen V1 training split")
    return train, test


def evaluate_robustness(frame: pd.DataFrame) -> dict:
    frame = _prepare(frame)
    league = frame[frame["league"] == TARGET_LEAGUE].copy()
    seasons = sorted(league["season"].unique())
    if TEST_SEASON not in seasons:
        raise RuntimeError("frozen untouched test season missing")

    final_train, final_test = frozen_final_split(league)
    y, market, candidate = _fit_predict(final_train, final_test)
    db, dl = per_match_deltas(y, candidate, market)

    # Earlier seasons are post-selection diagnostics only. They never alter V1 and
    # never determine the frozen 2025-2026 candidate. The final OOT is deliberately
    # excluded from this expanding-history loop because V1 did not refit on validation.
    final_idx = seasons.index(TEST_SEASON)
    walk_forward = []
    for i in range(3, final_idx):
        test_season = seasons[i]
        train = league[league["season"].isin(seasons[:i])].copy()
        test = league[league["season"] == test_season].copy()
        yy, mm, cc = _fit_predict(train, test)
        sm = score_probabilities(yy, mm)
        sc = score_probabilities(yy, cc)
        walk_forward.append({
            "test_season": test_season,
            "train_n": int(len(train)),
            "test_n": int(len(test)),
            "market": sm,
            "candidate": sc,
            "delta_brier": sc["brier"] - sm["brier"],
            "delta_log_loss": sc["log_loss"] - sm["log_loss"],
            "dual_metric_win": bool(sc["brier"] < sm["brier"] and sc["log_loss"] < sm["log_loss"]),
        })

    return {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": "MARKET_ANCHOR_1X2_V1",
        "diagnostic_only": True,
        "no_tuning_performed": True,
        "target_league": TARGET_LEAGUE,
        "frozen_feature_variant": FROZEN_FEATURE_VARIANT,
        "frozen_lambda": FROZEN_LAMBDA,
        "final_oot_season": TEST_SEASON,
        "final_oot_training_seasons": list(TRAIN_SEASONS),
        "validation_season_used_for_selection_not_refit": VALIDATION_SEASON,
        "final_oot_n": int(len(y)),
        "final_oot_market": score_probabilities(y, market),
        "final_oot_candidate": score_probabilities(y, candidate),
        "final_oot_brier_bootstrap": paired_bootstrap(db),
        "final_oot_log_loss_bootstrap": paired_bootstrap(dl),
        "final_oot_candidate_better_match_fraction_brier": float((db < 0).mean()),
        "final_oot_candidate_better_match_fraction_log_loss": float((dl < 0).mean()),
        "retrospective_walk_forward_status": "POST_SELECTION_DESCRIPTIVE_ONLY_NOT_AN_INDEPENDENT_GATE",
        "retrospective_walk_forward": walk_forward,
        "retrospective_prior_season_dual_wins": int(sum(r["dual_metric_win"] for r in walk_forward)),
        "retrospective_prior_seasons": int(len(walk_forward)),
        "production_promotion": False,
        "bet_decision": "NO_BET",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/market_anchor_1x2_v1_robustness/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/market_anchor_1x2_v1_robustness/report.json"))
    args = parser.parse_args()
    frames = [download(cfg, league, args.work_dir / league.lower()) for league, cfg in LEAGUES.items()]
    report = evaluate_robustness(pd.concat(frames, ignore_index=True))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
