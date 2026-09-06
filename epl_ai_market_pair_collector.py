"""Prospective EPL Football-AI-vs-market pair collection core.

Research only. This module never reads target outcomes. It uses one already-loaded
historical ``matches`` snapshot, one immutable model artifact and one immutable
calibrator artifact to generate point-in-time probabilities for future EPL fixtures.

The conservative history gate requires the latest historical match date to be
strictly before the canonical market snapshot UTC date. This intentionally gives up
some same-day coverage rather than risk using information that was unavailable at
that market decision timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

from research_model_features import (
    FEATURES,
    HOME_ADVANTAGE,
    INITIAL_ELO,
    LAST_MATCHES,
    average,
    calculate_current_state,
)
from team_names import normalize_team_name

EXPERIMENT_ID = "EPL_AI_MARKET_PAIR_V1"
LEAGUE = "EPL"
MODEL_PATH = Path("football_model_no_odds.pkl")
CALIBRATOR_PATH = Path("1x2_calibrator.pkl")
EPS = 1e-7
PROB_TOL = 1e-6

LEDGER_REQUIRED = {
    "prediction_key",
    "league",
    "event_id",
    "home_team",
    "away_team",
    "kickoff_utc",
    "prediction_time_utc",
    "snapshot_time_utc",
    "market_home_prob",
    "market_draw_prob",
    "market_away_prob",
    "prediction_mode",
}
ODDS_REQUIRED = {
    "league",
    "event_id",
    "snapshot_time_utc",
    "commence_time_utc",
    "home_team",
    "away_team",
    "home_odds",
    "draw_odds",
    "away_odds",
}
HISTORY_REQUIRED = {
    "match_date",
    "match_time",
    "home_team",
    "away_team",
    "home_goals",
    "away_goals",
    "result",
    "home_shots",
    "away_shots",
    "home_shots_target",
    "away_shots_target",
}


@dataclass(frozen=True)
class ModelBundle:
    model: Any
    calibrator: Any
    model_sha256: str
    calibrator_sha256: str


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_model_bundle(
    model_path: Path = MODEL_PATH,
    calibrator_path: Path = CALIBRATOR_PATH,
) -> ModelBundle:
    if not model_path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")
    if not calibrator_path.exists():
        raise FileNotFoundError(f"Calibrator artifact not found: {calibrator_path}")

    model_sha = sha256_file(model_path)
    calibrator_sha = sha256_file(calibrator_path)
    model = joblib.load(model_path)
    calibrator = joblib.load(calibrator_path)

    feature_names = set(map(str, model.feature_names_in_))
    forbidden = {"home_odds", "draw_odds", "away_odds"}.intersection(feature_names)
    if forbidden:
        raise RuntimeError(
            "Expected no-odds model but artifact requires market odds features: "
            f"{sorted(forbidden)}"
        )
    return ModelBundle(model, calibrator, model_sha, calibrator_sha)


def verify_model_bundle_unchanged(
    bundle: ModelBundle,
    model_path: Path = MODEL_PATH,
    calibrator_path: Path = CALIBRATOR_PATH,
) -> None:
    if sha256_file(model_path) != bundle.model_sha256:
        raise RuntimeError("Model artifact changed during prospective collection")
    if sha256_file(calibrator_path) != bundle.calibrator_sha256:
        raise RuntimeError("Calibrator artifact changed during prospective collection")


def _normalize_probabilities(values: np.ndarray) -> np.ndarray:
    probs = np.asarray(values, dtype=float)
    if probs.shape != (3,) or not np.isfinite(probs).all() or (probs < 0).any():
        raise ValueError("Invalid H/D/A probability vector")
    total = float(probs.sum())
    if total <= 0:
        raise ValueError("Non-positive H/D/A probability sum")
    probs = probs / total
    if (probs > 1).any():
        raise ValueError("Invalid normalized H/D/A probability vector")
    return probs


def calibrate_with_bundle(raw_probabilities: np.ndarray, calibrator: Any) -> np.ndarray:
    raw = np.clip(_normalize_probabilities(raw_probabilities), EPS, 1 - EPS)
    raw = raw / raw.sum()
    method = calibrator.get("method", "RAW")

    if method == "MULTINOMIAL":
        calibrated = calibrator["model"].predict_proba(np.log(raw).reshape(1, -1))[0]
        return _normalize_probabilities(calibrated)
    if method == "TEMPERATURE":
        temperature = float(calibrator["temperature"])
        if not np.isfinite(temperature) or temperature <= 0:
            raise ValueError("Invalid calibration temperature")
        scaled = np.log(raw) / temperature
        scaled -= scaled.max()
        return _normalize_probabilities(np.exp(scaled))
    return raw


def prepare_history_snapshot(history: pd.DataFrame) -> pd.DataFrame:
    missing = HISTORY_REQUIRED.difference(history.columns)
    if missing:
        raise ValueError(f"matches history missing columns: {sorted(missing)}")
    if history.empty:
        raise ValueError("matches history is empty")

    work = history.copy()
    work["match_date"] = pd.to_datetime(work["match_date"], errors="coerce")
    if work["match_date"].isna().any():
        raise ValueError("matches history contains invalid match_date")
    work["match_time"] = work["match_time"].fillna("00:00").astype(str)
    if not work["result"].astype(str).isin(["H", "D", "A"]).all():
        raise ValueError("matches history contains non-final result values")

    numeric_columns = [
        "home_goals",
        "away_goals",
        "home_shots",
        "away_shots",
        "home_shots_target",
        "away_shots_target",
    ]
    for column in numeric_columns:
        work[column] = pd.to_numeric(work[column], errors="coerce")
        if work[column].isna().any():
            raise ValueError(f"matches history contains invalid {column}")

    return work.sort_values(["match_date", "match_time"]).reset_index(drop=True)


def _feature_frame_from_history(
    history: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
) -> pd.DataFrame:
    if home_team == away_team:
        raise ValueError("Home and away teams must differ")
    known_teams = set(history["home_team"].astype(str)) | set(history["away_team"].astype(str))
    unknown = [team for team in (home_team, away_team) if team not in known_teams]
    if unknown:
        raise ValueError(f"Unknown normalized model teams: {unknown}")

    team_history, home_venue_history, away_venue_history, ratings = calculate_current_state(history)
    home_history = team_history.get(home_team, [])[-LAST_MATCHES:]
    away_history = team_history.get(away_team, [])[-LAST_MATCHES:]
    home_last5_points = sum(match["points"] for match in home_history)
    away_last5_points = sum(match["points"] for match in away_history)
    home_elo = ratings.get(home_team, INITIAL_ELO)
    away_elo = ratings.get(away_team, INITIAL_ELO)
    home_venue_matches = home_venue_history.get(home_team, [])
    away_venue_matches = away_venue_history.get(away_team, [])

    values = {
        "home_odds": 2.0,
        "draw_odds": 2.0,
        "away_odds": 2.0,
        "home_last5_points": home_last5_points,
        "away_last5_points": away_last5_points,
        "form_difference": home_last5_points - away_last5_points,
        "home_goals_scored_last5": average([m["goals_scored"] for m in home_history]),
        "home_goals_conceded_last5": average([m["goals_conceded"] for m in home_history]),
        "away_goals_scored_last5": average([m["goals_scored"] for m in away_history]),
        "away_goals_conceded_last5": average([m["goals_conceded"] for m in away_history]),
        "home_shots_last5": average([m["shots"] for m in home_history]),
        "away_shots_last5": average([m["shots"] for m in away_history]),
        "home_shots_target_last5": average([m["shots_target"] for m in home_history]),
        "away_shots_target_last5": average([m["shots_target"] for m in away_history]),
        "home_elo": home_elo,
        "away_elo": away_elo,
        "elo_difference": home_elo + HOME_ADVANTAGE - away_elo,
        "home_venue_win_rate": average([m["win"] for m in home_venue_matches]),
        "away_venue_win_rate": average([m["win"] for m in away_venue_matches]),
        "home_venue_goals_scored": average([m["goals_scored"] for m in home_venue_matches]),
        "away_venue_goals_scored": average([m["goals_scored"] for m in away_venue_matches]),
    }
    return pd.DataFrame([values], columns=FEATURES)


def predict_from_history(
    bundle: ModelBundle,
    history: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
) -> tuple[np.ndarray, np.ndarray]:
    features = _feature_frame_from_history(history, home_team=home_team, away_team=away_team)
    model_features = features[list(bundle.model.feature_names_in_)]
    raw = _normalize_probabilities(bundle.model.predict_proba(model_features)[0])
    calibrated = calibrate_with_bundle(raw, bundle.calibrator)
    return raw, calibrated


def canonical_market_candidates(
    ledger: pd.DataFrame,
    odds_snapshots: pd.DataFrame,
    *,
    now_utc: pd.Timestamp | str,
) -> pd.DataFrame:
    missing = LEDGER_REQUIRED.difference(ledger.columns)
    if missing:
        raise ValueError(f"prediction ledger missing columns: {sorted(missing)}")
    missing = ODDS_REQUIRED.difference(odds_snapshots.columns)
    if missing:
        raise ValueError(f"odds snapshots missing columns: {sorted(missing)}")

    now = pd.Timestamp(now_utc)
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    work = ledger.copy()
    for column in ("kickoff_utc", "prediction_time_utc", "snapshot_time_utc"):
        work[column] = pd.to_datetime(work[column], utc=True, errors="coerce")
    work = work.dropna(subset=["kickoff_utc", "prediction_time_utc", "snapshot_time_utc"])
    work = work.loc[
        (work["league"].astype(str) == LEAGUE)
        & (work["prediction_mode"].astype(str) == "MARKET_ONLY")
        & (work["prediction_time_utc"] <= now)
        & (work["snapshot_time_utc"] <= now)
        & (work["snapshot_time_utc"] < work["kickoff_utc"])
        & (work["kickoff_utc"] > now)
    ].copy()
    if work.empty:
        return work

    identity = work.groupby("event_id").agg(
        kickoff_count=("kickoff_utc", "nunique"),
        home_count=("home_team", "nunique"),
        away_count=("away_team", "nunique"),
    )
    conflicting = set(identity.index[(identity > 1).any(axis=1)].astype(str))
    if conflicting:
        work = work.loc[~work["event_id"].astype(str).isin(conflicting)].copy()
    if work.empty:
        return work

    prob_cols = ["market_home_prob", "market_draw_prob", "market_away_prob"]
    probabilities = work[prob_cols].apply(pd.to_numeric, errors="coerce")
    valid = (
        ~probabilities.isna().any(axis=1)
        & np.isfinite(probabilities.to_numpy()).all(axis=1)
        & (probabilities >= 0).all(axis=1)
        & (probabilities <= 1).all(axis=1)
        & np.isclose(probabilities.sum(axis=1), 1.0, atol=PROB_TOL, rtol=0)
    )
    work = work.loc[valid].copy()
    if work.empty:
        return work

    latest = (
        work.sort_values(["event_id", "snapshot_time_utc", "prediction_key"])
        .groupby("event_id", as_index=False)
        .tail(1)
        .copy()
    )

    odds = odds_snapshots.copy()
    for column in ("snapshot_time_utc", "commence_time_utc"):
        odds[column] = pd.to_datetime(odds[column], utc=True, errors="coerce")
    odds = odds.loc[odds["league"].astype(str) == LEAGUE].copy()
    join_keys = ["league", "event_id", "snapshot_time_utc"]
    if odds.duplicated(join_keys).any():
        raise RuntimeError("Ambiguous exact raw odds snapshot identity")

    raw_columns = join_keys + [
        "commence_time_utc",
        "home_team",
        "away_team",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
    merged = latest.merge(
        odds[raw_columns],
        on=join_keys,
        how="left",
        suffixes=("", "_raw"),
        validate="one_to_one",
    )
    if merged[["home_odds", "draw_odds", "away_odds"]].isna().any(axis=None):
        raise RuntimeError("Canonical market row is missing its exact raw odds snapshot")
    if not (
        (merged["home_team"].astype(str) == merged["home_team_raw"].astype(str))
        & (merged["away_team"].astype(str) == merged["away_team_raw"].astype(str))
    ).all():
        raise RuntimeError("Ledger/raw team identity mismatch")
    if not (
        pd.to_datetime(merged["kickoff_utc"], utc=True)
        == pd.to_datetime(merged["commence_time_utc"], utc=True)
    ).all():
        raise RuntimeError("Ledger/raw kickoff identity mismatch")

    prices = merged[["home_odds", "draw_odds", "away_odds"]].apply(pd.to_numeric, errors="coerce")
    if prices.isna().any(axis=None) or (prices <= 1).any(axis=None):
        raise ValueError("Invalid exact raw 1X2 odds")
    implied = 1.0 / prices
    raw_market = implied.div(implied.sum(axis=1), axis=0)
    if not np.allclose(
        raw_market.to_numpy(),
        merged[prob_cols].astype(float).to_numpy(),
        atol=PROB_TOL,
        rtol=0,
    ):
        raise RuntimeError("Ledger market probabilities do not reproduce from exact raw odds")
    return merged.sort_values(["kickoff_utc", "event_id"]).reset_index(drop=True)


def build_pair_rows(
    candidates: pd.DataFrame,
    history: pd.DataFrame,
    bundle: ModelBundle,
    *,
    generated_at_utc: pd.Timestamp | str,
    code_commit_sha: str,
) -> tuple[pd.DataFrame, list[dict[str, str]]]:
    generated = pd.Timestamp(generated_at_utc)
    generated = generated.tz_localize("UTC") if generated.tzinfo is None else generated.tz_convert("UTC")
    history = prepare_history_snapshot(history)
    history_max_date = history["match_date"].max().date()
    history_rows = int(len(history))
    known_teams = set(history["home_team"].astype(str)) | set(history["away_team"].astype(str))
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []

    for _, row in candidates.iterrows():
        event_id = str(row["event_id"])
        kickoff = pd.Timestamp(row["kickoff_utc"])
        snapshot = pd.Timestamp(row["snapshot_time_utc"])
        kickoff = kickoff.tz_localize("UTC") if kickoff.tzinfo is None else kickoff.tz_convert("UTC")
        snapshot = snapshot.tz_localize("UTC") if snapshot.tzinfo is None else snapshot.tz_convert("UTC")
        if generated >= kickoff:
            excluded.append({"event_id": event_id, "reason": "MODEL_NOT_PRE_KICKOFF"})
            continue
        if history_max_date >= snapshot.date():
            excluded.append({"event_id": event_id, "reason": "HISTORY_NOT_STRICTLY_BEFORE_MARKET_DATE"})
            continue

        provider_home = str(row["home_team"])
        provider_away = str(row["away_team"])
        model_home = normalize_team_name(provider_home)
        model_away = normalize_team_name(provider_away)
        if model_home not in known_teams or model_away not in known_teams:
            excluded.append({"event_id": event_id, "reason": "UNKNOWN_NORMALIZED_TEAM"})
            continue

        kickoff_date = kickoff.date()
        same_date_target = history.loc[
            (history["match_date"].dt.date == kickoff_date)
            & (history["home_team"].astype(str) == model_home)
            & (history["away_team"].astype(str) == model_away)
        ]
        if not same_date_target.empty:
            excluded.append({"event_id": event_id, "reason": "TARGET_FIXTURE_PRESENT_IN_HISTORY"})
            continue

        raw, calibrated = predict_from_history(
            bundle,
            history,
            home_team=model_home,
            away_team=model_away,
        )
        identity = "|".join(
            [
                EXPERIMENT_ID,
                event_id,
                snapshot.isoformat(),
                bundle.model_sha256,
                bundle.calibrator_sha256,
            ]
        )
        pair_key = sha256(identity.encode("utf-8")).hexdigest()
        accepted.append(
            {
                "pair_key": pair_key,
                "experiment_id": EXPERIMENT_ID,
                "league": LEAGUE,
                "event_id": event_id,
                "provider_home_team": provider_home,
                "provider_away_team": provider_away,
                "model_home_team": model_home,
                "model_away_team": model_away,
                "kickoff_utc": kickoff.isoformat(),
                "market_snapshot_time_utc": snapshot.isoformat(),
                "model_generated_at_utc": generated.isoformat(),
                "market_home_prob": float(row["market_home_prob"]),
                "market_draw_prob": float(row["market_draw_prob"]),
                "market_away_prob": float(row["market_away_prob"]),
                "model_home_prob": float(calibrated[0]),
                "model_draw_prob": float(calibrated[1]),
                "model_away_prob": float(calibrated[2]),
                "raw_model_home_prob": float(raw[0]),
                "raw_model_draw_prob": float(raw[1]),
                "raw_model_away_prob": float(raw[2]),
                "model_artifact_sha256": bundle.model_sha256,
                "calibrator_artifact_sha256": bundle.calibrator_sha256,
                "code_commit_sha": str(code_commit_sha or "UNKNOWN"),
                "history_max_match_date": history_max_date.isoformat(),
                "history_rows": history_rows,
            }
        )
    return pd.DataFrame(accepted), excluded
