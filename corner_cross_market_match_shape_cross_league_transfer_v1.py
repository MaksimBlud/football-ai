"""Frozen Bundesliga/Ligue 1 transport of the corner match-shape gap.

Research-only.  The movement target is read only after the immutable source and
same-fixture Football-Data join have passed the preregistered coverage audit.
"""
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

from corner_six_signal_screen_v1 import (
    HIST_CODES,
    MARKET_FEATURES,
    _historical_market_training_rows,
    _join_current_row,
    _market_feature_row,
    _ridge_model,
)
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get


EXPERIMENT_ID = "CORNER_CROSS_MARKET_MATCH_SHAPE_CROSS_LEAGUE_TRANSFER_V1"
ARTIFACT_ID = 11294063833
ARTIFACT_SHA256 = "92b958e6f5f8c911236f5e6451ed2f974d4e02af727637644dc2ad037cd78aa0"
ARTIFACT_MEMBER = "corner_rows.csv"
ARTIFACT_URL = f"https://api.github.com/repos/MaksimBlud/football-ai/actions/artifacts/{ARTIFACT_ID}/zip"
LEAGUES = ("BUNDESLIGA", "LIGUE_1")
COMP = {"BUNDESLIGA": "D1", "LIGUE_1": "F1"}
EXPECTED_SOURCE_ROWS = {"BUNDESLIGA": 35, "LIGUE_1": 39}
EXPECTED_COHORTS = {"V1_55", "REP50", "V1_46", "V2B_43"}
CURRENT_SEASON = "2026-2027"
CURRENT_CODE = "2627"
PERMUTATION_DRAWS = 10_000
SEED = 20261005
CONTRACT_COLUMNS = {
    "fixture_id", "cohort", "league", "match_date", "home_team", "away_team",
    "opening_lambda",
}
TARGET_COLUMNS = {"fixture_id", "closing_lambda", "centre_delta"}


def _safety() -> dict[str, Any]:
    return {
        "research_only": True,
        "no_bet": True,
        "new_prospective_rows_collected": 0,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "production_promotion": False,
        "frozen_sign_changed": False,
        "threshold_search_used": False,
        "movement_target_read_before_coverage_gate": False,
    }


def _source_gap(reason: str, *, audit: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "decision": "BLOCKED_BY_EXISTING_SOURCE_GAP",
        "source_gap": reason,
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": ARTIFACT_SHA256,
        "coverage_audit": audit or {"passed": False},
        "rows": 0,
        "nonzero_movement_rows": 0,
        "binary_direction_status": "NOT_EVALUATED",
        "continuous_ranking_status": "NOT_EVALUATED",
        "safety": _safety(),
        "interpretation_guard": "The outcome-free source gate failed; movement targets were not loaded and no proxy was substituted.",
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
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=60,
        )
        response.raise_for_status()
        payload = response.content
    observed = hashlib.sha256(payload).hexdigest()
    if observed != ARTIFACT_SHA256:
        raise RuntimeError(f"pinned artifact digest mismatch: expected {ARTIFACT_SHA256}, got {observed}")
    return payload


def _read_artifact(payload: bytes, *, target: bool) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        if ARTIFACT_MEMBER not in archive.namelist():
            raise RuntimeError(f"pinned artifact is missing {ARTIFACT_MEMBER}")
        wanted = TARGET_COLUMNS | {"fixture_id"} if target else CONTRACT_COLUMNS
        frame = pd.read_csv(archive.open(ARTIFACT_MEMBER), usecols=lambda value: value in wanted)
    missing = sorted(wanted - set(frame.columns))
    if missing:
        raise RuntimeError(f"pinned artifact is missing columns: {missing}")
    if target:
        return frame
    frame = frame.loc[frame["league"].astype(str).isin(LEAGUES)].copy()
    counts = frame.groupby("league").size().to_dict()
    if counts != EXPECTED_SOURCE_ROWS:
        raise RuntimeError(f"cross-league source identity mismatch: {counts}")
    if frame["fixture_id"].astype(str).nunique() != sum(EXPECTED_SOURCE_ROWS.values()):
        raise RuntimeError("cross-league source fixture IDs are not unique")
    if set(frame["cohort"].astype(str)) != EXPECTED_COHORTS:
        raise RuntimeError("cross-league source cohort identity mismatch")
    frame["fixture_id"] = frame["fixture_id"].astype(str)
    frame["match_date"] = pd.to_datetime(frame["match_date"], errors="raise").dt.normalize()
    frame["opening_lambda"] = pd.to_numeric(frame["opening_lambda"], errors="raise")
    return frame.sort_values("fixture_id", kind="stable").reset_index(drop=True)


def _get_csv(url: str) -> pd.DataFrame:
    response = _official_or_pinned_mirror_get(url, timeout=60)
    return pd.read_csv(io.BytesIO(response.content))


def _download_football_data() -> dict[str, pd.DataFrame]:
    result: dict[str, pd.DataFrame] = {}
    for league in LEAGUES:
        frames = []
        for season, code in HIST_CODES.items():
            frame = _get_csv(f"https://www.football-data.co.uk/mmz4281/{code}/{COMP[league]}.csv")
            frame["season"] = season
            frames.append(frame)
        current = _get_csv(f"https://www.football-data.co.uk/mmz4281/{CURRENT_CODE}/{COMP[league]}.csv")
        current["season"] = CURRENT_SEASON
        frames.append(current)
        combined = pd.concat(frames, ignore_index=True)
        combined["match_date"] = pd.to_datetime(combined["Date"], dayfirst=True, errors="coerce").dt.normalize()
        result[league] = combined
    return result


def _prepare_without_target(
    contract: pd.DataFrame,
    football_data: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    validation: dict[str, Any] = {}
    for league in LEAGUES:
        raw = football_data[league]
        train = _historical_market_training_rows(raw, allowed_seasons=set(HIST_CODES) - {"2025-2026"})
        valid = _historical_market_training_rows(raw, allowed_seasons={"2025-2026"})
        if len(train) < 200 or len(valid) < 50:
            raise RuntimeError(f"{league}: insufficient frozen historical rows train={len(train)} validation={len(valid)}")
        model = _ridge_model()
        model.fit(train[list(MARKET_FEATURES)], train["total_corners"])
        pred = model.predict(valid[list(MARKET_FEATURES)])
        baseline = np.full(len(valid), float(train["total_corners"].mean()))
        validation[league] = {
            "train_rows": int(len(train)),
            "validation_rows": int(len(valid)),
            "mae_match_shape_model": float(np.mean(np.abs(valid["total_corners"].to_numpy(float) - pred))),
            "mae_league_mean_baseline": float(np.mean(np.abs(valid["total_corners"].to_numpy(float) - baseline))),
        }
        full = _historical_market_training_rows(raw, allowed_seasons=set(HIST_CODES))
        full_model = _ridge_model()
        full_model.fit(full[list(MARKET_FEATURES)], full["total_corners"])
        current = raw.loc[raw["season"].astype(str) == CURRENT_SEASON]
        for _, fixture in contract.loc[contract["league"] == league].iterrows():
            source = _join_current_row(fixture, current)
            if source is None:
                continue
            features = _market_feature_row(source)
            if features is None:
                continue
            expected = float(full_model.predict(pd.DataFrame([features], columns=MARKET_FEATURES))[0])
            rows.append({
                **fixture.to_dict(),
                "match_shape_expected_corners": expected,
                "match_shape_gap": expected - float(fixture["opening_lambda"]),
            })
    prepared = pd.DataFrame(rows)
    joined = prepared.groupby("league").size().to_dict() if not prepared.empty else {}
    audit = {
        "passed": joined == EXPECTED_SOURCE_ROWS,
        "expected_rows_by_league": EXPECTED_SOURCE_ROWS,
        "joined_rows_by_league": {league: int(joined.get(league, 0)) for league in LEAGUES},
        "exact_same_fixture_join_required": True,
        "movement_target_loaded": False,
        "historical_validation": validation,
    }
    return prepared, audit


def _pearson(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3 or np.isclose(np.std(left), 0) or np.isclose(np.std(right), 0):
        return float("nan")
    return float(np.corrcoef(left, right)[0, 1])


def _spearman(left: np.ndarray, right: np.ndarray) -> float:
    return _pearson(pd.Series(left).rank(method="average").to_numpy(float), pd.Series(right).rank(method="average").to_numpy(float))


def _residuals(frame: pd.DataFrame, column: str) -> np.ndarray:
    league = pd.get_dummies(frame[["league"]].astype(str), drop_first=True, dtype=float)
    design = np.column_stack([np.ones(len(frame)), frame["opening_lambda"].to_numpy(float), league.to_numpy()])
    values = frame[column].to_numpy(float)
    return values - design @ np.linalg.lstsq(design, values, rcond=None)[0]


def _residual_spearman(frame: pd.DataFrame) -> float:
    return _spearman(_residuals(frame, "match_shape_gap"), _residuals(frame, "centre_delta"))


def _permutation(frame: pd.DataFrame) -> dict[str, Any]:
    observed = _residual_spearman(frame)
    score = _residuals(frame, "match_shape_gap")
    groups = [np.asarray(v, dtype=int) for v in frame.groupby("league", sort=True).indices.values()]
    rng = np.random.default_rng(SEED)
    hits = 0
    for _ in range(PERMUTATION_DRAWS):
        shuffled = frame.copy()
        values = shuffled["centre_delta"].to_numpy(float)
        for indices in groups:
            values[indices] = rng.permutation(values[indices])
        shuffled["centre_delta"] = values
        hits += int(_spearman(score, _residuals(shuffled, "centre_delta")) >= observed - 1e-15)
    return {"draws": PERMUTATION_DRAWS, "seed": SEED, "one_sided_p": (hits + 1) / (PERMUTATION_DRAWS + 1)}


def _binary(frame: pd.DataFrame) -> dict[str, Any]:
    actual = frame["centre_delta"].to_numpy(float) > 0
    predicted = frame["match_shape_gap"].to_numpy(float) > 0
    up_recall = float(np.mean(predicted[actual])) if actual.any() else None
    down_recall = float(np.mean(~predicted[~actual])) if (~actual).any() else None
    return {
        "rows": int(len(frame)), "up_rows": int(actual.sum()), "down_rows": int((~actual).sum()),
        "raw_accuracy": float(np.mean(predicted == actual)), "always_up_accuracy": float(np.mean(actual)),
        "up_recall": up_recall, "down_recall": down_recall,
        "balanced_accuracy": (up_recall + down_recall) / 2 if up_recall is not None and down_recall is not None else None,
    }


def evaluate() -> dict[str, Any]:
    audit: dict[str, Any] | None = None
    try:
        payload = _artifact_bytes()
        contract = _read_artifact(payload, target=False)
        prepared, audit = _prepare_without_target(contract, _download_football_data())
        if not audit["passed"]:
            return _source_gap("exact same-fixture cross-market coverage is incomplete", audit=audit)
        targets = _read_artifact(payload, target=True)
        targets["fixture_id"] = targets["fixture_id"].astype(str)
        frame = prepared.merge(targets, on="fixture_id", how="left", validate="one_to_one")
        for column in ("closing_lambda", "centre_delta", "match_shape_gap", "opening_lambda"):
            frame[column] = pd.to_numeric(frame[column], errors="raise")
        if frame[["closing_lambda", "centre_delta"]].isna().any().any():
            raise RuntimeError("movement target coverage is incomplete after the passed source audit")
    except (OSError, RuntimeError, ValueError, KeyError, zipfile.BadZipFile, requests.RequestException, pd.errors.ParserError) as error:
        return _source_gap(str(error), audit=audit)

    nonzero = frame.loc[~np.isclose(frame["centre_delta"], 0.0, atol=1e-12)].reset_index(drop=True)
    per_league = {
        league: {
            "rows": int(len(group)),
            "spearman": _spearman(group["match_shape_gap"].to_numpy(float), group["centre_delta"].to_numpy(float)),
            "pearson": _pearson(group["match_shape_gap"].to_numpy(float), group["centre_delta"].to_numpy(float)),
        }
        for league, group in nonzero.groupby("league", sort=True)
    }
    pooled_spearman = _spearman(nonzero["match_shape_gap"].to_numpy(float), nonzero["centre_delta"].to_numpy(float))
    pooled_pearson = _pearson(nonzero["match_shape_gap"].to_numpy(float), nonzero["centre_delta"].to_numpy(float))
    residual = _residual_spearman(nonzero)
    residual_pearson = _pearson(_residuals(nonzero, "match_shape_gap"), _residuals(nonzero, "centre_delta"))
    permutation = _permutation(nonzero)
    leave_one = {
        league: _residual_spearman(nonzero.loc[nonzero["league"] != league].reset_index(drop=True))
        for league in LEAGUES
    }
    robust = bool(
        all(league in per_league and per_league[league]["spearman"] > 0 for league in LEAGUES)
        and pooled_spearman > 0
        and residual > 0
        and permutation["one_sided_p"] <= 0.05
        and all(value > 0 for value in leave_one.values())
    )
    binary = _binary(nonzero)
    audit = dict(audit or {})
    audit["movement_target_loaded"] = True
    return {
        "experiment_id": EXPERIMENT_ID,
        "decision": "SUPPORTED_FOR_FUTURE_CONFIRMATION" if robust else "WEAK_OR_INCONSISTENT_CROSS_MARKET_CORNER_DIRECTION_HYPOTHESIS",
        "artifact_id": ARTIFACT_ID,
        "artifact_sha256": ARTIFACT_SHA256,
        "coverage_audit": audit,
        "rows": int(len(frame)),
        "nonzero_movement_rows": int(len(nonzero)),
        "binary_direction_status": "WEAK_BELOW_ALWAYS_UP_WITH_DOWN_SCARCITY" if binary["raw_accuracy"] <= binary["always_up_accuracy"] else "ABOVE_ALWAYS_UP_DIAGNOSTIC_ONLY",
        "continuous_ranking_status": "CROSS_LEAGUE_TRANSFER_SUPPORTED_REQUIRES_UNTOUCHED_CONFIRMATION" if robust else "CROSS_LEAGUE_TRANSFER_NOT_SUPPORTED",
        "binary_direction": binary,
        "raw_continuous": {"pooled_spearman": pooled_spearman, "pooled_pearson": pooled_pearson, "by_league": per_league},
        "falsification": {
            "mechanical_opening_component_pearson_nonzero": _pearson(
                -nonzero["opening_lambda"].to_numpy(float),
                nonzero["centre_delta"].to_numpy(float),
            ),
            "residual_pearson_nonzero": residual_pearson,
            "residual_spearman_nonzero": residual,
            "permutation_p": permutation["one_sided_p"],
            "permutation": permutation,
        },
        "leave_one_league_out": leave_one,
        "safety": _safety(),
        "interpretation_guard": "Bundesliga/Ligue 1 are independent of #522, but their movements were opened previously for other hypotheses. This is cross-league falsification, not untouched confirmation or a betting edge; NO_BET remains binding.",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, sort_keys=True))
