"""Reproducible EPL Football-AI-vs-market pair collection core.

Research only. Target settlement tables are never read. The production model artifact
and feature formula both predate the September 2026 decision snapshots. For each
canonical market row we reconstruct only the football history that was safely
available at that exact snapshot and feed the exact recorded 1X2 odds to the tracked
production model.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

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
MODEL_PATH = Path("football_model_xgboost_elo.pkl")
LOCAL_TZ = ZoneInfo("Europe/London")
RESULT_AVAILABILITY_BUFFER = pd.Timedelta(hours=4)
MODEL_ARTIFACT_AVAILABLE_UTC = pd.Timestamp("2026-08-03T15:32:10Z")
FEATURE_FORMULA_AVAILABLE_UTC = pd.Timestamp("2026-08-07T16:14:45Z")
PROB_TOL = 1e-6

LEDGER_REQUIRED = {
    "prediction_key", "league", "event_id", "home_team", "away_team",
    "kickoff_utc", "prediction_time_utc", "snapshot_time_utc",
    "market_home_prob", "market_draw_prob", "market_away_prob", "prediction_mode",
}
ODDS_REQUIRED = {
    "league", "event_id", "snapshot_time_utc", "commence_time_utc",
    "home_team", "away_team", "home_odds", "draw_odds", "away_odds",
}
HISTORY_REQUIRED = {
    "match_date", "match_time", "home_team", "away_team", "home_goals",
    "away_goals", "result", "home_shots", "away_shots",
    "home_shots_target", "away_shots_target",
}


@dataclass(frozen=True)
class ModelBundle:
    model: Any
    model_sha256: str


def sha256_file(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_model_bundle(model_path: Path = MODEL_PATH) -> ModelBundle:
    if not model_path.exists():
        raise FileNotFoundError(f"Tracked production model artifact not found: {model_path}")
    digest = sha256_file(model_path)
    model = joblib.load(model_path)
    feature_names = list(map(str, model.feature_names_in_))
    if feature_names != FEATURES:
        raise RuntimeError(
            "Tracked production model feature schema does not match frozen feature formula: "
            f"expected={FEATURES}, actual={feature_names}"
        )
    return ModelBundle(model=model, model_sha256=digest)


def verify_model_bundle_unchanged(bundle: ModelBundle, model_path: Path = MODEL_PATH) -> None:
    if sha256_file(model_path) != bundle.model_sha256:
        raise RuntimeError("Production model artifact changed during research collection")


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
    work["match_time"] = work["match_time"].where(work["match_time"].notna(), None)
    if not work["result"].astype(str).isin(["H", "D", "A"]).all():
        raise ValueError("matches history contains non-final result values")

    for column in (
        "home_goals", "away_goals", "home_shots", "away_shots",
        "home_shots_target", "away_shots_target",
    ):
        work[column] = pd.to_numeric(work[column], errors="coerce")
        if work[column].isna().any():
            raise ValueError(f"matches history contains invalid {column}")
    return work.sort_values(["match_date", "match_time"], na_position="first").reset_index(drop=True)


def history_as_of_market_snapshot(history: pd.DataFrame, snapshot_utc: pd.Timestamp | str) -> pd.DataFrame:
    """Return only results safely public by ``snapshot_utc``.

    EPL ``match_time`` is Europe/London local time. This was verified against recent
    rows that have exact ``odds_snapshots.commence_time_utc`` identities. Known times
    require kickoff + four hours <= snapshot. For old rows without a stored time, we
    fail closed for the immediately preceding/current local date and include them only
    when at least two local calendar dates behind the snapshot.
    """
    work = prepare_history_snapshot(history)
    cutoff = pd.Timestamp(snapshot_utc)
    cutoff = cutoff.tz_localize("UTC") if cutoff.tzinfo is None else cutoff.tz_convert("UTC")
    cutoff_local_date = cutoff.tz_convert(LOCAL_TZ).date()

    availability = pd.Series(pd.NaT, index=work.index, dtype="datetime64[ns, UTC]")
    has_time = work["match_time"].notna() & work["match_time"].astype(str).str.strip().ne("")
    if has_time.any():
        local_naive = pd.to_datetime(
            work.loc[has_time, "match_date"].dt.strftime("%Y-%m-%d")
            + " "
            + work.loc[has_time, "match_time"].astype(str),
            errors="coerce",
        )
        if local_naive.isna().any():
            raise ValueError("matches history contains invalid match_time")
        localized = local_naive.dt.tz_localize(
            LOCAL_TZ, ambiguous="raise", nonexistent="raise"
        ).dt.tz_convert("UTC")
        availability.loc[has_time] = localized + RESULT_AVAILABILITY_BUFFER

    known_safe = has_time & availability.le(cutoff)
    missing_time_safe_before = pd.Timestamp(cutoff_local_date) - pd.Timedelta(days=2)
    missing_safe = (~has_time) & work["match_date"].lt(missing_time_safe_before)
    return work.loc[known_safe | missing_safe].copy().reset_index(drop=True)


def _feature_frame_from_history(
    history: pd.DataFrame,
    *,
    home_team: str,
    away_team: str,
    home_odds: float,
    draw_odds: float,
    away_odds: float,
) -> pd.DataFrame:
    prices = np.asarray([home_odds, draw_odds, away_odds], dtype=float)
    if not np.isfinite(prices).all() or (prices <= 1).any():
        raise ValueError("Invalid exact 1X2 odds for production model")
    if home_team == away_team:
        raise ValueError("Home and away teams must differ")
    known_teams = set(history["home_team"].astype(str)) | set(history["away_team"].astype(str))
    unknown = [team for team in (home_team, away_team) if team not in known_teams]
    if unknown:
        raise ValueError(f"Unknown normalized model teams at decision time: {unknown}")

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
        "home_odds": float(home_odds), "draw_odds": float(draw_odds), "away_odds": float(away_odds),
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
    home_odds: float,
    draw_odds: float,
    away_odds: float,
) -> np.ndarray:
    features = _feature_frame_from_history(
        history,
        home_team=home_team,
        away_team=away_team,
        home_odds=home_odds,
        draw_odds=draw_odds,
        away_odds=away_odds,
    )
    return _normalize_probabilities(bundle.model.predict_proba(features)[0])


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
        & (work["snapshot_time_utc"] > MODEL_ARTIFACT_AVAILABLE_UTC)
        & (work["snapshot_time_utc"] > FEATURE_FORMULA_AVAILABLE_UTC)
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
        .groupby("event_id", as_index=False).tail(1).copy()
    )
    odds = odds_snapshots.copy()
    for column in ("snapshot_time_utc", "commence_time_utc"):
        odds[column] = pd.to_datetime(odds[column], utc=True, errors="coerce")
    odds = odds.loc[odds["league"].astype(str) == LEAGUE].copy()
    join_keys = ["league", "event_id", "snapshot_time_utc"]
    if odds.duplicated(join_keys).any():
        raise RuntimeError("Ambiguous exact raw odds snapshot identity")
    raw_columns = join_keys + [
        "commence_time_utc", "home_team", "away_team",
        "home_odds", "draw_odds", "away_odds",
    ]
    merged = latest.merge(
        odds[raw_columns], on=join_keys, how="left", suffixes=("", "_raw"), validate="one_to_one"
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
        raw_market.to_numpy(), merged[prob_cols].astype(float).to_numpy(), atol=PROB_TOL, rtol=0
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
    full_history = prepare_history_snapshot(history)
    accepted: list[dict[str, Any]] = []
    excluded: list[dict[str, str]] = []

    for _, row in candidates.iterrows():
        event_id = str(row["event_id"])
        kickoff = pd.Timestamp(row["kickoff_utc"]).tz_convert("UTC")
        snapshot = pd.Timestamp(row["snapshot_time_utc"]).tz_convert("UTC")
        if generated >= kickoff:
            excluded.append({"event_id": event_id, "reason": "MODEL_NOT_GENERATED_PRE_KICKOFF"})
            continue

        history_asof = history_as_of_market_snapshot(full_history, snapshot)
        if history_asof.empty:
            excluded.append({"event_id": event_id, "reason": "EMPTY_HISTORY_AS_OF_MARKET"})
            continue
        provider_home = str(row["home_team"])
        provider_away = str(row["away_team"])
        model_home = normalize_team_name(provider_home)
        model_away = normalize_team_name(provider_away)
        known_teams = set(history_asof["home_team"].astype(str)) | set(history_asof["away_team"].astype(str))
        if model_home not in known_teams or model_away not in known_teams:
            excluded.append({"event_id": event_id, "reason": "UNKNOWN_NORMALIZED_TEAM_AT_DECISION_TIME"})
            continue

        same_target = history_asof.loc[
            (history_asof["home_team"].astype(str) == model_home)
            & (history_asof["away_team"].astype(str) == model_away)
            & (history_asof["match_date"].dt.date == kickoff.tz_convert(LOCAL_TZ).date())
        ]
        if not same_target.empty:
            excluded.append({"event_id": event_id, "reason": "TARGET_FIXTURE_PRESENT_IN_ASOF_HISTORY"})
            continue

        model_probs = predict_from_history(
            bundle,
            history_asof,
            home_team=model_home,
            away_team=model_away,
            home_odds=float(row["home_odds"]),
            draw_odds=float(row["draw_odds"]),
            away_odds=float(row["away_odds"]),
        )
        identity = "|".join([EXPERIMENT_ID, event_id, snapshot.isoformat(), bundle.model_sha256])
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
                "market_home_odds": float(row["home_odds"]),
                "market_draw_odds": float(row["draw_odds"]),
                "market_away_odds": float(row["away_odds"]),
                "market_home_prob": float(row["market_home_prob"]),
                "market_draw_prob": float(row["market_draw_prob"]),
                "market_away_prob": float(row["market_away_prob"]),
                "model_home_prob": float(model_probs[0]),
                "model_draw_prob": float(model_probs[1]),
                "model_away_prob": float(model_probs[2]),
                "model_artifact_sha256": bundle.model_sha256,
                "code_commit_sha": str(code_commit_sha or "UNKNOWN"),
                "history_cutoff_utc": snapshot.isoformat(),
                "history_max_match_date": history_asof["match_date"].max().date().isoformat(),
                "history_rows": int(len(history_asof)),
            }
        )
    return pd.DataFrame(accepted), excluded
