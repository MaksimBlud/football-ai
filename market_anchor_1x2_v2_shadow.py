"""Frozen prospective-shadow contract for MARKET_ANCHOR_1X2_V2.

Research only. The candidate recipe is inherited from MARKET_ANCHOR_1X2_V1 and
must never be re-selected using opened 2026-27 outcomes. The only primary cohort
is Serie A. Shadow rows are outcome-free and must be captured strictly before
kickoff. This module never reads, writes, trains, or promotes production .pkl
artifacts.
"""
from __future__ import annotations

import hashlib
import json
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

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V2"
EVIDENCE_CLASS = "PROSPECTIVE_SHADOW"
SOURCE_EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1"
PRIMARY_LEAGUE = "SERIE_A"
FEATURE_VARIANT = "ALL_FOOTBALL"
LAMBDA = 1.0
REFIT_SEASONS = tuple(f"{y}-{y+1}" for y in range(2016, 2026))
TRAINING_DATA_THROUGH = pd.Timestamp("2026-06-30T23:59:59Z")
ADMISSION_NOT_BEFORE = pd.Timestamp("2026-09-16T00:00:00Z")
FIRST_OUTCOME_READ_GATE = 30
INCUMBENT_MODEL_SHA256 = "1e516fe91420fdc2d6479e9fb92b005c4a0c75c7f0f217493dd6b27fd64d99a5"
FORBIDDEN_OUTCOME_FIELDS = frozenset(
    {"result", "outcome", "home_goals", "away_goals", "score", "final_score"}
)
PROBABILITY_FIELDS = (
    ("market_home_probability", "market_draw_probability", "market_away_probability"),
    ("incumbent_home_probability", "incumbent_draw_probability", "incumbent_away_probability"),
    ("candidate_home_probability", "candidate_draw_probability", "candidate_away_probability"),
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


def _finite_list(values: object, expected: int, field: str) -> list[float]:
    arr = np.asarray(values, dtype=float)
    if arr.shape != (expected,) or not np.isfinite(arr).all():
        raise ValueError(f"{field} must contain {expected} finite values")
    return [float(x) for x in arr]


def _finite_matrix(values: object, rows: int, cols: int, field: str) -> list[list[float]]:
    arr = np.asarray(values, dtype=float)
    if arr.shape != (rows, cols) or not np.isfinite(arr).all():
        raise ValueError(f"{field} must be a finite {rows}x{cols} matrix")
    return [[float(x) for x in row] for row in arr]


def candidate_recipe() -> dict:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "source_experiment_id": SOURCE_EXPERIMENT_ID,
        "primary_league": PRIMARY_LEAGUE,
        "feature_variant": FEATURE_VARIANT,
        "features": list(FEATURE_SETS[FEATURE_VARIANT]),
        "lambda": LAMBDA,
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
    """Refit the already-selected V1 recipe on frozen pre-2026/27 Serie A history."""
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
    if int(artifact.get("training_rows", 0)) <= 0:
        raise ValueError("training_rows must be positive")
    for field in ("training_fingerprint_sha256", "artifact_sha256"):
        value = str(artifact.get(field, ""))
        if len(value) != 64 or any(c not in "0123456789abcdef" for c in value):
            raise ValueError(f"{field} must be lowercase sha256")
    body = dict(artifact)
    supplied = body.pop("artifact_sha256")
    if _sha256_json(body) != supplied:
        raise ValueError("candidate artifact sha256 mismatch")


def predict_candidate(market_probabilities: np.ndarray, features: pd.DataFrame, artifact: Mapping) -> np.ndarray:
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
    residual = np.column_stack([pair[:, 0], np.zeros(len(x)), pair[:, 1]])
    return market_anchored_probabilities(validate_probabilities(market_probabilities), residual, LAMBDA)


def write_candidate_artifact(frame: pd.DataFrame, output: Path) -> dict:
    artifact = fit_candidate_artifact(frame)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return artifact


def validate_shadow_capture_rows(rows: Iterable[Mapping]) -> list[dict]:
    validated: list[dict] = []
    seen_events: set[str] = set()
    for raw in rows:
        row = dict(raw)
        missing = REQUIRED_CAPTURE_FIELDS - row.keys()
        if missing:
            raise ValueError("shadow row missing fields: " + ", ".join(sorted(missing)))
        leaked = FORBIDDEN_OUTCOME_FIELDS & row.keys()
        if leaked:
            raise ValueError("outcome fields are forbidden in shadow capture: " + ", ".join(sorted(leaked)))
        if row["experiment_id"] != EXPERIMENT_ID or row["evidence_class"] != EVIDENCE_CLASS:
            raise ValueError("wrong experiment identity")
        if row["league"] != PRIMARY_LEAGUE:
            raise ValueError("only Serie A counts as the V2 primary cohort")
        event_id = str(row["event_id"]).strip()
        if not event_id or event_id in seen_events:
            raise ValueError("event_id must be non-empty and unique")
        seen_events.add(event_id)

        kickoff = _as_utc(row["kickoff_utc"], "kickoff_utc")
        capture = _as_utc(row["capture_time_utc"], "capture_time_utc")
        market_time = _as_utc(row["market_snapshot_time_utc"], "market_snapshot_time_utc")
        incumbent_time = _as_utc(row["incumbent_generated_at_utc"], "incumbent_generated_at_utc")
        candidate_time = _as_utc(row["candidate_generated_at_utc"], "candidate_generated_at_utc")
        feature_cutoff = _as_utc(row["feature_history_cutoff_utc"], "feature_history_cutoff_utc")
        training_cutoff = _as_utc(row["candidate_training_data_through_utc"], "candidate_training_data_through_utc")

        if kickoff < ADMISSION_NOT_BEFORE or capture < ADMISSION_NOT_BEFORE:
            raise ValueError("retroactive/backfilled rows are forbidden")
        if not (market_time <= capture < kickoff):
            raise ValueError("market and capture timestamps must be pre-kickoff")
        if not (incumbent_time <= capture < kickoff and candidate_time <= capture < kickoff):
            raise ValueError("both model predictions must exist pre-kickoff")
        if not (feature_cutoff <= capture and feature_cutoff < kickoff):
            raise ValueError("feature history cutoff must be pre-capture and pre-kickoff")
        if training_cutoff != TRAINING_DATA_THROUGH:
            raise ValueError("candidate training cutoff differs from frozen contract")

        for triple in PROBABILITY_FIELDS:
            validate_probabilities(np.asarray([[float(row[name]) for name in triple]], dtype=float))
        if str(row["incumbent_model_sha256"]) != INCUMBENT_MODEL_SHA256:
            raise ValueError("incumbent model sha differs from frozen production comparator")
        for field in ("candidate_artifact_sha256", "code_commit_sha"):
            value = str(row[field])
            expected = 64 if field.endswith("sha256") else 40
            if len(value) != expected or any(c not in "0123456789abcdef" for c in value):
                raise ValueError(f"invalid {field}")
        validated.append(row)
    return validated


def outcome_read_permitted(completed_primary_events: int) -> bool:
    if completed_primary_events < 0:
        raise ValueError("completed_primary_events cannot be negative")
    return completed_primary_events >= FIRST_OUTCOME_READ_GATE
