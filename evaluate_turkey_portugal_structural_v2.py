"""Frozen Turkey/Portugal Structural V2 historical calibration evaluation.

Research-only. This module is intentionally separate from runtime configuration:
candidate alpha/threshold values are explicit arguments and are never written to
league runtime configs.

The evaluation is allowed only after
TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1 was preregistered on main.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import requests

import league_structural_edge_v2 as structural_v2
from league_historical_market import MarketTriplet, normalize_market_frame
from league_offline_features import build_temporal_elo_features
from league_offline_history import normalize_football_data_frame
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG
from turkey_super_lig_runtime_config import TURKEY_SUPER_LIG_RUNTIME_CONFIG


ROOT = Path(__file__).resolve().parent
PREREG_PATH = ROOT / "research" / "turkey_portugal_structural_v2_calibration_v1.json"
FOOTBALL_DATA_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"

EXPECTED_PREREG_ID = "TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1"
EXPECTED_PREREG_STATUS = "PREREGISTERED_NOT_EVALUATED"
RESULT_ID = "TURKEY_PORTUGAL_STRUCTURAL_V2_CALIBRATION_V1_EVALUATION"

TARGET_MAP = {"H": 0, "D": 1, "A": 2}
IDENTITY = ["league", "season", "match_date", "home_team", "away_team"]
MARKET_PROBABILITY_COLUMNS = [
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
]
PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)
CONFIGS = {
    "TURKEY_SUPER_LIG": TURKEY_SUPER_LIG_RUNTIME_CONFIG,
    "PRIMEIRA_LIGA": PRIMEIRA_LIGA_RUNTIME_CONFIG,
}


@dataclass(frozen=True)
class Candidate:
    alpha: float
    threshold: float


def _sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def production_state() -> dict[str, str | None]:
    return {name: _sha256(ROOT / name) for name in PRODUCTION_ARTIFACTS}


def load_prereg(path: Path = PREREG_PATH) -> dict:
    prereg = json.loads(path.read_text(encoding="utf-8"))
    if prereg.get("id") != EXPECTED_PREREG_ID:
        raise ValueError("Unexpected preregistration id")
    if prereg.get("status") != EXPECTED_PREREG_STATUS:
        raise ValueError("Unexpected preregistration status")
    if prereg.get("research_only") is not True:
        raise ValueError("Evaluation requires research_only preregistration")

    governance = prereg["governance"]
    required_false = (
        "runtime_config_mutation_during_research",
        "production_model_artifact_mutation",
        "automatic_promotion",
        "copy_final_parameters_from_other_leagues",
        "outcome_dependent_changes_after_freeze",
    )
    if any(governance.get(field) is not False for field in required_false):
        raise ValueError("Preregistration governance contract changed")

    structural = prereg["structural_algorithm"]
    expected_features = [
        "elo_difference",
        "form_difference",
        "venue_win_rate_difference",
        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",
    ]
    if structural.get("implementation") != "league_structural_v2_shadow":
        raise ValueError("Frozen Structural V2 implementation changed")
    if structural.get("score_features") != expected_features:
        raise ValueError("Frozen Structural V2 feature inputs changed")
    if structural.get("reference_stats_fit") != "prior_training_seasons_only":
        raise ValueError("Frozen reference-stat fitting contract changed")
    if structural.get("market_argmax_must_be_preserved") is not True:
        raise ValueError("Frozen argmax-preservation contract changed")

    decision = prereg["decision_contract"]
    if decision.get("runtime_status_before_and_after_research") != "CALIBRATION_REQUIRED":
        raise ValueError("Runtime calibration status contract changed")
    if decision.get("research_result_cannot_activate_structural_v2") is not True:
        raise ValueError("Research activation guard changed")
    return prereg


def _fetch_frame(
    session: requests.Session,
    *,
    code: str,
    competition: str,
) -> pd.DataFrame:
    response = session.get(
        FOOTBALL_DATA_URL.format(code=code, competition=competition),
        timeout=30,
    )
    response.raise_for_status()
    if not response.text.strip():
        raise ValueError("Empty Football-Data response")
    return pd.read_csv(StringIO(response.text))


def _season_code(config, season: str) -> str:
    matches = [
        code
        for code, configured_season in config.historical_source.season_codes.items()
        if configured_season == season
    ]
    if len(matches) != 1:
        raise ValueError(f"{config.identity.identifier}: season mapping is not unique: {season}")
    return matches[0]


def build_league_dataset(
    config,
    league_contract: dict,
    *,
    session: requests.Session,
) -> pd.DataFrame:
    """Build frozen completed-season dataset with leakage-safe temporal features."""
    config.validate()
    league_id = config.identity.identifier
    if config.structural_v2.calibration_status != "CALIBRATION_REQUIRED":
        raise ValueError(f"{league_id}: runtime must remain CALIBRATION_REQUIRED")

    competition = league_contract["football_data_competition"]
    if competition != config.historical_source.competition_code:
        raise ValueError(f"{league_id}: competition code mismatch")

    frozen_columns = league_contract["market_columns"]
    if frozen_columns != ["B365H", "B365D", "B365A"]:
        raise ValueError(f"{league_id}: frozen market columns changed")
    if league_contract["market_source"] != "BET365":
        raise ValueError(f"{league_id}: frozen market source changed")

    triplet = MarketTriplet("B365H", "B365D", "B365A", "BET365")
    normalized_history: list[pd.DataFrame] = []
    normalized_market: list[pd.DataFrame] = []

    for season in league_contract["completed_seasons"]:
        if season == "2026-2027":
            raise ValueError("Current season must not enter historical calibration")
        code = _season_code(config, season)
        source = _fetch_frame(session, code=code, competition=competition)

        history = normalize_football_data_frame(
            source,
            config=config,
            season=season,
            require_complete=True,
        )
        market = normalize_market_frame(
            source,
            config=config,
            season=season,
            triplet=triplet,
        )
        normalized_history.append(history)
        normalized_market.append(market)

    history = (
        pd.concat(normalized_history, ignore_index=True)
        .sort_values(["match_date", "home_team", "away_team"], kind="stable")
        .reset_index(drop=True)
    )
    temporal = build_temporal_elo_features(history, config)

    market = pd.concat(normalized_market, ignore_index=True)
    market = market[
        IDENTITY + MARKET_PROBABILITY_COLUMNS + ["market_valid", "market_source"]
    ].copy()

    feature_columns = [
        "elo_difference",
        "form_difference",
        "venue_win_rate_difference",
        "home_goals_scored_last5",
        "home_goals_conceded_last5",
        "away_goals_scored_last5",
        "away_goals_conceded_last5",
    ]
    left = temporal[IDENTITY + ["result"] + feature_columns].copy()
    merged = left.merge(market, on=IDENTITY, how="left", validate="one_to_one")

    if merged["market_source"].dropna().ne("BET365").any():
        raise ValueError(f"{league_id}: non-BET365 market row entered dataset")
    valid = merged["market_valid"].fillna(False).astype(bool)
    merged = merged.loc[valid].copy()
    if merged.empty:
        raise ValueError(f"{league_id}: no frozen market-valid rows")

    if merged[MARKET_PROBABILITY_COLUMNS].isna().any().any():
        raise ValueError(f"{league_id}: null market probabilities after valid-row filter")
    sums = merged[MARKET_PROBABILITY_COLUMNS].sum(axis=1).to_numpy(dtype=float)
    if not np.allclose(sums, 1.0, atol=1e-12, rtol=0.0):
        raise ValueError(f"{league_id}: no-vig probabilities do not sum to one")
    if not set(merged["result"]).issubset(TARGET_MAP):
        raise ValueError(f"{league_id}: unexpected result label")

    merged["target"] = merged["result"].map(TARGET_MAP).astype(int)
    return merged.reset_index(drop=True)


def apply_candidate(
    market: np.ndarray,
    scores: np.ndarray,
    *,
    alpha: float,
    threshold: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Apply an explicit research candidate without mutating runtime config."""
    if alpha <= 0.0 or alpha > 1.0:
        raise ValueError("alpha must be in (0, 1]")
    if threshold < 0.0:
        raise ValueError("threshold must be non-negative")
    if len(market) != len(scores):
        raise ValueError("market and score row counts differ")

    output = np.asarray(market, dtype=float).copy()
    enabled = np.zeros(len(output), dtype=bool)
    weights = np.zeros(len(output), dtype=float)

    for index, score in enumerate(np.asarray(scores, dtype=float)):
        if not np.isfinite(score) or abs(score) < threshold:
            continue
        enabled[index] = True
        candidate = structural_v2.raw_structural_correction(
            output[index],
            float(score),
            structural_alpha=float(alpha),
        )
        safe, weight = structural_v2.preserve_market_argmax(output[index], candidate)
        output[index] = safe
        weights[index] = float(weight)

    output = np.clip(output, 1e-12, None)
    output = output / output.sum(axis=1, keepdims=True)
    if np.any(np.argmax(output, axis=1) != np.argmax(market, axis=1)):
        raise RuntimeError("Structural candidate changed market argmax")
    return output, enabled, weights


def metric_values(y: np.ndarray, probability: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    probability = np.asarray(probability, dtype=float)
    probability = np.clip(probability, 1e-12, 1.0)
    probability = probability / probability.sum(axis=1, keepdims=True)

    row_index = np.arange(len(y))
    logloss = -np.mean(np.log(probability[row_index, y]))
    one_hot = np.eye(3, dtype=float)[y]
    brier = np.mean(np.sum((probability - one_hot) ** 2, axis=1))
    accuracy = np.mean(np.argmax(probability, axis=1) == y)
    return {
        "logloss": float(logloss),
        "brier": float(brier),
        "accuracy": float(accuracy),
    }


def _evaluate_candidate_on_fold(
    training: pd.DataFrame,
    validation: pd.DataFrame,
    candidate: Candidate,
) -> dict:
    stats = structural_v2.fit_stats(training)
    score = structural_v2.structural_score(validation, stats).to_numpy(dtype=float)
    market = validation[MARKET_PROBABILITY_COLUMNS].to_numpy(dtype=float)
    y = validation["target"].to_numpy(dtype=int)
    corrected, enabled, weights = apply_candidate(
        market,
        score,
        alpha=candidate.alpha,
        threshold=candidate.threshold,
    )
    market_metrics = metric_values(y, market)
    v2_metrics = metric_values(y, corrected)
    argmax_changes = int(np.sum(np.argmax(market, axis=1) != np.argmax(corrected, axis=1)))
    if argmax_changes:
        raise RuntimeError("Inner fold argmax preservation failed")
    return {
        "rows": int(len(validation)),
        "market_logloss": market_metrics["logloss"],
        "v2_logloss": v2_metrics["logloss"],
        "logloss_delta": v2_metrics["logloss"] - market_metrics["logloss"],
        "market_brier": market_metrics["brier"],
        "v2_brier": v2_metrics["brier"],
        "brier_delta": v2_metrics["brier"] - market_metrics["brier"],
        "enabled_rows": int(enabled.sum()),
        "argmax_clipped_rows": int(np.sum(enabled & (weights < 0.999999))),
        "argmax_changes": argmax_changes,
    }


def summarize_inner_folds(candidate: Candidate, folds: list[dict], min_fraction: float) -> dict:
    if not folds:
        raise ValueError("Candidate has no inner validation folds")
    total_rows = sum(fold["rows"] for fold in folds)
    if total_rows <= 0:
        raise ValueError("Inner folds contain no rows")
    weighted_ll = sum(fold["rows"] * fold["logloss_delta"] for fold in folds) / total_rows
    weighted_brier = sum(fold["rows"] * fold["brier_delta"] for fold in folds) / total_rows
    required_positive = int(math.ceil(min_fraction * len(folds)))
    ll_positive = sum(fold["logloss_delta"] < 0.0 for fold in folds)
    brier_positive = sum(fold["brier_delta"] < 0.0 for fold in folds)
    robust = (
        weighted_ll < 0.0
        and weighted_brier < 0.0
        and ll_positive >= required_positive
        and brier_positive >= required_positive
    )
    return {
        "alpha": candidate.alpha,
        "threshold": candidate.threshold,
        "fold_count": len(folds),
        "rows": int(total_rows),
        "weighted_logloss_delta": float(weighted_ll),
        "weighted_brier_delta": float(weighted_brier),
        "logloss_improving_folds": int(ll_positive),
        "brier_improving_folds": int(brier_positive),
        "required_improving_folds": required_positive,
        "robust": bool(robust),
        "folds": folds,
    }


def select_candidate(
    training: pd.DataFrame,
    *,
    alphas: Iterable[float],
    thresholds: Iterable[float],
    min_fraction: float,
) -> tuple[Candidate | None, list[dict]]:
    """Select only from inner folds; caller never passes the outer-test frame."""
    seasons = sorted(training["season"].astype(str).unique().tolist())
    if len(seasons) < 2:
        return None, []

    reports: list[dict] = []
    for alpha in alphas:
        for threshold in thresholds:
            candidate = Candidate(float(alpha), float(threshold))
            folds: list[dict] = []
            for validation_season in seasons[1:]:
                inner_training = training[
                    training["season"].astype(str) < validation_season
                ].copy()
                validation = training[
                    training["season"].astype(str) == validation_season
                ].copy()
                if inner_training.empty or validation.empty:
                    continue
                fold = _evaluate_candidate_on_fold(inner_training, validation, candidate)
                fold["validation_season"] = validation_season
                fold["training_seasons"] = sorted(
                    inner_training["season"].astype(str).unique().tolist()
                )
                folds.append(fold)
            reports.append(summarize_inner_folds(candidate, folds, min_fraction))

    robust = [report for report in reports if report["robust"]]
    if not robust:
        return None, reports
    chosen = min(
        robust,
        key=lambda report: (
            report["weighted_logloss_delta"],
            report["weighted_brier_delta"],
            report["alpha"],
            -report["threshold"],
        ),
    )
    return Candidate(chosen["alpha"], chosen["threshold"]), reports


def evaluate_outer_fold(
    dataset: pd.DataFrame,
    *,
    test_season: str,
    alphas: list[float],
    thresholds: list[float],
    min_fraction: float,
) -> dict:
    training = dataset[dataset["season"].astype(str) < test_season].copy()
    test = dataset[dataset["season"].astype(str) == test_season].copy()
    if training.empty or test.empty:
        raise ValueError(f"Missing outer data for {test_season}")

    selected, candidate_reports = select_candidate(
        training,
        alphas=alphas,
        thresholds=thresholds,
        min_fraction=min_fraction,
    )

    market = test[MARKET_PROBABILITY_COLUMNS].to_numpy(dtype=float)
    y = test["target"].to_numpy(dtype=int)
    market_metrics = metric_values(y, market)

    if selected is None:
        corrected = market.copy()
        enabled = np.zeros(len(test), dtype=bool)
        weights = np.zeros(len(test), dtype=float)
        decision = "MARKET_ONLY"
    else:
        stats = structural_v2.fit_stats(training)
        score = structural_v2.structural_score(test, stats).to_numpy(dtype=float)
        corrected, enabled, weights = apply_candidate(
            market,
            score,
            alpha=selected.alpha,
            threshold=selected.threshold,
        )
        decision = "STRUCTURAL_V2_CANDIDATE"

    v2_metrics = metric_values(y, corrected)
    argmax_changes = int(np.sum(np.argmax(market, axis=1) != np.argmax(corrected, axis=1)))
    if argmax_changes != 0:
        raise RuntimeError("Outer fold argmax preservation failed")

    return {
        "test_season": test_season,
        "training_seasons": sorted(training["season"].astype(str).unique().tolist()),
        "training_rows": int(len(training)),
        "test_rows": int(len(test)),
        "selection_decision": decision,
        "selected_candidate": (
            None
            if selected is None
            else {"alpha": selected.alpha, "threshold": selected.threshold}
        ),
        "parameter_selection": candidate_reports,
        "enabled_rows": int(enabled.sum()),
        "enabled_rate": float(enabled.mean()) if len(enabled) else 0.0,
        "argmax_clipped_rows": int(np.sum(enabled & (weights < 0.999999))),
        "argmax_changes": argmax_changes,
        "market_metrics": market_metrics,
        "evaluated_metrics": v2_metrics,
        "logloss_delta": v2_metrics["logloss"] - market_metrics["logloss"],
        "brier_delta": v2_metrics["brier"] - market_metrics["brier"],
        "accuracy_delta": v2_metrics["accuracy"] - market_metrics["accuracy"],
    }


def aggregate_outer(folds: list[dict]) -> dict:
    if not folds:
        raise ValueError("No outer folds")
    total_rows = sum(fold["test_rows"] for fold in folds)
    weighted = {}
    for field in ("logloss_delta", "brier_delta", "accuracy_delta"):
        weighted[field] = float(
            sum(fold["test_rows"] * fold[field] for fold in folds) / total_rows
        )
    return {
        "outer_folds": len(folds),
        "rows": int(total_rows),
        "market_only_folds": sum(fold["selection_decision"] == "MARKET_ONLY" for fold in folds),
        "structural_candidate_folds": sum(
            fold["selection_decision"] == "STRUCTURAL_V2_CANDIDATE" for fold in folds
        ),
        "weighted_logloss_delta": weighted["logloss_delta"],
        "weighted_brier_delta": weighted["brier_delta"],
        "weighted_accuracy_delta": weighted["accuracy_delta"],
        "argmax_changes": int(sum(fold["argmax_changes"] for fold in folds)),
    }


def evaluate_league(
    config,
    league_contract: dict,
    structural_contract: dict,
    walkforward_contract: dict,
    *,
    session: requests.Session,
) -> dict:
    dataset = build_league_dataset(config, league_contract, session=session)
    outer_seasons = walkforward_contract["outer_test_seasons"]
    alphas = structural_contract["alphas"]
    thresholds = structural_contract["thresholds"]
    min_fraction = float(walkforward_contract["minimum_positive_fraction_per_metric"])

    folds = [
        evaluate_outer_fold(
            dataset,
            test_season=season,
            alphas=alphas,
            thresholds=thresholds,
            min_fraction=min_fraction,
        )
        for season in outer_seasons
    ]
    aggregate = aggregate_outer(folds)
    if aggregate["argmax_changes"] != 0:
        raise RuntimeError("Aggregate argmax-change contract failed")

    return {
        "league": config.identity.identifier,
        "runtime_calibration_status_before": config.structural_v2.calibration_status,
        "runtime_calibration_status_after": config.structural_v2.calibration_status,
        "market_source": league_contract["market_source"],
        "market_valid_rows": int(len(dataset)),
        "available_seasons_in_evaluation": sorted(dataset["season"].astype(str).unique().tolist()),
        "outer_folds": folds,
        "aggregate_outer_oos": aggregate,
        "research_conclusion": (
            "HISTORICAL_OOS_SIGNAL_OBSERVED"
            if aggregate["weighted_logloss_delta"] < 0.0
            and aggregate["weighted_brier_delta"] < 0.0
            and aggregate["structural_candidate_folds"] > 0
            else "CALIBRATION_NOT_SUPPORTED_OR_INCONSISTENT"
        ),
        "runtime_action": "NONE_REQUIRES_SEPARATE_EXPLICIT_REVIEW_AND_PR",
    }


def run_evaluation(*, prereg_path: Path = PREREG_PATH) -> dict:
    prereg = load_prereg(prereg_path)
    before = production_state()
    session = requests.Session()
    session.headers.update({"User-Agent": "football-ai-structural-v2-research/1.0"})

    leagues = []
    for league_id, league_contract in prereg["leagues"].items():
        if league_id not in CONFIGS:
            raise ValueError(f"Unknown preregistered league: {league_id}")
        leagues.append(
            evaluate_league(
                CONFIGS[league_id],
                league_contract,
                prereg["candidate_search_space"],
                prereg["nested_walk_forward"],
                session=session,
            )
        )

    after = production_state()
    if before != after:
        raise RuntimeError("Production model artifacts changed during research evaluation")

    return {
        "id": RESULT_ID,
        "preregistration_id": prereg["id"],
        "preregistration_frozen_at_utc": prereg["frozen_at_utc"],
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "research_only": True,
        "outcomes_read": True,
        "outcome_gate": "ALLOWED_AFTER_PREREGISTRATION_MERGED_TO_MAIN",
        "odds_api_requests": 0,
        "supabase_operations": 0,
        "production_artifacts_unchanged": True,
        "automatic_promotion": False,
        "runtime_mutation": False,
        "leagues": leagues,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prereg", type=Path, default=PREREG_PATH)
    args = parser.parse_args()
    report = run_evaluation(prereg_path=args.prereg)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
