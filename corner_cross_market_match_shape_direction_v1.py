"""Frozen falsification audit for the corner match-shape direction signal."""
from __future__ import annotations

import hashlib
import io
import os
import zipfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

EXPERIMENT_ID = "CORNER_CROSS_MARKET_MATCH_SHAPE_DIRECTION_V1"
ARTIFACT_ID = 11294063833
ARTIFACT_SHA256 = "92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0"
ARTIFACT_MEMBER = "cross_market_shape_rows.csv"
ARTIFACT_URL = f"https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/{ARTIFACT_ID}/zip"
EXPECTED_ROWS = 117
EXPECTED_COHORTS = {"V1_55", "REP50", "V1_46", "V2B_43"}
EXPECTED_LEAGUES = {"EPL", "LA_LIGA", "SERIE_A"}
PERMUTATION_DRAWS = 10_000
SEED = 20261005
REQUIRED_COLUMNS = {"fixture_id", "cohort", "league", "opening_lambda", "centre_delta", "match_shape_gap"}


def _safety() -> dict[str, Any]:
    return {
        "research_only": True, "no_bet": True,
        "new_prospective_rows_collected": 0, "paid_odds_api_calls": 0,
        "supabase_writes": 0, "production_model_operations": 0,
        "production_promotion": False, "frozen_sign_changed": False,
        "threshold_search_used": False,
    }


def _source_gap(reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "decision": "BLOCKED_BY_EXISTING_SOURCE_GAP",
        "binary_direction_status": "NOT_EVALUATED",
        "continuous_ranking_status": "NOT_EVALUATED",
        "source_gap": reason, "artifact_id": ARTIFACT_ID,
        "artifact_sha256": ARTIFACT_SHA256, "rows": 0,
        "nonzero_movement_rows": 0,
        "falsification": {"residual_spearman_nonzero": None, "residual_spearman_all_rows": None, "permutation_p": None},
        "leave_one_cohort_out": {}, "leave_one_league_out": {},
        "safety": _safety(),
        "interpretation_guard": "The frozen authoritative artifact could not be verified; no proxy or newly collected sample was substituted.",
    }


def _artifact_bytes() -> bytes:
    local = os.environ.get("CORNER_SIX_SIGNAL_ARTIFACT_PATH", "").strip()
    if local:
        payload = Path(local).read_bytes()
    else:
        token = os.environ.get("GH_TOKEN", "").strip()
        if not token:
            raise RuntimeError("GH_TOKEN is required to read the pinned Actions artifact")
        response = requests.get(
            ARTIFACT_URL,
            headers={"Accept": "application/vnd.github+json", "Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.content
    observed = hashlib.sha256(payload).hexdigest()
    if observed != ARTIFACT_SHA256:
        raise RuntimeError(f"pinned artifact digest mismatch: expected {ARTIFACT_SHA256}, got {observed}")
    return payload


def _load_rows(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if ARTIFACT_MEMBER not in archive.namelist():
            raise RuntimeError(f"pinned artifact is missing {ARTIFACT_MEMBER}")
        frame = pd.read_csv(archive.open(ARTIFACT_MEMBER))
    missing = sorted(REQUIRED_COLUMNS - set(frame.columns))
    if missing:
        raise RuntimeError(f"pinned artifact is missing columns: {missing}")
    if len(frame) != EXPECTED_ROWS or frame["fixture_id"].nunique() != EXPECTED_ROWS:
        raise RuntimeError("pinned artifact does not contain exactly 117 unique fixtures")
    if set(frame["cohort"].astype(str)) != EXPECTED_COHORTS:
        raise RuntimeError("pinned artifact cohort identity mismatch")
    if set(frame["league"].astype(str)) != EXPECTED_LEAGUES:
        raise RuntimeError("pinned artifact league identity mismatch")
    for column in ("opening_lambda", "centre_delta", "match_shape_gap"):
        values = pd.to_numeric(frame[column], errors="coerce")
        if values.isna().any() or not np.isfinite(values).all():
            raise RuntimeError(f"pinned artifact has invalid {column}")
        frame[column] = values.astype(float)
    return frame.sort_values("fixture_id", kind="stable").reset_index(drop=True)


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or np.isclose(np.std(left), 0.0) or np.isclose(np.std(right), 0.0):
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def _spearman(left: np.ndarray, right: np.ndarray) -> float:
    return _pearson(pd.Series(left).rank(method="average").to_numpy(float), pd.Series(right).rank(method="average").to_numpy(float))


def _design(frame: pd.DataFrame) -> np.ndarray:
    fixed = pd.get_dummies(frame[["cohort", "league"]].astype(str), drop_first=True, dtype=float)
    return np.column_stack([np.ones(len(frame)), frame["opening_lambda"].to_numpy(float), fixed.to_numpy()])


def _residuals(frame: pd.DataFrame, column: str) -> np.ndarray:
    design = _design(frame)
    values = frame[column].to_numpy(float)
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


def _residual_spearman(frame: pd.DataFrame) -> float:
    return _spearman(_residuals(frame, "match_shape_gap"), _residuals(frame, "centre_delta"))


def _stratified_permutation(frame: pd.DataFrame) -> dict[str, Any]:
    observed = _residual_spearman(frame)
    score_residual = _residuals(frame, "match_shape_gap")
    design = _design(frame)
    target = frame["centre_delta"].to_numpy(float)
    groups = [np.asarray(indices, dtype=int) for indices in frame.groupby(["cohort", "league"], sort=True).indices.values()]
    rng = np.random.default_rng(SEED)
    at_least_observed = 0
    for _ in range(PERMUTATION_DRAWS):
        permuted = target.copy()
        for indices in groups:
            permuted[indices] = rng.permutation(permuted[indices])
        target_residual = permuted - design @ np.linalg.lstsq(design, permuted, rcond=None)[0]
        at_least_observed += int(_spearman(score_residual, target_residual) >= observed - 1e-15)
    return {"draws": PERMUTATION_DRAWS, "seed": SEED, "one_sided_p": (at_least_observed + 1) / (PERMUTATION_DRAWS + 1)}


def _binary_metrics(frame: pd.DataFrame) -> dict[str, Any]:
    nonzero = frame.loc[~np.isclose(frame["centre_delta"], 0.0, atol=1e-12)].copy()
    actual_up = nonzero["centre_delta"].to_numpy(float) > 0
    predicted_up = nonzero["match_shape_gap"].to_numpy(float) > 0
    up_recall = float(np.mean(predicted_up[actual_up]))
    down_recall = float(np.mean(~predicted_up[~actual_up]))
    return {
        "rows": int(len(nonzero)), "up_rows": int(actual_up.sum()), "down_rows": int((~actual_up).sum()),
        "raw_accuracy": float(np.mean(predicted_up == actual_up)), "always_up_accuracy": float(np.mean(actual_up)),
        "balanced_accuracy": (up_recall + down_recall) / 2.0, "up_recall": up_recall, "down_recall": down_recall,
    }


def _leave_one_out(frame: pd.DataFrame, column: str) -> dict[str, float]:
    return {str(value): _residual_spearman(frame.loc[frame[column] != value].reset_index(drop=True)) for value in sorted(frame[column].unique())}


def evaluate() -> dict[str, Any]:
    try:
        frame = _load_rows(_artifact_bytes())
    except (
        OSError,
        RuntimeError,
        ValueError,
        KeyError,
        zipfile.BadZipFile,
        requests.RequestException,
        pd.errors.ParserError,
    ) as error:
        return _source_gap(str(error))
    nonzero = frame.loc[~np.isclose(frame["centre_delta"], 0.0, atol=1e-12)].reset_index(drop=True)
    binary = _binary_metrics(frame)
    residual_nonzero = _residual_spearman(nonzero)
    residual_all = _residual_spearman(frame)
    permutation = _stratified_permutation(nonzero)
    leave_cohort = _leave_one_out(nonzero, "cohort")
    leave_league = _leave_one_out(nonzero, "league")
    robust = residual_nonzero > 0 and residual_all > 0 and permutation["one_sided_p"] <= 0.05 and all(v > 0 for v in leave_cohort.values()) and all(v > 0 for v in leave_league.values())
    decision = "SUPPORTED_FOR_FUTURE_CONFIRMATION" if robust else "WEAK_OR_INCONSISTENT_CROSS_MARKET_CORNER_DIRECTION_HYPOTHESIS"
    return {
        "experiment_id": EXPERIMENT_ID, "decision": decision,
        "artifact_id": ARTIFACT_ID, "artifact_sha256": ARTIFACT_SHA256,
        "rows": int(len(frame)), "nonzero_movement_rows": int(len(nonzero)),
        "binary_direction_status": "WEAK_BELOW_ALWAYS_UP_WITH_DOWN_SCARCITY" if binary["raw_accuracy"] <= binary["always_up_accuracy"] else "ABOVE_ALWAYS_UP_DIAGNOSTIC_ONLY",
        "continuous_ranking_status": "ROBUST_WITHIN_OPENED_SAMPLE_REQUIRES_UNTOUCHED_CONFIRMATION" if robust else "NOT_ROBUST_AFTER_FALSIFICATION",
        "binary_direction": binary,
        "raw_continuous": {
            "pearson_nonzero": _pearson(nonzero["match_shape_gap"].to_numpy(float), nonzero["centre_delta"].to_numpy(float)),
            "spearman_nonzero": _spearman(nonzero["match_shape_gap"].to_numpy(float), nonzero["centre_delta"].to_numpy(float)),
            "spearman_all_rows": _spearman(frame["match_shape_gap"].to_numpy(float), frame["centre_delta"].to_numpy(float)),
        },
        "falsification": {
            "mechanical_opening_component_pearson_nonzero": _pearson(-nonzero["opening_lambda"].to_numpy(float), nonzero["centre_delta"].to_numpy(float)),
            "residual_pearson_nonzero": _pearson(_residuals(nonzero, "match_shape_gap"), _residuals(nonzero, "centre_delta")),
            "residual_spearman_nonzero": residual_nonzero, "residual_spearman_all_rows": residual_all,
            "permutation_p": permutation["one_sided_p"], "permutation": permutation,
        },
        "leave_one_cohort_out": leave_cohort, "leave_one_league_out": leave_league,
        "safety": _safety(),
        "interpretation_guard": "The same already-opened sample was used for falsification, not independent confirmation. Binary direction remains weaker than always-UP and DOWN has only 11 rows. A positive result supports only a future untouched confirmation; it is not a betting edge and NO_BET remains binding.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
