"""La Liga POWER-de-vig market anchor plus bounded football residual, research only.

This follow-up keeps 2026-27 outcomes out of fitting/selection/evaluation. Raw
historical decimal odds are reconstructed with the already-selected POWER de-vig
method. Football residual selection uses 2024-25 only and is evaluated once on
untouched 2025-26. Lambda zero is an exact identity to the POWER market prior.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from bookmaker_reconstruction_devig_v1 import power
from historical_football_signal_lab import FEATURE_SETS, RESULT_TO_INT, add_difference_features
from historical_football_signal_runner import LEAGUES, download
from market_anchor_1x2_v1 import (
    L2_PENALTY,
    fit_residual_model,
    market_anchored_probabilities,
    score_probabilities,
)

EXPERIMENT_ID = "LA_LIGA_POWER_ANCHOR_V3"
LEAGUE = "LA_LIGA"
TRAIN_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
LATEST_ALLOWED_DATE = pd.Timestamp("2026-06-30")
FEATURE_VARIANTS = ("FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
LAMBDA_GRID = (0.0, 0.10, 0.25, 0.50, 0.75, 1.0)


def _power_market(frame: pd.DataFrame) -> np.ndarray:
    values = frame[["market_home", "market_draw", "market_away"]].to_numpy(float)
    if not np.isfinite(values).all() or (values <= 0).any():
        raise ValueError("market values must be finite and positive")
    # Historical signal lab stores proportionally de-vigged probabilities, so the
    # raw overround is no longer recoverable here. V3 therefore requires raw odds
    # columns populated by its loader before evaluation.
    if not {"market_home_odds", "market_draw_odds", "market_away_odds"}.issubset(frame.columns):
        raise ValueError("V3 requires raw decimal odds; normalized market columns are insufficient")
    odds = frame[["market_home_odds", "market_draw_odds", "market_away_odds"]].to_numpy(float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("raw decimal odds must be finite and > 1")
    return power(1.0 / odds)


def _prepare(frame: pd.DataFrame) -> pd.DataFrame:
    out = add_difference_features(frame)
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    out = out[(out["league"] == LEAGUE) & out["season"].isin(allowed)].copy()
    out = out[out["match_date"] <= LATEST_ALLOWED_DATE]
    out = out[out["result"].isin(RESULT_TO_INT)]
    required = ["market_home_odds", "market_draw_odds", "market_away_odds"]
    out = out.dropna(subset=required)
    return out.sort_values(["match_date"], kind="stable").reset_index(drop=True)


def _choose_on_validation(train: pd.DataFrame, validation: pd.DataFrame):
    y_train = train["result"].map(RESULT_TO_INT).to_numpy()
    y_val = validation["result"].map(RESULT_TO_INT).to_numpy()
    market_train = _power_market(train)
    market_val = _power_market(validation)
    market_score = score_probabilities(y_val, market_val)
    choices, fitted = [], {}
    for variant in FEATURE_VARIANTS:
        features = list(FEATURE_SETS[variant])
        model = fit_residual_model(train[features], y_train, market_train, L2_PENALTY)
        fitted[variant] = model
        residual = model.residual_logits(validation[features])
        for lam in LAMBDA_GRID:
            p = market_anchored_probabilities(market_val, residual, lam)
            score = score_probabilities(y_val, p)
            choices.append({"feature_variant": variant, "lambda": lam, **score})
    admissible = [
        c for c in choices
        if c["lambda"] > 0.0
        and c["brier"] < market_score["brier"]
        and c["log_loss"] < market_score["log_loss"]
    ]
    if not admissible:
        return {"feature_variant": "MARKET", "lambda": 0.0, **market_score}, choices, None
    selected = min(admissible, key=lambda c: (c["log_loss"], c["brier"], c["lambda"], c["feature_variant"]))
    return selected, choices, fitted[selected["feature_variant"]]


def evaluate_frame(frame: pd.DataFrame) -> dict:
    frame = _prepare(frame)
    train = frame[frame["season"].isin(TRAIN_SEASONS)].copy()
    validation = frame[frame["season"] == VALIDATION_SEASON].copy()
    test = frame[frame["season"] == TEST_SEASON].copy()
    if min(len(train), len(validation), len(test)) == 0:
        raise RuntimeError("La Liga V3 requires complete train/validation/test seasons")

    selected, choices, model = _choose_on_validation(train, validation)
    y_test = test["result"].map(RESULT_TO_INT).to_numpy()
    market_test = _power_market(test)
    market_score = score_probabilities(y_test, market_test)
    if selected["lambda"] == 0.0:
        candidate = market_test.copy()
    else:
        features = list(FEATURE_SETS[selected["feature_variant"]])
        candidate = market_anchored_probabilities(
            market_test, model.residual_logits(test[features]), float(selected["lambda"])
        )
    candidate_score = score_probabilities(y_test, candidate)
    accepted = candidate_score["brier"] < market_score["brier"] and candidate_score["log_loss"] < market_score["log_loss"]
    active = candidate if accepted else market_test
    active_score = score_probabilities(y_test, active)
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "league": LEAGUE,
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "market_prior": "POWER_DEVIG_RAW_DECIMAL_ODDS",
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "untouched_test_season": TEST_SEASON,
        "feature_variants": list(FEATURE_VARIANTS),
        "lambda_grid": list(LAMBDA_GRID),
        "l2_penalty": L2_PENALTY,
        "train_n": int(len(train)),
        "validation_n": int(len(validation)),
        "test_n": int(len(test)),
        "selected_feature_variant": selected["feature_variant"],
        "selected_lambda": float(selected["lambda"]),
        "validation_candidates_evaluated": len(choices),
        "validation_power_market": score_probabilities(validation["result"].map(RESULT_TO_INT).to_numpy(), _power_market(validation)),
        "validation_selected": {k: selected[k] for k in ("brier", "log_loss", "accuracy")},
        "test_power_market": market_score,
        "test_residual_candidate": candidate_score,
        "test_delta_brier": candidate_score["brier"] - market_score["brier"],
        "test_delta_log_loss": candidate_score["log_loss"] - market_score["log_loss"],
        "residual_accepted": bool(accepted),
        "active_mode": "RESIDUAL" if accepted else "POWER_MARKET_FALLBACK",
        "active_test": active_score,
        "acceptance_rule": "candidate OOT Brier < POWER market AND candidate OOT LogLoss < POWER market; otherwise exact POWER market fallback",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/la_liga_power_anchor_v3/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_power_anchor_v3/report.json"))
    args = parser.parse_args()
    cfg = LEAGUES[LEAGUE]
    frame = download(cfg, LEAGUE, args.work_dir)
    # The existing historical runner exposes normalized market columns, not raw
    # decimal odds. Fail closed until the raw-odds join is explicitly implemented.
    report = evaluate_frame(frame)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
