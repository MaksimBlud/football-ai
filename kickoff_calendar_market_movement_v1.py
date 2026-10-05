"""Outcome-free OOS audit of kickoff/calendar effects on O/U 2.5 repricing.

The target is the Bet365 no-vig Over-2.5 probability change from the published
opening columns to the published closing columns. Match outcomes are neither
loaded nor used. Research-only: no paid API, Supabase, production operation or
promotion.
"""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import requests
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from historical_football_signal_runner import BASE, LEAGUES
from kickoff_calendar_context_v1 import LEAGUE_ORDER, SLOTS, WEEKDAYS, _slot

EXPERIMENT_ID = "KICKOFF_CALENDAR_MARKET_MOVEMENT_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
REQUIRED_COLUMNS = (
    "Date",
    "Time",
    "B365>2.5",
    "B365<2.5",
    "B365C>2.5",
    "B365C<2.5",
)
BOOTSTRAP_DRAWS = 5000
SEED = 20261005


def _devig_over(over_odds: float, under_odds: float) -> float:
    inverse_over = 1.0 / over_odds
    inverse_under = 1.0 / under_odds
    return inverse_over / (inverse_over + inverse_under)


def _source_gap_result(
    coverage: dict[str, Any], source_gaps: list[dict[str, Any]]
) -> dict[str, Any]:
    empty_split = {
        "rows": 0,
        "baseline_mse": None,
        "calendar_mse": None,
        "calendar_minus_baseline_mse": None,
        "baseline_mae": None,
        "calendar_mae": None,
        "baseline_sign_accuracy": None,
        "calendar_sign_accuracy": None,
        "nonzero_movement_rows": 0,
    }
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "OUTCOME_FREE_MARKET_MOVEMENT_MECHANISM",
        "research_only": True,
        "match_outcomes_used": False,
        "production_promotion": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "opened_2026_27_data_used": False,
        "coverage": coverage,
        "source_gaps": source_gaps,
        "reference_rows": 0,
        "validation": dict(empty_split),
        "test": {**empty_split, "bootstrap": {"ci95_low": None, "ci95_high": None}},
        "supported": False,
        "decision": "BLOCKED_BY_OPEN_CLOSE_SOURCE_GAP",
        "interpretation_guard": (
            "The required Bet365 opening/closing O/U 2.5 source contract was not "
            "available for every frozen league-season; no proxy was substituted."
        ),
        "result": "RESEARCH_ONLY",
    }


def _download_rows() -> tuple[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]:
    original_get = requests.get
    rows: list[dict[str, Any]] = []
    coverage: dict[str, dict[str, Any]] = {}
    source_gaps: list[dict[str, Any]] = []
    try:
        requests.get = _official_or_pinned_mirror_get
        for league in LEAGUE_ORDER:
            config = LEAGUES[league]
            coverage[league] = {}
            for code, season in config.historical_source.season_codes.items():
                if season not in ALLOWED:
                    continue
                url = BASE.format(
                    code=code, comp=config.historical_source.competition_code
                )
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                payload = response.content
                header = pd.read_csv(BytesIO(payload), nrows=0)
                missing = sorted(set(REQUIRED_COLUMNS) - set(header.columns))
                if missing:
                    frame = pd.DataFrame()
                    source_rows = 0
                    source_gaps.append(
                        {"league": league, "season": season, "missing": missing}
                    )
                else:
                    # Outcomes are deliberately excluded at parse time.
                    frame = pd.read_csv(BytesIO(payload), usecols=list(REQUIRED_COLUMNS))
                    source_rows = len(frame)

                usable = 0
                nonzero = 0
                for _, row in frame.iterrows():
                    date = pd.to_datetime(row.get("Date"), dayfirst=True, errors="coerce")
                    time = str(row.get("Time", "")).strip()
                    try:
                        hour, minute = [int(value) for value in time.split(":")[:2]]
                        opening_over = float(row.get("B365>2.5"))
                        opening_under = float(row.get("B365<2.5"))
                        closing_over = float(row.get("B365C>2.5"))
                        closing_under = float(row.get("B365C<2.5"))
                    except (TypeError, ValueError):
                        continue
                    odds = (opening_over, opening_under, closing_over, closing_under)
                    if (
                        pd.isna(date)
                        or not (0 <= hour <= 23 and 0 <= minute <= 59)
                        or not all(np.isfinite(value) and value > 1.0 for value in odds)
                    ):
                        continue
                    decimal_hour = hour + minute / 60.0
                    p_open = _devig_over(opening_over, opening_under)
                    p_close = _devig_over(closing_over, closing_under)
                    movement = p_close - p_open
                    rows.append(
                        {
                            "league": league,
                            "season": season,
                            "date": date,
                            "weekday": int(date.dayofweek),
                            "hour": decimal_hour,
                            "slot": _slot(decimal_hour),
                            "p_open_over25": p_open,
                            "movement": movement,
                        }
                    )
                    usable += 1
                    nonzero += int(not np.isclose(movement, 0.0, atol=1e-12))
                coverage[league][season] = {
                    "source_rows": int(source_rows),
                    "usable_rows": int(usable),
                    "nonzero_movement_rows": int(nonzero),
                    "missing_required_columns": missing,
                }
    finally:
        requests.get = original_get

    data = pd.DataFrame(rows)
    if not data.empty:
        data = data.sort_values(["date", "league"], kind="stable").reset_index(
            drop=True
        )
    return data, coverage, source_gaps


def _design(frame: pd.DataFrame, with_calendar: bool) -> np.ndarray:
    columns = [frame["p_open_over25"].to_numpy(float).reshape(-1, 1)]
    leagues = frame["league"].astype(str)
    for league in LEAGUE_ORDER[1:]:
        columns.append((leagues == league).astype(float).to_numpy().reshape(-1, 1))

    if with_calendar:
        weekdays = frame["weekday"].astype(int)
        for day in WEEKDAYS[1:]:
            columns.append((weekdays == day).astype(float).to_numpy().reshape(-1, 1))
        hour = frame["hour"].to_numpy(float)
        radians = 2.0 * math.pi * hour / 24.0
        columns.append(np.sin(radians).reshape(-1, 1))
        columns.append(np.cos(radians).reshape(-1, 1))
        slots = frame["slot"].astype(str)
        for slot in SLOTS[1:]:
            columns.append((slots == slot).astype(float).to_numpy().reshape(-1, 1))
    return np.hstack(columns)


def _model() -> Any:
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


def _paired_bootstrap(frame: pd.DataFrame, loss_delta: np.ndarray) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    leagues = frame["league"].astype(str).to_numpy()
    groups = {league: np.flatnonzero(leagues == league) for league in LEAGUE_ORDER}
    if any(len(indices) == 0 for indices in groups.values()):
        raise RuntimeError("OOT bootstrap missing frozen league")
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    total = len(frame)
    for draw in range(BOOTSTRAP_DRAWS):
        value = 0.0
        for indices in groups.values():
            chosen = rng.choice(indices, size=len(indices), replace=True)
            value += float(loss_delta[chosen].sum())
        draws[draw] = value / total
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": SEED,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "probability_below_zero": float((draws < 0.0).mean()),
    }


def _sign_accuracy(y: np.ndarray, prediction: np.ndarray) -> tuple[int, float | None]:
    mask = ~np.isclose(y, 0.0, atol=1e-12)
    rows = int(mask.sum())
    if rows == 0:
        return 0, None
    value = float((np.sign(prediction[mask]) == np.sign(y[mask])).mean())
    return rows, value


def _evaluate_split(
    frame: pd.DataFrame,
    baseline: Any,
    calendar: Any,
    *,
    bootstrap: bool,
) -> dict[str, Any]:
    target = frame["movement"].to_numpy(float)
    baseline_prediction = baseline.predict(_design(frame, False))
    calendar_prediction = calendar.predict(_design(frame, True))
    baseline_error = (target - baseline_prediction) ** 2
    calendar_error = (target - calendar_prediction) ** 2
    loss_delta = calendar_error - baseline_error
    nonzero_rows, baseline_sign = _sign_accuracy(target, baseline_prediction)
    _, calendar_sign = _sign_accuracy(target, calendar_prediction)
    report = {
        "rows": int(len(frame)),
        "by_league_rows": {
            league: int((frame["league"] == league).sum()) for league in LEAGUE_ORDER
        },
        "nonzero_movement_rows": nonzero_rows,
        "baseline_mse": float(baseline_error.mean()),
        "calendar_mse": float(calendar_error.mean()),
        "calendar_minus_baseline_mse": float(loss_delta.mean()),
        "baseline_mae": float(np.abs(target - baseline_prediction).mean()),
        "calendar_mae": float(np.abs(target - calendar_prediction).mean()),
        "baseline_sign_accuracy": baseline_sign,
        "calendar_sign_accuracy": calendar_sign,
    }
    if bootstrap:
        report["bootstrap"] = _paired_bootstrap(frame, loss_delta)
    return report


def _supported(validation: dict[str, Any], test: dict[str, Any]) -> bool:
    return bool(
        validation["calendar_minus_baseline_mse"] < 0.0
        and test["calendar_minus_baseline_mse"] < 0.0
        and test["bootstrap"]["ci95_high"] < 0.0
    )


def evaluate() -> dict[str, Any]:
    data, coverage, source_gaps = _download_rows()
    if source_gaps:
        return _source_gap_result(coverage, source_gaps)

    reference = data[data["season"].isin(REFERENCE)].copy()
    validation_frame = data[data["season"] == VALIDATION].copy()
    test_frame = data[data["season"] == TEST].copy()
    if min(len(reference), len(validation_frame), len(test_frame)) == 0:
        missing_splits = [
            name
            for name, frame in (
                ("reference", reference),
                ("validation", validation_frame),
                ("test", test_frame),
            )
            if frame.empty
        ]
        return _source_gap_result(
            coverage,
            [{"missing_frozen_splits": missing_splits}],
        )

    baseline = _model()
    calendar = _model()
    target = reference["movement"].to_numpy(float)
    baseline.fit(_design(reference, False), target)
    calendar.fit(_design(reference, True), target)
    validation = _evaluate_split(
        validation_frame, baseline, calendar, bootstrap=False
    )
    test = _evaluate_split(test_frame, baseline, calendar, bootstrap=True)
    supported = _supported(validation, test)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "OUTCOME_FREE_MARKET_MOVEMENT_MECHANISM",
        "research_only": True,
        "match_outcomes_used": False,
        "production_promotion": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "opened_2026_27_data_used": False,
        "leagues": list(LEAGUE_ORDER),
        "reference_seasons": list(REFERENCE),
        "validation_season": VALIDATION,
        "test_season": TEST,
        "coverage": coverage,
        "source_gaps": [],
        "reference_rows": int(len(reference)),
        "validation": validation,
        "test": test,
        "supported": supported,
        "decision": (
            "KICKOFF_CALENDAR_PREDICTS_OU25_REPRICING"
            if supported
            else "NO_STABLE_KICKOFF_CALENDAR_OU25_REPRICING"
        ),
        "interpretation_guard": (
            "This outcome-free test concerns opening-to-closing market repricing only; "
            "it cannot rescue the rejected goal-outcome hypothesis or authorize betting."
        ),
        "result": "RESEARCH_ONLY",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, sort_keys=True, ensure_ascii=False))
