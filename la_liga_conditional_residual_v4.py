"""La Liga conditional football residual over the fixed POWER market prior.

Research only. The gate is learned on 2024-25 without using 2025-26 outcomes;
2025-26 is opened once as temporal OOT. No 2026-27 outcomes are used.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from historical_football_signal_lab import FEATURE_SETS, RESULT_TO_INT, add_difference_features
from la_liga_power_anchor_v3 import LEAGUE, TRAIN_SEASONS, VALIDATION_SEASON, TEST_SEASON, LATEST_ALLOWED_DATE, _power_market, load_history
from market_anchor_1x2_v1 import L2_PENALTY, fit_residual_model, market_anchored_probabilities, score_probabilities

EXPERIMENT_ID = "LA_LIGA_CONDITIONAL_RESIDUAL_V4"
FEATURE_VARIANTS = ("FORM", "FORM_GOALS", "FORM_GOALS_CORNERS", "ALL_FOOTBALL")
LAMBDA = 0.25
DISAGREEMENT_QUANTILES = (0.50, 0.65, 0.80)
ENTROPY_QUANTILES = (0.35, 0.65)


def prepare(frame: pd.DataFrame) -> pd.DataFrame:
    out = add_difference_features(frame)
    allowed = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}
    out = out[(out["league"] == LEAGUE) & out["season"].isin(allowed)].copy()
    out = out[(out["match_date"] <= LATEST_ALLOWED_DATE) & out["result"].isin(RESULT_TO_INT)]
    return out.dropna(subset=["market_home_odds", "market_draw_odds", "market_away_odds"]).sort_values("match_date").reset_index(drop=True)


def _entropy(p: np.ndarray) -> np.ndarray:
    return -(p * np.log(np.clip(p, 1e-15, 1.0))).sum(axis=1)


def _row_loss(y: np.ndarray, p: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    onehot = np.eye(3)[y]
    return ((p - onehot) ** 2).sum(axis=1), -np.log(np.clip(p[np.arange(len(y)), y], 1e-15, 1.0))


def _candidate(market: np.ndarray, residual: np.ndarray, mask: np.ndarray) -> np.ndarray:
    corrected = market_anchored_probabilities(market, residual, LAMBDA)
    return np.where(mask[:, None], corrected, market)


def evaluate_frame(frame: pd.DataFrame) -> dict:
    frame = prepare(frame)
    train = frame[frame["season"].isin(TRAIN_SEASONS)].copy()
    val = frame[frame["season"] == VALIDATION_SEASON].copy()
    test = frame[frame["season"] == TEST_SEASON].copy()
    y_train = train["result"].map(RESULT_TO_INT).to_numpy()
    y_val = val["result"].map(RESULT_TO_INT).to_numpy()
    y_test = test["result"].map(RESULT_TO_INT).to_numpy()
    m_train, m_val, m_test = _power_market(train), _power_market(val), _power_market(test)
    val_market_score = score_probabilities(y_val, m_val)
    test_market_score = score_probabilities(y_test, m_test)

    candidates = []
    fitted = {}
    for variant in FEATURE_VARIANTS:
        features = list(FEATURE_SETS[variant])
        model = fit_residual_model(train[features], y_train, m_train, L2_PENALTY)
        fitted[variant] = model
        r_val = model.residual_logits(val[features])
        corrected_val = market_anchored_probabilities(m_val, r_val, LAMBDA)
        disagreement = np.max(np.abs(corrected_val - m_val), axis=1)
        entropy = _entropy(m_val)
        for dq in DISAGREEMENT_QUANTILES:
            d_cut = float(np.quantile(disagreement, dq))
            for eq in ENTROPY_QUANTILES:
                e_cut = float(np.quantile(entropy, eq))
                for entropy_side in ("LOW", "HIGH"):
                    emask = entropy <= e_cut if entropy_side == "LOW" else entropy >= e_cut
                    mask = (disagreement >= d_cut) & emask
                    if mask.sum() < 30:
                        continue
                    p = _candidate(m_val, r_val, mask)
                    s = score_probabilities(y_val, p)
                    candidates.append({
                        "feature_variant": variant, "disagreement_quantile": dq,
                        "entropy_quantile": eq, "entropy_side": entropy_side,
                        "disagreement_cut": d_cut, "entropy_cut": e_cut,
                        "acted_n": int(mask.sum()), **s,
                    })
    admissible = [c for c in candidates if c["brier"] < val_market_score["brier"] and c["log_loss"] < val_market_score["log_loss"]]
    if not admissible:
        selected = None
        test_candidate = m_test.copy()
        acted_n = 0
    else:
        selected = min(admissible, key=lambda c: (c["log_loss"], c["brier"], -c["acted_n"], c["feature_variant"]))
        features = list(FEATURE_SETS[selected["feature_variant"]])
        r_test = fitted[selected["feature_variant"]].residual_logits(test[features])
        corrected_test = market_anchored_probabilities(m_test, r_test, LAMBDA)
        disagreement = np.max(np.abs(corrected_test - m_test), axis=1)
        entropy = _entropy(m_test)
        emask = entropy <= selected["entropy_cut"] if selected["entropy_side"] == "LOW" else entropy >= selected["entropy_cut"]
        mask = (disagreement >= selected["disagreement_cut"]) & emask
        acted_n = int(mask.sum())
        test_candidate = np.where(mask[:, None], corrected_test, m_test)
    test_score = score_probabilities(y_test, test_candidate)
    accepted = selected is not None and test_score["brier"] < test_market_score["brier"] and test_score["log_loss"] < test_market_score["log_loss"]
    return {
        "experiment_id": EXPERIMENT_ID, "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "league": LEAGUE, "research_only": True, "production_promotion": False,
        "betting_enabled": False, "result": "NO_BET", "opened_2026_27_outcomes_used": False,
        "market_prior": "POWER_DEVIG_RAW_DECIMAL_ODDS", "lambda": LAMBDA,
        "gate_features": ["residual_disagreement", "market_entropy"],
        "train_n": int(len(train)), "validation_n": int(len(val)), "test_n": int(len(test)),
        "validation_candidates_evaluated": len(candidates), "validation_admissible": len(admissible),
        "validation_power_market": val_market_score, "selected_gate": selected,
        "test_power_market": test_market_score, "test_candidate": test_score,
        "test_acted_n": acted_n, "test_delta_brier": test_score["brier"] - test_market_score["brier"],
        "test_delta_log_loss": test_score["log_loss"] - test_market_score["log_loss"],
        "conditional_residual_accepted": bool(accepted),
        "active_mode": "CONDITIONAL_RESIDUAL" if accepted else "POWER_MARKET_FALLBACK",
        "acceptance_rule": "gate selected only if validation beats POWER on both Brier and LogLoss; OOT accepted only if it again beats POWER on both",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/la_liga_conditional_residual_v4/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_conditional_residual_v4/report.json"))
    args = parser.parse_args()
    report = evaluate_frame(load_history(args.work_dir))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
