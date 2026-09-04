"""Prospective market-path research primitives.

Research-only and read-only. Every feature is derived exclusively from snapshots
observed no later than kickoff minus six hours for fixtures whose kickoff is not
before the preregistration timestamp.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from league_config import get_league_config
from team_names import normalize_team_name

FREEZE_UTC = pd.Timestamp("2026-09-04T14:25:00Z")
CUTOFF_HOURS = 6
MIN_SNAPSHOTS = 3
MIN_PATH_SPAN_HOURS = 12.0
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A")
OUTCOMES = ("H", "D", "A")
BASE_FEATURES = ["market_home_prob", "market_draw_prob", "market_away_prob"]
PATH_FEATURES = [
    "net_home_prob_move",
    "net_draw_prob_move",
    "net_away_prob_move",
    "total_home_prob_path",
    "total_draw_prob_path",
    "total_away_prob_path",
]
MIN_FIXTURES_PER_LEAGUE = 100
MIN_MONTHS_PER_LEAGUE = 4
MIN_TEST_BLOCKS = 2
MIN_TRAIN = 60
MIN_TEST = 20


@dataclass(frozen=True)
class Readiness:
    league: str
    fixtures: int
    calendar_months: int
    valid_test_blocks: int
    ready: bool


def _novig(home, draw, away) -> tuple[float, float, float]:
    odds = np.asarray([home, draw, away], dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("invalid 1X2 odds")
    inv = 1.0 / odds
    p = inv / inv.sum()
    return float(p[0]), float(p[1]), float(p[2])


def build_market_paths(snapshots: pd.DataFrame) -> pd.DataFrame:
    required = {
        "league", "event_id", "home_team", "away_team", "commence_time_utc",
        "snapshot_time_utc", "home_odds", "draw_odds", "away_odds",
    }
    missing = required - set(snapshots.columns)
    if missing:
        raise ValueError("snapshots missing columns: " + ", ".join(sorted(missing)))
    work = snapshots.copy()
    work = work[work["league"].astype(str).isin(LEAGUES)].copy()
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work["snapshot_time_utc"] = pd.to_datetime(work["snapshot_time_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["commence_time_utc", "snapshot_time_utc"])
    work = work[work["commence_time_utc"] >= FREEZE_UTC].copy()
    work["cutoff_utc"] = work["commence_time_utc"] - pd.Timedelta(hours=CUTOFF_HOURS)
    work = work[work["snapshot_time_utc"] <= work["cutoff_utc"]].copy()
    if work.empty:
        return pd.DataFrame()

    probs = []
    for row in work.itertuples(index=False):
        try:
            probs.append(_novig(row.home_odds, row.draw_odds, row.away_odds))
        except (TypeError, ValueError):
            probs.append((np.nan, np.nan, np.nan))
    work[["p_home", "p_draw", "p_away"]] = pd.DataFrame(probs, index=work.index)
    work = work.dropna(subset=["p_home", "p_draw", "p_away"])

    rows = []
    identity = ["league", "event_id"]
    for (league, event_id), group in work.groupby(identity, sort=False):
        group = group.sort_values("snapshot_time_utc").drop_duplicates("snapshot_time_utc", keep="last")
        # A provider event may be rescheduled while retaining event_id. Mixing snapshots
        # from multiple announced kickoffs would make the -6h information cutoff
        # ambiguous, so the entire event is excluded rather than guessed or re-keyed.
        kickoff_values = group["commence_time_utc"].unique()
        if len(kickoff_values) != 1:
            print(f"WAIT conflicting kickoff excluded for {league}/{event_id}")
            continue
        if len(group) < MIN_SNAPSHOTS:
            continue
        span_hours = (group["snapshot_time_utc"].iloc[-1] - group["snapshot_time_utc"].iloc[0]).total_seconds() / 3600.0
        if span_hours < MIN_PATH_SPAN_HOURS:
            continue
        first = group.iloc[0]
        last = group.iloc[-1]
        row = {
            "league": str(league),
            "event_id": str(event_id),
            "home_team": str(last["home_team"]),
            "away_team": str(last["away_team"]),
            "kickoff_utc": pd.Timestamp(last["commence_time_utc"]),
            "cutoff_snapshot_time_utc": pd.Timestamp(last["snapshot_time_utc"]),
            "first_path_snapshot_time_utc": pd.Timestamp(first["snapshot_time_utc"]),
            "path_snapshot_count": int(len(group)),
            "path_span_hours": float(span_hours),
            "market_home_prob": float(last["p_home"]),
            "market_draw_prob": float(last["p_draw"]),
            "market_away_prob": float(last["p_away"]),
        }
        for label in ("home", "draw", "away"):
            values = group[f"p_{label}"].to_numpy(dtype=float)
            row[f"net_{label}_prob_move"] = float(values[-1] - values[0])
            row[f"total_{label}_prob_path"] = float(np.abs(np.diff(values)).sum())
        rows.append(row)
    result = pd.DataFrame(rows)
    if not result.empty and result.duplicated(["league", "event_id"]).any():
        raise ValueError("duplicate market-path fixture identity")
    return result


def _team_key(value) -> str:
    return normalize_team_name(str(value))


def settle_market_paths(paths: pd.DataFrame, results: pd.DataFrame, league: str) -> pd.DataFrame:
    if paths.empty or results.empty:
        return pd.DataFrame()
    required_results = {"league", "match_date", "home_team", "away_team", "result"}
    missing = required_results - set(results.columns)
    if missing:
        raise ValueError("results missing columns: " + ", ".join(sorted(missing)))
    p = paths[paths["league"].astype(str) == league].copy()
    r = results[results["league"].astype(str) == league].copy()
    if p.empty or r.empty:
        return pd.DataFrame()
    timezone = get_league_config(league).timezone
    p["_match_date"] = pd.to_datetime(p["kickoff_utc"], utc=True).dt.tz_convert(timezone).dt.date
    p["_home_key"] = p["home_team"].map(_team_key)
    p["_away_key"] = p["away_team"].map(_team_key)
    r["_match_date"] = pd.to_datetime(r["match_date"], errors="coerce").dt.date
    r["_home_key"] = r["home_team"].map(_team_key)
    r["_away_key"] = r["away_team"].map(_team_key)
    r["result"] = r["result"].astype(str).str.upper()
    if not r["result"].isin(OUTCOMES).all():
        raise ValueError("invalid finished result")
    identity = ["_match_date", "_home_key", "_away_key"]

    # Distinct provider event ids can represent multiple schedule revisions of the
    # same canonical fixture. Do not select one revision using later provider state:
    # exclude the entire ambiguous canonical identity fail-closed before settlement.
    ambiguous_paths = p.duplicated(identity, keep=False)
    if ambiguous_paths.any():
        for key in p.loc[ambiguous_paths, identity].drop_duplicates().itertuples(index=False, name=None):
            print(f"WAIT ambiguous canonical path identity excluded for {league}/{key}")
        p = p.loc[~ambiguous_paths].copy()
        if p.empty:
            return pd.DataFrame()

    result_view = r[identity + ["result"]].copy()
    if result_view.duplicated(identity, keep=False).any():
        raise ValueError("duplicate finished-result fixture identity")
    settled = p.merge(result_view.rename(columns={"result": "actual_result"}), on=identity, how="inner", validate="one_to_one")
    kickoff_utc = pd.to_datetime(settled["kickoff_utc"], utc=True)
    settled["month"] = kickoff_utc.dt.tz_localize(None).dt.to_period("M").astype(str)
    return settled


def readiness_for_league(settled: pd.DataFrame, league: str) -> Readiness:
    if settled.empty or "league" not in settled.columns:
        return Readiness(league, 0, 0, 0, False)
    frame = settled[settled["league"].astype(str) == league].sort_values("kickoff_utc").copy()
    fixtures = int(frame["event_id"].nunique()) if not frame.empty else 0
    months = sorted(frame["month"].unique()) if not frame.empty else []
    valid_blocks = 0
    for month in months:
        test = frame[frame["month"] == month]
        start = pd.Period(month, freq="M").start_time.tz_localize("UTC")
        train = frame[pd.to_datetime(frame["kickoff_utc"], utc=True) < start]
        if len(train) >= MIN_TRAIN and len(test) >= MIN_TEST:
            valid_blocks += 1
    ready = fixtures >= MIN_FIXTURES_PER_LEAGUE and len(months) >= MIN_MONTHS_PER_LEAGUE and valid_blocks >= MIN_TEST_BLOCKS
    return Readiness(league, fixtures, len(months), valid_blocks, ready)


def _model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000)),
    ])


def _metrics(y: np.ndarray, p: np.ndarray) -> tuple[float, float]:
    onehot = np.eye(3)[y]
    brier = float(np.mean(np.sum((p - onehot) ** 2, axis=1)))
    loss = float(log_loss(y, p, labels=[0, 1, 2]))
    return brier, loss


def evaluate_ready_league(settled: pd.DataFrame, league: str) -> pd.DataFrame:
    readiness = readiness_for_league(settled, league)
    if not readiness.ready:
        raise RuntimeError(f"{league} prospective market-path sample is not ready")
    frame = settled[settled["league"].astype(str) == league].sort_values("kickoff_utc").copy()
    outcome_map = {"H": 0, "D": 1, "A": 2}
    rows = []
    for month in sorted(frame["month"].unique()):
        test = frame[frame["month"] == month].copy()
        start = pd.Period(month, freq="M").start_time.tz_localize("UTC")
        train = frame[pd.to_datetime(frame["kickoff_utc"], utc=True) < start].copy()
        if len(train) < MIN_TRAIN or len(test) < MIN_TEST:
            continue
        y_train = train["actual_result"].map(outcome_map).to_numpy(dtype=int)
        y_test = test["actual_result"].map(outcome_map).to_numpy(dtype=int)
        block = {"league": league, "test_month": month, "matches": len(test)}
        for name, columns in (
            ("MARKET_MODEL", BASE_FEATURES),
            ("MARKET_PATH_MODEL", BASE_FEATURES + PATH_FEATURES),
        ):
            model = _model()
            model.fit(train[columns], y_train)
            probabilities = model.predict_proba(test[columns])
            brier, loss = _metrics(y_test, probabilities)
            block[f"{name}_brier"] = brier
            block[f"{name}_log_loss"] = loss
        block["delta_brier"] = block["MARKET_PATH_MODEL_brier"] - block["MARKET_MODEL_brier"]
        block["delta_log_loss"] = block["MARKET_PATH_MODEL_log_loss"] - block["MARKET_MODEL_log_loss"]
        rows.append(block)
    return pd.DataFrame(rows)
