"""Frozen market-residual process-vs-results divergence experiment (#562).

The evaluator uses only zero-cost Football-Data Bundesliga/Ligue 1 history.
It audits the complete source contract before reading FTR values, constructs
strict same-season five-match features without current-match leakage, and
compares a calibrated market model with the same model plus the preregistered
process/result divergence features.
"""
from __future__ import annotations

import math
from collections import defaultdict, deque
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import requests
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get


EXPERIMENT_ID = "MARKET_RESIDUAL_PROCESS_DIVERGENCE_V1"
BASE = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
LEAGUES = {"BUNDESLIGA": "D1", "LIGUE_1": "F1"}
SEASONS = {
    f"{year % 100:02d}{(year + 1) % 100:02d}": f"{year}-{year + 1}"
    for year in range(2019, 2026)
}
REFERENCE = {f"{year}-{year + 1}" for year in range(2019, 2024)}
VALIDATION = "2024-2025"
TEST = "2025-2026"
REQUIRED_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTR",
    "HS",
    "AS",
    "HST",
    "AST",
    "B365H",
    "B365D",
    "B365A",
}
MARKET_FEATURES = ["market_home", "market_draw", "market_away"]
DIVERGENCE_FEATURES = [
    "home_process_result_divergence_5",
    "away_process_result_divergence_5",
    "diff_process_result_divergence_5",
]
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
BOOTSTRAP_DRAWS = 5000
SEED = 20261006


def _download_and_audit() -> tuple[dict[tuple[str, str], bytes], dict[str, Any], bool]:
    """Fetch fixed files and audit headers before any outcome value is read."""
    payloads: dict[tuple[str, str], bytes] = {}
    files: dict[str, Any] = {}
    source_gate = True
    original_get = requests.get
    try:
        requests.get = _official_or_pinned_mirror_get
        for league, competition in LEAGUES.items():
            for code, season in SEASONS.items():
                response = requests.get(
                    BASE.format(code=code, competition=competition), timeout=60
                )
                response.raise_for_status()
                payload = response.content
                header = pd.read_csv(BytesIO(payload), nrows=0)
                missing = sorted(REQUIRED_COLUMNS - set(header.columns))
                files[f"{league}:{season}"] = {
                    "missing_required_columns": missing,
                    "market_triplet": ["B365H", "B365D", "B365A"],
                }
                if missing:
                    source_gate = False
                payloads[(league, season)] = payload
    finally:
        requests.get = original_get
    return payloads, {
        "outcome_read_before_audit": False,
        "leagues": list(LEAGUES),
        "seasons": list(SEASONS.values()),
        "required_columns": sorted(REQUIRED_COLUMNS),
        "files": files,
        "header_gate_passed": source_gate,
    }, source_gate


def _number(value: Any) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return math.nan
    return result if math.isfinite(result) else math.nan


def _market_probabilities(row: pd.Series) -> tuple[float, float, float] | None:
    odds = np.asarray(
        [_number(row.get("B365H")), _number(row.get("B365D")), _number(row.get("B365A"))],
        dtype=float,
    )
    if not np.isfinite(odds).all() or not (odds > 1.0).all():
        return None
    inverse = 1.0 / odds
    probabilities = inverse / inverse.sum()
    return tuple(float(value) for value in probabilities)


def _points(result: str) -> tuple[float, float]:
    if result == "H":
        return 3.0, 0.0
    if result == "D":
        return 1.0, 1.0
    if result == "A":
        return 0.0, 3.0
    return math.nan, math.nan


def _divergence(history: deque[tuple[float, float, float]]) -> float:
    if len(history) != 5:
        return math.nan
    values = np.asarray(history, dtype=float)
    if not np.isfinite(values).all():
        return math.nan
    denominator = float(values[:, 1].sum() + values[:, 2].sum())
    if denominator <= 0:
        return math.nan
    points_rate = float(values[:, 0].sum() / 15.0)
    sot_share = float(values[:, 1].sum() / denominator)
    return sot_share - points_rate


def build_features(
    payloads: dict[tuple[str, str], bytes]
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Build only eligible fixtures using prior five matches from the same season."""
    rows: list[dict[str, Any]] = []
    coverage: dict[str, Any] = {}
    for (league, season), payload in sorted(payloads.items()):
        frame = pd.read_csv(BytesIO(payload), usecols=lambda c: c in REQUIRED_COLUMNS)
        frame["_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
        frame = frame.sort_values("_date", kind="stable")
        histories: dict[str, deque[tuple[float, float, float]]] = defaultdict(
            lambda: deque(maxlen=5)
        )
        eligible = 0
        for _, row in frame.iterrows():
            home = str(row.get("HomeTeam", ""))
            away = str(row.get("AwayTeam", ""))
            result = str(row.get("FTR", ""))
            market = _market_probabilities(row)
            home_divergence = _divergence(histories[home])
            away_divergence = _divergence(histories[away])
            outcome = RESULT_TO_INT.get(result)
            if (
                market is not None
                and outcome is not None
                and math.isfinite(home_divergence)
                and math.isfinite(away_divergence)
            ):
                rows.append(
                    {
                        "league": league,
                        "season": season,
                        "match_date": row["_date"],
                        "home_team": home,
                        "away_team": away,
                        "outcome": outcome,
                        "market_home": market[0],
                        "market_draw": market[1],
                        "market_away": market[2],
                        "home_process_result_divergence_5": home_divergence,
                        "away_process_result_divergence_5": away_divergence,
                        "diff_process_result_divergence_5": (
                            home_divergence - away_divergence
                        ),
                    }
                )
                eligible += 1

            home_points, away_points = _points(result)
            home_sot = _number(row.get("HST"))
            away_sot = _number(row.get("AST"))
            histories[home].append((home_points, home_sot, away_sot))
            histories[away].append((away_points, away_sot, home_sot))
        coverage[f"{league}:{season}"] = {
            "raw_rows": int(len(frame)),
            "eligible_rows": eligible,
        }
    return pd.DataFrame(rows), coverage


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=2000, solver="lbfgs")),
        ]
    )


def _per_match_losses(outcome: np.ndarray, probabilities: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    clipped = np.clip(probabilities, 1e-15, 1.0)
    log_losses = -np.log(clipped[np.arange(len(outcome)), outcome])
    one_hot = np.eye(3)[outcome]
    brier = np.sum((probabilities - one_hot) ** 2, axis=1)
    return log_losses, brier


def _paired_evaluation(train: pd.DataFrame, evaluated: pd.DataFrame) -> tuple[dict[str, Any], pd.DataFrame]:
    if train.empty or evaluated.empty:
        raise ValueError("temporal train/evaluation split is empty")
    y_train = train["outcome"].to_numpy(int)
    y_eval = evaluated["outcome"].to_numpy(int)
    if set(y_train) != {0, 1, 2}:
        raise ValueError("training split does not contain all 1X2 outcome classes")

    baseline = _model()
    candidate = _model()
    baseline.fit(train[MARKET_FEATURES], y_train)
    candidate.fit(train[MARKET_FEATURES + DIVERGENCE_FEATURES], y_train)
    baseline_p = baseline.predict_proba(evaluated[MARKET_FEATURES])
    candidate_p = candidate.predict_proba(
        evaluated[MARKET_FEATURES + DIVERGENCE_FEATURES]
    )
    baseline_ll, baseline_brier = _per_match_losses(y_eval, baseline_p)
    candidate_ll, candidate_brier = _per_match_losses(y_eval, candidate_p)
    losses = evaluated[["league", "season", "home_team", "away_team"]].copy()
    losses["log_loss_delta"] = candidate_ll - baseline_ll
    losses["brier_delta"] = candidate_brier - baseline_brier
    summary = {
        "rows": int(len(losses)),
        "market_model_log_loss": float(baseline_ll.mean()),
        "candidate_log_loss": float(candidate_ll.mean()),
        "candidate_minus_market_log_loss": float(losses["log_loss_delta"].mean()),
        "market_model_brier": float(baseline_brier.mean()),
        "candidate_brier": float(candidate_brier.mean()),
        "candidate_minus_market_brier": float(losses["brier_delta"].mean()),
        "market_model_accuracy": float((baseline_p.argmax(axis=1) == y_eval).mean()),
        "candidate_accuracy": float((candidate_p.argmax(axis=1) == y_eval).mean()),
        "by_league": {
            league: {
                "rows": int(len(part)),
                "candidate_minus_market_log_loss": float(part["log_loss_delta"].mean()),
                "candidate_minus_market_brier": float(part["brier_delta"].mean()),
            }
            for league, part in losses.groupby("league")
        },
    }
    return summary, losses


def _bootstrap(losses: pd.DataFrame) -> dict[str, Any]:
    if losses.empty:
        return {"draws": BOOTSTRAP_DRAWS, "ci95_low": None, "ci95_high": None}
    groups = [part["log_loss_delta"].to_numpy(float) for _, part in losses.groupby("league")]
    rng = np.random.default_rng(SEED)
    draws = np.empty(BOOTSTRAP_DRAWS)
    for index in range(BOOTSTRAP_DRAWS):
        sample = np.concatenate(
            [values[rng.integers(0, len(values), len(values))] for values in groups]
        )
        draws[index] = float(sample.mean())
    return {
        "draws": BOOTSTRAP_DRAWS,
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
    }


def _formal_gate(validation: dict[str, Any], test: dict[str, Any], source_gate: bool) -> dict[str, Any]:
    league_deltas = [
        part["candidate_minus_market_log_loss"]
        for part in test.get("by_league", {}).values()
    ]
    gates = {
        "source_and_leakage_checks_pass": source_gate,
        "validation_log_loss_improves": validation.get("candidate_minus_market_log_loss", 0) < 0,
        "validation_brier_improves": validation.get("candidate_minus_market_brier", 0) < 0,
        "test_log_loss_improves": test.get("candidate_minus_market_log_loss", 0) < 0,
        "test_brier_improves": test.get("candidate_minus_market_brier", 0) < 0,
        "test_log_loss_ci95_upper_below_zero": (
            test.get("bootstrap", {}).get("ci95_high") is not None
            and test["bootstrap"]["ci95_high"] < 0
        ),
        "no_positive_test_league_log_loss_delta": (
            len(league_deltas) == len(LEAGUES)
            and all(value <= 0 for value in league_deltas)
        ),
    }
    return {"supported": all(gates.values()), "gates": gates}


def _blocked(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    empty = {
        "rows": 0,
        "candidate_minus_market_log_loss": None,
        "candidate_minus_market_brier": None,
        "by_league": {},
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "research_only": True,
        "source_audit": audit,
        "validation": empty,
        "test": {**empty, "bootstrap": {"draws": BOOTSTRAP_DRAWS, "ci95_low": None, "ci95_high": None}},
        "formal_gate": {"supported": False, "reason": reason, "gates": {}},
        "supported": False,
        "decision": "BLOCKED_BY_SOURCE_GAP",
        "interpretation_guard": reason,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate_payloads(payloads: dict[tuple[str, str], bytes], audit: dict[str, Any]) -> dict[str, Any]:
    features, coverage = build_features(payloads)
    audit = {**audit, "coverage": coverage, "outcome_read_after_audit": True}
    required_splits = REFERENCE | {VALIDATION, TEST}
    if features.empty or not required_splits.issubset(set(features["season"])):
        return _blocked(audit, "Frozen temporal split has insufficient eligible rows.")
    for season in (VALIDATION, TEST):
        if set(features[features["season"] == season]["league"]) != set(LEAGUES):
            return _blocked(
                audit,
                f"Both frozen leagues must be present in {season}.",
            )

    reference = features[features["season"].isin(REFERENCE)]
    validation_rows = features[features["season"] == VALIDATION]
    test_rows = features[features["season"] == TEST]
    validation, _ = _paired_evaluation(reference, validation_rows)
    test, test_losses = _paired_evaluation(
        features[features["season"].isin(REFERENCE | {VALIDATION})], test_rows
    )
    test["bootstrap"] = _bootstrap(test_losses)
    gate = _formal_gate(validation, test, True)
    supported = bool(gate["supported"])
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_MARKET_INCREMENTAL_PROCESS_DIVERGENCE",
        "research_only": True,
        "source_audit": audit,
        "temporal_design": {
            "development": sorted(REFERENCE),
            "validation": VALIDATION,
            "untouched_test": TEST,
            "opened_2026_27_outcomes": False,
        },
        "feature_contract": {
            "window": 5,
            "same_season_only": True,
            "points_rate": "points_won / 15",
            "sot_share": "sum(SOT_for) / (sum(SOT_for) + sum(SOT_against))",
            "divergence": "sot_share_5 - points_rate_5",
        },
        "validation": validation,
        "test": test,
        "formal_gate": gate,
        "supported": supported,
        "decision": (
            "SUPPORTED_MARKET_RESIDUAL_PROCESS_DIVERGENCE"
            if supported
            else "NO_STABLE_MARKET_RESIDUAL_PROCESS_DIVERGENCE"
        ),
        "interpretation_guard": (
            "The fixed process-vs-results divergence added stable historical OOS probability information beyond the fitted market baseline; this is not betting or production authorization."
            if supported
            else "The frozen process-vs-results representation did not pass every validation, untouched-test, uncertainty and cross-league gate; do not retune it on these outcomes."
        ),
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = _download_and_audit()
    if not source_gate:
        return _blocked(audit, "Required zero-cost Football-Data columns are unavailable.")
    return evaluate_payloads(payloads, audit)


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
