"""Temporal OOS audit of kickoff time/day-of-week for O/U 2.5.

Uses only pre-kickoff calendar/market features and Football-Data historical rows.
Research-only: no production model, paid API, Supabase or promotion.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from historical_football_signal_runner import BASE, LEAGUES

EXPERIMENT_ID = "KICKOFF_CALENDAR_CONTEXT_V1"
REFERENCE = tuple(f"{y}-{y+1}" for y in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
WEEKDAYS = tuple(range(7))
SLOTS = ("EARLY", "AFTERNOON", "EVENING", "LATE")
BOOTSTRAP_DRAWS = 5000
SEED = 20261004


def _slot(hour: float) -> str:
    if hour < 14:
        return "EARLY"
    if hour < 17:
        return "AFTERNOON"
    if hour < 20:
        return "EVENING"
    return "LATE"


def _devig_over(over_odds: float, under_odds: float) -> float:
    io, iu = 1.0 / over_odds, 1.0 / under_odds
    return io / (io + iu)


def _download_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    original = requests.get
    rows: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, Any]] = {}
    try:
        requests.get = _official_or_pinned_mirror_get
        for league in LEAGUE_ORDER:
            config = LEAGUES[league]
            coverage[league] = {}
            for code, season in config.historical_source.season_codes.items():
                if season not in ALLOWED:
                    continue
                url = BASE.format(code=code, comp=config.historical_source.competition_code)
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                frame = pd.read_csv(pd.io.common.BytesIO(response.content))
                source_rows = len(frame)
                required = {"Date", "Time", "FTHG", "FTAG", "B365>2.5", "B365<2.5"}
                missing = sorted(required - set(frame.columns))
                usable = 0
                if not missing:
                    for _, row in frame.iterrows():
                        date = pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce")
                        time = str(row.get("Time", "")).strip()
                        try:
                            hour, minute = [int(x) for x in time.split(":")[:2]]
                        except (ValueError, TypeError):
                            continue
                        if pd.isna(date) or not (0 <= hour <= 23 and 0 <= minute <= 59):
                            continue
                        try:
                            over = float(row.get("B365>2.5"))
                            under = float(row.get("B365<2.5"))
                            home_goals = float(row.get("FTHG"))
                            away_goals = float(row.get("FTAG"))
                        except (TypeError, ValueError):
                            continue
                        if not all(np.isfinite(v) for v in (over, under, home_goals, away_goals)):
                            continue
                        if over <= 1.0 or under <= 1.0:
                            continue
                        decimal_hour = hour + minute / 60.0
                        p_market = _devig_over(over, under)
                        rows.append(
                            {
                                "league": league,
                                "season": season,
                                "date": date,
                                "weekday": int(date.dayofweek),
                                "hour": decimal_hour,
                                "slot": _slot(decimal_hour),
                                "p_market_over25": p_market,
                                "target_over25": int(home_goals + away_goals > 2.5),
                            }
                        )
                        usable += 1
                coverage[league][season] = {
                    "source_rows": int(source_rows),
                    "usable_rows": int(usable),
                    "missing_required_columns": missing,
                }
    finally:
        requests.get = original

    data = pd.DataFrame(rows)
    if data.empty:
        raise RuntimeError("kickoff-calendar dataset is empty")
    return data.sort_values(["date", "league"], kind="stable").reset_index(drop=True), coverage


def _design(frame: pd.DataFrame, with_calendar: bool) -> np.ndarray:
    p = frame["p_market_over25"].clip(1e-6, 1 - 1e-6).to_numpy(float)
    market_logit = np.log(p / (1 - p)).reshape(-1, 1)
    cols = [market_logit]

    league = frame["league"].astype(str)
    for name in LEAGUE_ORDER[1:]:
        cols.append((league == name).astype(float).to_numpy().reshape(-1, 1))

    if with_calendar:
        weekday = frame["weekday"].astype(int)
        for day in WEEKDAYS[1:]:
            cols.append((weekday == day).astype(float).to_numpy().reshape(-1, 1))
        hour = frame["hour"].to_numpy(float)
        radians = 2.0 * math.pi * hour / 24.0
        cols.append(np.sin(radians).reshape(-1, 1))
        cols.append(np.cos(radians).reshape(-1, 1))
        slot = frame["slot"].astype(str)
        for name in SLOTS[1:]:
            cols.append((slot == name).astype(float).to_numpy().reshape(-1, 1))

    return np.hstack(cols)


def _metrics(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    return {
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else float("nan"),
    }


def _paired_bootstrap(frame: pd.DataFrame, loss_delta: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    leagues = frame["league"].astype(str).to_numpy()
    groups = {league: np.flatnonzero(leagues == league) for league in LEAGUE_ORDER}
    if any(len(v) == 0 for v in groups.values()):
        raise RuntimeError("OOT bootstrap missing frozen league")
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    total = len(frame)
    for i in range(BOOTSTRAP_DRAWS):
        value = 0.0
        for indices in groups.values():
            chosen = rng.choice(indices, size=len(indices), replace=True)
            value += float(loss_delta[chosen].sum())
        draws[i] = value / total
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": SEED,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "probability_below_zero": float((draws < 0).mean()),
    }


def _evaluate_split(
    frame: pd.DataFrame,
    baseline: LogisticRegression,
    calendar: LogisticRegression,
    *,
    bootstrap: bool,
) -> dict[str, Any]:
    y = frame["target_over25"].to_numpy(int)
    p_base = baseline.predict_proba(_design(frame, False))[:, 1]
    p_cal = calendar.predict_proba(_design(frame, True))[:, 1]
    p_market = frame["p_market_over25"].to_numpy(float)
    base_m = _metrics(y, p_base)
    cal_m = _metrics(y, p_cal)
    market_m = _metrics(y, p_market)

    eps = 1e-12
    base_loss = -(y * np.log(np.clip(p_base, eps, 1-eps)) + (1-y) * np.log(np.clip(1-p_base, eps, 1-eps)))
    cal_loss = -(y * np.log(np.clip(p_cal, eps, 1-eps)) + (1-y) * np.log(np.clip(1-p_cal, eps, 1-eps)))
    delta = cal_loss - base_loss

    out = {
        "rows": int(len(frame)),
        "by_league_rows": {league: int((frame["league"] == league).sum()) for league in LEAGUE_ORDER},
        "market_direct": market_m,
        "baseline": base_m,
        "calendar": cal_m,
        "calendar_minus_baseline_log_loss": float(cal_m["log_loss"] - base_m["log_loss"]),
    }
    if bootstrap:
        out["bootstrap"] = _paired_bootstrap(frame, delta)
    return out


def evaluate() -> dict[str, Any]:
    data, coverage = _download_rows()
    reference = data[data["season"].isin(REFERENCE)].copy()
    validation = data[data["season"] == VALIDATION].copy()
    test = data[data["season"] == TEST].copy()
    if min(len(reference), len(validation), len(test)) == 0:
        raise RuntimeError("one or more frozen temporal splits are empty")

    baseline = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
    calendar = LogisticRegression(C=1.0, max_iter=2000, solver="lbfgs")
    y_ref = reference["target_over25"].to_numpy(int)
    baseline.fit(_design(reference, False), y_ref)
    calendar.fit(_design(reference, True), y_ref)

    validation_report = _evaluate_split(validation, baseline, calendar, bootstrap=False)
    test_report = _evaluate_split(test, baseline, calendar, bootstrap=True)

    supported = bool(
        validation_report["calendar_minus_baseline_log_loss"] < 0.0
        and test_report["calendar_minus_baseline_log_loss"] < 0.0
        and test_report["bootstrap"]["ci95_high"] < 0.0
    )
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_CALENDAR_INCREMENTAL",
        "research_only": True,
        "production_promotion": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "opened_2026_27_data_used": False,
        "leagues": list(LEAGUE_ORDER),
        "reference_seasons": list(REFERENCE),
        "validation_season": VALIDATION,
        "test_season": TEST,
        "coverage": coverage,
        "reference_rows": int(len(reference)),
        "validation": validation_report,
        "test": test_report,
        "supported": supported,
        "decision": (
            "KICKOFF_CALENDAR_ADDS_OOS_INFO"
            if supported
            else "NO_KICKOFF_CALENDAR_OOS_SIGNAL"
        ),
        "result": "RESEARCH_ONLY",
    }
