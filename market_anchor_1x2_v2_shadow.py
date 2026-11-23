"""Frozen prospective-shadow contract for MARKET_ANCHOR_1X2_V2.

Research only. The Serie A residual recipe is inherited from MARKET_ANCHOR_1X2_V1
without re-selection on opened 2026-27 outcomes. A stricter predeclared stability
gate controls whether that residual may become active. The frozen V1 robustness
evidence does not pass the gate, so V2 fails closed to the exact de-vigged market
(lambda=0) while the lambda=1 residual remains diagnostic shadow-only. Shadow rows
are outcome-free and must be captured strictly before kickoff. This module never
reads, writes, trains, or promotes production .pkl artifacts.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from historical_football_signal_lab import FEATURE_SETS, RESULT_TO_INT
from market_anchor_1x2_v1 import (
    L2_PENALTY,
    _market,
    _prepare,
    fit_residual_model,
    market_anchored_probabilities,
    validate_probabilities,
)
from serie_a_runtime_config import SERIE_A_RUNTIME_CONFIG

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V2"
EVIDENCE_CLASS = "PROSPECTIVE_SHADOW"
SOURCE_EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1"
PRIMARY_LEAGUE = "SERIE_A"
FEATURE_VARIANT = "ALL_FOOTBALL"
SHADOW_RESIDUAL_LAMBDA = 1.0
ACTIVE_LAMBDA = 0.0
STABILITY_GATE_PASSED = False
STABILITY_REQUIRED_PRIOR_SEASONS = 6
STABILITY_MIN_DUAL_WINS = 4
STABILITY_MAX_CI95_HIGH = 0.0
STABILITY_MIN_PROBABILITY_BETTER = 0.95
SOURCE_ROBUSTNESS_REPORT_BLOB_SHA = "96d2f462849a70276a2c27a2c0cc18ec0672b00a"
REFIT_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2026))
TRAINING_DATA_THROUGH = pd.Timestamp("2026-06-30T23:59:59Z")
ADMISSION_NOT_BEFORE = pd.Timestamp("2026-09-16T00:00:00Z")
FIRST_OUTCOME_READ_GATE = 30
INCUMBENT_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
# Keep the same narrow V2-only alias used by the original historical feature adapter.
V2_HISTORICAL_TEAM_ALIASES = {"Atalanta BC": "Atalanta"}
FROZEN_CANDIDATE_ARTIFACT_SHA256 = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
FORBIDDEN_OUTCOME_FIELDS = frozenset({
    "result", "outcome", "home_goals", "away_goals", "score", "final_score",
    # Generic nested score-provider containers and common goal-count aliases.
    "goal", "goals", "goal_count", "goals_count", "total_goals",
    "goals_scored", "goals_conceded", "goals_for", "goals_against",
    "goals_home", "goals_away", "home_goal", "away_goal",
    "home_goals_scored", "away_goals_scored",
    "home_goals_conceded", "away_goals_conceded",
    "score_home", "score_away",
    "full_time_goals", "half_time_goals", "fulltime_goals", "halftime_goals",
    # Common camelCase/acronym and nested scoreline provider aliases.
    "home_team_goals", "away_team_goals", "goals_home_team", "goals_away_team",
    "home_team_score", "away_team_score",
    "home_team_goals_scored", "away_team_goals_scored",
    "home_team_goals_conceded", "away_team_goals_conceded",
    "home_team_score_ft", "away_team_score_ft",
    "ft_score", "ht_score", "score_ft", "score_ht",
    "scoreline", "score_line", "match_score", "game_score",
    "full_time_scoreline", "half_time_scoreline",
    "full_time", "half_time", "fulltime", "halftime",
    "result_code", "result_name", "outcome_code", "outcome_name",
    "ft_result", "ht_result", "final_result", "fulltime_result", "halftime_result",
    "ft_outcome", "ht_outcome", "full_time_outcome", "half_time_outcome",
    "fulltime_outcome", "halftime_outcome", "final_outcome",
    "home_team_result", "away_team_result",
    "winner_name", "winning_team_name", "winner_id", "winning_team_id",
    # Explicit 1X2 winner/side flags are outcomes, not pre-match market quotes.
    "home_win", "away_win", "home_won", "away_won",
    "is_home_winner", "is_away_winner", "home_team_won", "away_team_won",
    "winner_side", "winning_side", "winner_team", "winner_team_id",
    "result_1x2", "outcome_1x2", "match_result_1x2", "match_outcome_1x2",
    "home_result", "away_result", "draw_result", "is_draw", "was_draw", "drawn",
    # Preserve compact Football-Data xG aliases after camelCase tokenization.
    "hx_g", "ax_g", "x_g_home", "x_g_away",
    # Plural score and team-oriented score containers used by common APIs.
    "scores", "scores_home", "scores_away", "home_scores", "away_scores",
    "scores_home_team", "scores_away_team", "score_full_time", "score_half_time",
    "settlement", "prediction_correct", "match_winner", "winner", "winning_team",
    "home_score", "away_score", "full_time_score", "full_time_result",
    "match_result", "match_outcome",
    "home_corners", "away_corners", "corners_home", "corners_away",
    "home_yellows", "away_yellows", "home_reds", "away_reds",
    "home_cards", "away_cards", "home_yellow_cards", "away_yellow_cards",
    "home_red_cards", "away_red_cards",
    "home_points", "away_points", "points_home", "points_away",
    # Football-Data result aliases (full-time and half-time).
    "fthg", "hg", "ftag", "ag", "ftr", "res", "hthg", "htag", "htr",
    # Football-Data post-match statistics; never valid raw capture-time inputs.
    "hxg", "axg", "hs", "as", "hst", "ast", "hhw", "ahw",
    "hf", "af", "hfkc", "afkc", "ho", "ao", "hbp", "abp", "attendance",
    "hc", "ac", "hy", "ay", "hr", "ar",
    # Common descriptive aliases for the same post-match fields.
    "half_time_home_goals", "half_time_away_goals",
    "home_xg", "away_xg", "xg_home", "xg_away",
    "home_shots", "away_shots", "shots_home", "shots_away",
    "home_shots_on_target", "away_shots_on_target",
    "shots_on_target_home", "shots_on_target_away",
    "home_hit_woodwork", "away_hit_woodwork",
    "home_fouls", "away_fouls", "fouls_home", "fouls_away",
    "home_free_kicks_conceded", "away_free_kicks_conceded",
    "home_offsides", "away_offsides", "offsides_home", "offsides_away",
    "home_bookings_points", "away_bookings_points", "crowd_attendance",
    # Generic post-match statistic labels used in typed name/value arrays.
    "corner", "corners", "corner_kicks", "card", "cards", "yellow_card",
    "yellow_cards", "red_card", "red_cards", "shot", "shots",
    "shot_on_target", "shots_on_target", "shots_off_target",
    "foul", "fouls", "offside", "offsides", "possession",
    "expected_goal", "expected_goals", "xg", "free_kick", "free_kicks",
    "save", "saves",
})
OUTCOME_FIELD_DESCRIPTOR_KEYS = frozenset({
    "name", "field", "field_name", "stat", "stat_name", "statistic",
    "statistic_name", "metric", "metric_name", "key", "label",
    "attribute", "property", "code", "slug", "type", "stat_type",
    # Provider schemas also store the statistic identity in abbreviation/code
    # and display-name fields; inspect only these exact descriptor keys.
    "abbr", "abbreviation", "short_name", "short_code",
    "stat_code", "statistic_code", "field_code", "metric_code",
    "attribute_name", "property_name", "display_name",
    # Some provider schemas expose statistic identifiers separately from labels.
    "stat_id", "statistic_id", "field_id", "metric_id",
    "attribute_id", "property_id", "data_key", "stat_key",
    "outcome_key", "result_key",
})
PROBABILITY_FIELDS = (
    ("market_home_probability", "market_draw_probability", "market_away_probability"),
    ("incumbent_home_probability", "incumbent_draw_probability", "incumbent_away_probability"),
    ("candidate_home_probability", "candidate_draw_probability", "candidate_away_probability"),
    ("shadow_residual_home_probability", "shadow_residual_draw_probability", "shadow_residual_away_probability"),
)
REQUIRED_CAPTURE_FIELDS = frozenset(
    {
        "experiment_id",
        "evidence_class",
        "league",
        "event_id",
        "home_team",
        "away_team",
        "kickoff_utc",
        "capture_time_utc",
        "market_snapshot_time_utc",
        "incumbent_generated_at_utc",
        "candidate_generated_at_utc",
        "feature_history_cutoff_utc",
        "candidate_training_data_through_utc",
        "candidate_artifact_sha256",
        "incumbent_model_sha256",
        "code_commit_sha",
        "active_lambda",
        "stability_gate_passed",
    }
    | {name for triple in PROBABILITY_FIELDS for name in triple}
)


def _sha256_json(payload: Mapping) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _as_utc(value: object, field: str) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    if ts.tzinfo is None:
        raise ValueError(f"{field} must be timezone-aware UTC")
    return ts.tz_convert("UTC")


def _canonical_shadow_team_identity(value: str) -> str:
    """Apply the existing Serie A/V2 aliases only for cohort deduplication."""
    stripped = value.strip()
    runtime_name = SERIE_A_RUNTIME_CONFIG.aliases.get(stripped, stripped)
    historical_name = V2_HISTORICAL_TEAM_ALIASES.get(runtime_name, runtime_name)
    return " ".join(historical_name.split()).casefold()


def _is_numeric_scalar(value: object) -> bool:
    return (
        not isinstance(value, (bool, np.bool_))
        and isinstance(value, (int, float, np.integer, np.floating))
    )


def _finite_report_number(value: object, field: str) -> float:
    if not _is_numeric_scalar(value) or not np.isfinite(value):
        raise ValueError(f"{field} must be a finite numeric scalar")
    return float(value)


def _probability_report_number(value: object, field: str) -> float:
    number = _finite_report_number(value, field)
    if not 0.0 <= number <= 1.0:
        raise ValueError(f"{field} must be between 0 and 1")
    return number


def _nonnegative_report_count(value: object, field: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{field} must be a nonnegative integer")
    return value


def _finite_list(values: object, expected: int, field: str) -> list[float]:
    raw = np.asarray(values, dtype=object)
    if raw.shape != (expected,) or not all(_is_numeric_scalar(x) for x in raw.flat):
        raise ValueError(f"{field} must contain {expected} finite numeric values")
    arr = np.asarray(values, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError(f"{field} must contain {expected} finite numeric values")
    return [float(x) for x in arr]


def _finite_matrix(values: object, rows: int, cols: int, field: str) -> list[list[float]]:
    raw = np.asarray(values, dtype=object)
    if raw.shape != (rows, cols) or not all(_is_numeric_scalar(x) for x in raw.flat):
        raise ValueError(f"{field} must be a finite numeric {rows}x{cols} matrix")
    arr = np.asarray(values, dtype=float)
    if not np.isfinite(arr).all():
        raise ValueError(f"{field} must be a finite numeric {rows}x{cols} matrix")
    return [[float(x) for x in row] for row in arr]


def stability_gate(report: Mapping) -> dict:
    """Evaluate the frozen multi-period/uncertainty gate without tuning it."""
    if not isinstance(report, Mapping):
        raise ValueError("robustness report must be a mapping")
    if report.get("experiment_id") != "MARKET_ANCHOR_1X2_V1_ROBUSTNESS":
        raise ValueError("wrong robustness experiment")
    if report.get("target_league") != PRIMARY_LEAGUE:
        raise ValueError("robustness report must target Serie A")
    if report.get("frozen_feature_variant") != FEATURE_VARIANT:
        raise ValueError("robustness feature variant differs from frozen V2 recipe")
    frozen_lambda = _finite_report_number(report.get("frozen_lambda"), "frozen_lambda")
    if frozen_lambda != SHADOW_RESIDUAL_LAMBDA:
        raise ValueError("robustness lambda differs from frozen V2 residual recipe")

    prior_seasons = _nonnegative_report_count(
        report.get("retrospective_prior_seasons"), "retrospective_prior_seasons"
    )
    dual_wins = _nonnegative_report_count(
        report.get("retrospective_prior_season_dual_wins"),
        "retrospective_prior_season_dual_wins",
    )
    if dual_wins > prior_seasons:
        raise ValueError(
            "retrospective_prior_season_dual_wins cannot exceed retrospective_prior_seasons"
        )
    brier = report.get("final_oot_brier_bootstrap")
    log_loss = report.get("final_oot_log_loss_bootstrap")
    if not isinstance(brier, Mapping):
        raise ValueError("final_oot_brier_bootstrap must be a mapping")
    if not isinstance(log_loss, Mapping):
        raise ValueError("final_oot_log_loss_bootstrap must be a mapping")

    brier_ci_high = _finite_report_number(
        brier.get("bootstrap_ci95_high"),
        "final_oot_brier_bootstrap.bootstrap_ci95_high",
    )
    log_loss_ci_high = _finite_report_number(
        log_loss.get("bootstrap_ci95_high"),
        "final_oot_log_loss_bootstrap.bootstrap_ci95_high",
    )
    brier_probability = _probability_report_number(
        brier.get("bootstrap_probability_better_than_market"),
        "final_oot_brier_bootstrap.bootstrap_probability_better_than_market",
    )
    log_loss_probability = _probability_report_number(
        log_loss.get("bootstrap_probability_better_than_market"),
        "final_oot_log_loss_bootstrap.bootstrap_probability_better_than_market",
    )
    checks = {
        "required_prior_seasons": prior_seasons == STABILITY_REQUIRED_PRIOR_SEASONS,
        "min_prior_dual_metric_wins": dual_wins >= STABILITY_MIN_DUAL_WINS,
        "brier_ci95_entirely_better_than_market": brier_ci_high < STABILITY_MAX_CI95_HIGH,
        "log_loss_ci95_entirely_better_than_market": log_loss_ci_high < STABILITY_MAX_CI95_HIGH,
        "brier_probability_better_at_least_95pct": brier_probability >= STABILITY_MIN_PROBABILITY_BETTER,
        "log_loss_probability_better_at_least_95pct": log_loss_probability >= STABILITY_MIN_PROBABILITY_BETTER,
    }
    return {
        "passed": all(checks.values()),
        "checks": checks,
        "observed": {
            "prior_seasons": prior_seasons,
            "prior_dual_metric_wins": dual_wins,
            "brier_ci95_high": brier_ci_high,
            "log_loss_ci95_high": log_loss_ci_high,
            "brier_probability_better_than_market": brier_probability,
            "log_loss_probability_better_than_market": log_loss_probability,
        },
    }


def candidate_recipe() -> dict:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "primary_league": PRIMARY_LEAGUE,
        "feature_variant": FEATURE_VARIANT,
        "features": list(FEATURE_SETS[FEATURE_VARIANT]),
        "shadow_residual_lambda": SHADOW_RESIDUAL_LAMBDA,
        "active_lambda": ACTIVE_LAMBDA,
        "stability_gate_passed": STABILITY_GATE_PASSED,
        "l2_penalty": float(L2_PENALTY),
        "refit_seasons": list(REFIT_SEASONS),
        "training_data_through_utc": TRAINING_DATA_THROUGH.isoformat(),
        "opened_2026_27_outcomes_used": False,
        "research_only": True,
        "automatic_promotion": False,
    }


def _training_fingerprint(frame: pd.DataFrame, features: list[str]) -> str:
    cols = [
        "league", "season", "match_date", "home_team", "away_team", "result",
        "market_home", "market_draw", "market_away", *features,
    ]
    missing = set(cols) - set(frame.columns)
    if missing:
        raise ValueError("training frame missing columns: " + ", ".join(sorted(missing)))
    canonical = frame[cols].copy()
    canonical["match_date"] = pd.to_datetime(canonical["match_date"]).dt.strftime("%Y-%m-%d")
    records = canonical.replace({np.nan: None}).to_dict(orient="records")
    return _sha256_json({"rows": records})


def fit_candidate_artifact(frame: pd.DataFrame) -> dict:
    """Refit the frozen residual recipe on pre-2026/27 Serie A history only."""
    prepared = _prepare(frame)
    prepared = prepared[(prepared["league"] == PRIMARY_LEAGUE) & prepared["season"].isin(REFIT_SEASONS)].copy()
    if prepared.empty:
        raise ValueError("no eligible frozen Serie A training rows")
    if pd.to_datetime(prepared["match_date"]).max() > TRAINING_DATA_THROUGH.tz_localize(None):
        raise ValueError("training data exceeds frozen cutoff")

    features = list(FEATURE_SETS[FEATURE_VARIANT])
    market = _market(prepared)
    y = prepared["result"].map(RESULT_TO_INT).to_numpy()
    if np.isnan(y.astype(float)).any():
        raise ValueError("training outcomes must be known historical labels")
    model = fit_residual_model(prepared[features], y, market, l2_penalty=L2_PENALTY)

    artifact = {
        **candidate_recipe(),
        "training_rows": int(len(prepared)),
        "training_fingerprint_sha256": _training_fingerprint(prepared, features),
        "imputer_medians": _finite_list(model.imputer.statistics_, len(features), "imputer_medians"),
        "scaler_mean": _finite_list(model.scaler.mean_, len(features), "scaler_mean"),
        "scaler_scale": _finite_list(model.scaler.scale_, len(features), "scaler_scale"),
        "weights": _finite_matrix(model.weights, len(features) + 1, 2, "weights"),
    }
    artifact["artifact_sha256"] = _sha256_json(artifact)
    validate_candidate_artifact(artifact)
    return artifact


def validate_candidate_artifact(artifact: Mapping) -> None:
    for field in ("shadow_residual_lambda", "active_lambda", "l2_penalty"):
        value = artifact.get(field)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float, np.integer, np.floating))
            or not np.isfinite(value)
        ):
            raise ValueError(f"{field} must be a finite numeric scalar")
    for field in (
        "stability_gate_passed",
        "opened_2026_27_outcomes_used",
        "research_only",
        "automatic_promotion",
    ):
        if type(artifact.get(field)) is not bool:
            raise ValueError(f"{field} must be a boolean")
    recipe = candidate_recipe()
    for key, expected in recipe.items():
        if artifact.get(key) != expected:
            raise ValueError(f"candidate artifact violates frozen recipe: {key}")
    features = list(recipe["features"])
    _finite_list(artifact.get("imputer_medians"), len(features), "imputer_medians")
    _finite_list(artifact.get("scaler_mean"), len(features), "scaler_mean")
    scale = np.asarray(_finite_list(artifact.get("scaler_scale"), len(features), "scaler_scale"))
    if (scale <= 0).any():
        raise ValueError("scaler_scale must be positive")
    _finite_matrix(artifact.get("weights"), len(features) + 1, 2, "weights")
    training_rows = artifact.get("training_rows")
    if type(training_rows) is not int or training_rows <= 0:
        raise ValueError("training_rows must be a positive integer")
    for field in ("training_fingerprint_sha256", "artifact_sha256"):
        value = artifact.get(field)
        if not isinstance(value, str) or len(value) != 64 or any(
            c not in "0123456789abcdef" for c in value
        ):
            raise ValueError(f"{field} must be a lowercase sha256 string")
    body = dict(artifact)
    supplied = body.pop("artifact_sha256")
    if _sha256_json(body) != supplied:
        raise ValueError("candidate artifact sha256 mismatch")


def _artifact_residual_logits(features: pd.DataFrame, artifact: Mapping) -> np.ndarray:
    validate_candidate_artifact(artifact)
    names = list(artifact["features"])
    if list(features.columns) != names:
        raise ValueError("feature columns must exactly match frozen feature order")
    x = features.to_numpy(dtype=float)
    medians = np.asarray(artifact["imputer_medians"], dtype=float)
    missing = np.isnan(x)
    if missing.any():
        x = x.copy()
        x[missing] = np.take(medians, np.where(missing)[1])
    if not np.isfinite(x).all():
        raise ValueError("candidate features must be finite after imputation")
    x = (x - np.asarray(artifact["scaler_mean"], dtype=float)) / np.asarray(artifact["scaler_scale"], dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    pair = x @ np.asarray(artifact["weights"], dtype=float)
    return np.column_stack([pair[:, 0], np.zeros(len(x)), pair[:, 1]])


def predict_shadow_residual(market_probabilities: np.ndarray, features: pd.DataFrame, artifact: Mapping) -> np.ndarray:
    residual = _artifact_residual_logits(features, artifact)
    return market_anchored_probabilities(
        validate_probabilities(market_probabilities), residual, SHADOW_RESIDUAL_LAMBDA
    )


def predict_candidate(market_probabilities: np.ndarray, features: pd.DataFrame, artifact: Mapping) -> np.ndarray:
    """Return active V2 probabilities; currently exact market because the gate failed."""
    residual = _artifact_residual_logits(features, artifact)
    return market_anchored_probabilities(validate_probabilities(market_probabilities), residual, ACTIVE_LAMBDA)


def write_candidate_artifact(frame: pd.DataFrame, output: Path) -> dict:
    artifact = fit_candidate_artifact(frame)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


COMPACT_FORBIDDEN_OUTCOME_FIELDS = frozenset(
    name.replace("_", "") for name in FORBIDDEN_OUTCOME_FIELDS
)


def normalize_outcome_field_name(key: str) -> str:
    """Canonicalize provider key spelling before the recursive outcome embargo.

    Handles snake/kebab/space/dot separators, camelCase and acronym boundaries
    (for example homeTeamGoals, FTScore and score.line) without changing any
    frozen derived feature names such as diff_goals_for_5.
    """
    if not isinstance(key, str):
        return ""
    value = key.strip()
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", value)
    value = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", value)
    value = re.sub(r"[^A-Za-z0-9]+", "_", value)
    return value.strip("_").lower()


def is_forbidden_outcome_field(key: str) -> bool:
    """Match outcome aliases even when acronym letters are punctuation-separated.

    The readable normalizer preserves separators as underscores (e.g. F.T.H.G
    -> f_t_h_g). Compare a second compact form against the same frozen alias
    set so punctuation cannot split a protected provider abbreviation.
    """
    normalized = normalize_outcome_field_name(key)
    return bool(
        normalized
        and (
            normalized in FORBIDDEN_OUTCOME_FIELDS
            or normalized.replace("_", "") in COMPACT_FORBIDDEN_OUTCOME_FIELDS
        )
    )


def forbidden_outcome_field_match(key: str, value=None) -> str | None:
    """Return an exact forbidden field name, including typed stat descriptors.

    Some providers encode statistics as arrays of records such as
    {"name": "FTR", "value": "H"} or {"type": "Full Time Result", ...}.
    The descriptor is a field name stored as a value, not a mapping key. Match
    only exact normalized descriptor values; do not scan arbitrary free text or
    substrings, so labels such as "Home Win Probability" remain admissible.
    """
    if is_forbidden_outcome_field(key):
        return normalize_outcome_field_name(key)
    if normalize_outcome_field_name(key) not in OUTCOME_FIELD_DESCRIPTOR_KEYS:
        return None
    candidates = value if isinstance(value, (list, tuple)) else (value,)
    for candidate in candidates:
        if isinstance(candidate, str) and is_forbidden_outcome_field(candidate):
            return normalize_outcome_field_name(candidate)
    return None


def _nested_forbidden_outcome_keys(value) -> set[str]:
    """Return protected match-outcome keys found anywhere in nested containers."""
    pending = [value]
    seen: set[int] = set()
    leaked: set[str] = set()
    while pending:
        current = pending.pop()
        if isinstance(current, Mapping):
            identity = id(current)
            if identity in seen:
                continue
            seen.add(identity)
            for key, nested in current.items():
                if isinstance(key, str):
                    matched = forbidden_outcome_field_match(key, nested)
                    if matched:
                        leaked.add(matched)
                pending.append(nested)
        elif isinstance(current, (list, tuple)):
            identity = id(current)
            if identity in seen:
                continue
            seen.add(identity)
            pending.extend(current)
    return leaked



def validate_shadow_capture_rows(rows: Iterable[Mapping]) -> list[dict]:
    validated: list[dict] = []
    seen_events: set[str] = set()
    seen_fixtures: set[tuple[str, str, tuple[str, str]]] = set()
    candidate_artifacts: set[str] = set()
    for raw in rows:
        row = dict(raw)
        missing = REQUIRED_CAPTURE_FIELDS - row.keys()
        if missing:
            raise ValueError("shadow row missing fields: " + ", ".join(sorted(missing)))
        leaked = _nested_forbidden_outcome_keys(raw)
        if leaked:
            raise ValueError("outcome fields are forbidden in shadow capture: " + ", ".join(sorted(leaked)))
        if row["experiment_id"] != EXPERIMENT_ID or row["evidence_class"] != EVIDENCE_CLASS:
            raise ValueError("wrong experiment identity")
        if row["league"] != PRIMARY_LEAGUE:
            raise ValueError("only Serie A counts as the V2 primary cohort")
        stability_value = row["stability_gate_passed"]
        if type(stability_value) is not bool:
            raise ValueError("stability_gate_passed must be a boolean")
        if stability_value is not STABILITY_GATE_PASSED:
            raise ValueError("shadow row stability gate state differs from frozen contract")
        active_lambda = row["active_lambda"]
        if not _is_numeric_scalar(active_lambda) or not np.isfinite(active_lambda):
            raise ValueError("active_lambda must be a finite numeric scalar")
        if float(active_lambda) != ACTIVE_LAMBDA:
            raise ValueError("shadow row active lambda differs from frozen contract")
        event_value = row["event_id"]
        if not isinstance(event_value, str):
            raise ValueError("event_id must be a string")
        event_id = event_value.strip()
        if not event_id or event_value != event_id or event_id in seen_events:
            raise ValueError("event_id must be a non-empty canonical string and unique")
        seen_events.add(event_id)

        home_team = row["home_team"]
        away_team = row["away_team"]
        if type(home_team) is not str or not home_team or home_team != home_team.strip():
            raise ValueError("home_team must be a non-empty canonical string")
        if type(away_team) is not str or not away_team or away_team != away_team.strip():
            raise ValueError("away_team must be a non-empty canonical string")
        home_identity = _canonical_shadow_team_identity(home_team)
        away_identity = _canonical_shadow_team_identity(away_team)
        if home_identity == away_identity:
            raise ValueError("home_team and away_team must identify distinct teams")

        kickoff = _as_utc(row["kickoff_utc"], "kickoff_utc")
        # Provider event IDs are not a sufficient unit for the 30-event gate:
        # the same Serie A fixture can be duplicated under different IDs or
        # reversed home/away labels. Deduplicate by canonical teams and local
        # fixture date, without changing any frozen feature or model input.
        fixture_day = kickoff.tz_convert(SERIE_A_RUNTIME_CONFIG.identity.timezone).date().isoformat()
        fixture_identity = (
            PRIMARY_LEAGUE,
            fixture_day,
            tuple(sorted((home_identity, away_identity))),
        )
        if fixture_identity in seen_fixtures:
            raise ValueError("duplicate canonical primary fixture identity")
        seen_fixtures.add(fixture_identity)
        capture = _as_utc(row["capture_time_utc"], "capture_time_utc")
        market_time = _as_utc(row["market_snapshot_time_utc"], "market_snapshot_time_utc")
        incumbent_time = _as_utc(row["incumbent_generated_at_utc"], "incumbent_generated_at_utc")
        candidate_time = _as_utc(row["candidate_generated_at_utc"], "candidate_generated_at_utc")
        feature_cutoff = _as_utc(row["feature_history_cutoff_utc"], "feature_history_cutoff_utc")
        training_cutoff = _as_utc(row["candidate_training_data_through_utc"], "candidate_training_data_through_utc")

        if kickoff < ADMISSION_NOT_BEFORE or capture < ADMISSION_NOT_BEFORE:
            raise ValueError("retroactive/backfilled rows are forbidden")
        if min(market_time, incumbent_time, candidate_time) < ADMISSION_NOT_BEFORE:
            raise ValueError("retroactive/backfilled prediction inputs are forbidden")
        if not (feature_cutoff < market_time < kickoff):
            raise ValueError("feature history cutoff must be strictly before market snapshot and capture pre-kickoff")
        if not (
            market_time < incumbent_time < capture < kickoff
            and market_time < candidate_time < capture < kickoff
        ):
            raise ValueError("market snapshot must precede both model predictions; both predictions must strictly precede capture pre-kickoff")
        if training_cutoff != TRAINING_DATA_THROUGH:
            raise ValueError("candidate training cutoff differs from frozen contract")

        validated_probabilities = []
        for triple in PROBABILITY_FIELDS:
            raw_values = [row[name] for name in triple]
            if not all(_is_numeric_scalar(value) for value in raw_values):
                raise ValueError(
                    f"{triple[0]} probability values must be finite numeric scalars"
                )
            validated_probabilities.append(
                validate_probabilities(np.asarray([raw_values], dtype=float))[0]
            )
        market_p, _, active_p, _ = validated_probabilities
        if not np.allclose(active_p, market_p, atol=1e-12, rtol=0.0):
            raise ValueError("active V2 candidate must equal market while stability gate is closed")
        incumbent_sha = row["incumbent_model_sha256"]
        if not isinstance(incumbent_sha, str) or incumbent_sha != INCUMBENT_MODEL_SHA256:
            raise ValueError("incumbent model sha differs from frozen production comparator")
        for field in ("candidate_artifact_sha256", "code_commit_sha"):
            value = row[field]
            expected = 64 if field.endswith("sha256") else 40
            if (
                not isinstance(value, str)
                or len(value) != expected
                or any(c not in "0123456789abcdef" for c in value)
            ):
                raise ValueError(f"invalid {field}")
        candidate_artifacts.add(row["candidate_artifact_sha256"])
        validated.append(row)
    if len(candidate_artifacts) > 1:
        raise ValueError("one shadow capture batch cannot mix candidate artifacts")
    if candidate_artifacts and candidate_artifacts != {FROZEN_CANDIDATE_ARTIFACT_SHA256}:
        raise ValueError("candidate_artifact_sha256 differs from frozen V2 candidate")
    return validated


def outcome_read_permitted(completed_primary_events: int) -> bool:
    """Open the frozen outcome-read gate only from an exact integer event count."""
    if isinstance(completed_primary_events, (bool, np.bool_)) or not isinstance(
        completed_primary_events, (int, np.integer)
    ):
        raise ValueError("completed_primary_events must be a nonnegative integer")
    if completed_primary_events < 0:
        raise ValueError("completed_primary_events must be a nonnegative integer")
    return int(completed_primary_events) >= FIRST_OUTCOME_READ_GATE
