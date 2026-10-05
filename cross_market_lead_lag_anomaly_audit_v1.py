"""2024/25 source/market anomaly audit for frozen cross-market lead-lag.

Research-only, outcome-free and post-hoc. This module diagnoses source/market
structure; it cannot alter V1/V2 gates or create a betting signal.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

import numpy as np
import pandas as pd
import requests

import cross_market_lead_lag_v1 as v1
import cross_market_lead_lag_replication_v2 as v2
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from cross_market_lead_lag_replication_transport import _replication_get
from cross_market_score_coherence_v1 import (
    AH_COLUMNS,
    ONE_X_TWO_COLUMNS,
    TOTAL_COLUMNS,
    _first_line,
    _is_half_goal_line,
    _valid_prices,
)

EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_2024_25_ANOMALY_AUDIT_V1"
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")
SEASONS = (
    "2019-2020",
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
)
TARGET = "2024-2025"
REFERENCE = SEASONS[:5]
ADJACENT = ("2023-2024", "2025-2026")
REQUIRED_COLUMNS = (
    "B365H", "B365D", "B365A", "B365>2.5", "B365<2.5",
    "B365AHH", "B365AHA", "B365CH", "B365CD", "B365CA",
)
CONTINUOUS = (
    "open_1x2_overround",
    "close_1x2_overround",
    "ou25_overround",
    "ah_overround",
    "gap_open_tv",
    "open_to_close_move_tv",
    "gap_reduction_tv",
    "lead_norm",
    "move_norm",
    "ah_fit_abs_error",
)


def _overround(prices: tuple[float, ...] | np.ndarray) -> float:
    values = np.asarray(prices, dtype=float)
    return float(np.sum(1.0 / values) - 1.0)


def _raw_and_rows(league: str) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    original = requests.get
    try:
        if league in {"EPL", "LA_LIGA", "SERIE_A"}:
            requests.get = _official_or_pinned_mirror_get
            raw = v1._download_league_raw(league)
        else:
            requests.get = _replication_get
            raw = v2._download_league_raw(league)
        rows, coverage = v1._build_league_rows(raw, league)
    finally:
        requests.get = original
    return raw, rows, coverage


def _raw_market_diagnostics(raw: pd.DataFrame, league: str) -> pd.DataFrame:
    out: list[dict[str, Any]] = []
    for _, row in raw.iterrows():
        season = str(row.get("season"))
        if season not in SEASONS:
            continue
        opening = _valid_prices(row, ONE_X_TWO_COLUMNS)
        closing = _valid_prices(row, v1.CLOSING_1X2_COLUMNS)
        total = _valid_prices(row, TOTAL_COLUMNS)
        ah = _valid_prices(row, AH_COLUMNS)
        line_info = _first_line(row)
        if opening is None or closing is None or total is None or ah is None or line_info is None:
            continue
        line, _ = line_info
        if not _is_half_goal_line(line):
            continue
        out.append(
            {
                "league": league,
                "season": season,
                "match_date": row.get("match_date"),
                "home_team": str(row.get("HomeTeam")),
                "away_team": str(row.get("AwayTeam")),
                "ah_line": float(line),
                "open_1x2_overround": _overround(opening),
                "close_1x2_overround": _overround(closing),
                "ou25_overround": _overround(total),
                "ah_overround": _overround(ah),
            }
        )
    return pd.DataFrame(out)


def _smd(target: pd.Series, reference: pd.Series) -> float | None:
    t = target.dropna().astype(float)
    r = reference.dropna().astype(float)
    if len(t) < 2 or len(r) < 2:
        return None
    denom = float(r.std(ddof=1))
    if not np.isfinite(denom) or denom <= 1e-12:
        return None
    return float((t.mean() - r.mean()) / denom)


def _line_distribution(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {}
    counts = Counter(f"{float(x):+.1f}" for x in frame["ah_line"])
    total = sum(counts.values())
    return {key: value / total for key, value in sorted(counts.items())}


def _tv(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a) | set(b)
    return 0.5 * sum(abs(a.get(k, 0.0) - b.get(k, 0.0)) for k in keys)


def evaluate() -> dict[str, Any]:
    frames: list[pd.DataFrame] = []
    raw_market: list[pd.DataFrame] = []
    coverage: dict[str, Any] = {}
    schema: dict[str, dict[str, Any]] = {}

    for league in LEAGUES:
        raw, rows, cov = _raw_and_rows(league)
        frames.append(rows)
        raw_market.append(_raw_market_diagnostics(raw, league))
        coverage[league] = cov
        schema[league] = {}
        for season in SEASONS:
            local = raw[raw["season"].astype(str) == season]
            schema[league][season] = {
                "source_rows": int(len(local)),
                "missing_required_columns": [
                    c
                    for c in REQUIRED_COLUMNS
                    if c not in local.columns or local[c].notna().sum() == 0
                ],
            }

    combined = pd.concat(frames, ignore_index=True)
    market = pd.concat(raw_market, ignore_index=True)
    keys = ["league", "season", "match_date", "home_team", "away_team", "ah_line"]
    data = combined.merge(market, on=keys, how="left", validate="one_to_one")

    cells: dict[str, dict[str, Any]] = {}
    for league in LEAGUES:
        cells[league] = {}
        ref = data[(data["league"] == league) & data["season"].isin(REFERENCE)]
        ref_lines = _line_distribution(ref)
        for season in SEASONS:
            local = data[(data["league"] == league) & (data["season"] == season)]
            cov = coverage[league][season]
            source_rows = int(cov["source_rows"])
            reconstructed = int(cov["reconstructed_rows"])
            cell = {
                "source_rows": source_rows,
                "complete_open_close_same_book_rows": int(cov["complete_open_close_same_book_rows"]),
                "half_goal_ah_rows": int(cov["half_goal_ah_rows"]),
                "reconstructed_rows": reconstructed,
                "reconstruction_share": (reconstructed / source_rows) if source_rows else None,
                "ah_line_distribution": _line_distribution(local),
                "ah_line_tv_vs_reference": _tv(_line_distribution(local), ref_lines) if season == TARGET else None,
            }
            for metric in CONTINUOUS:
                values = local[metric].dropna().astype(float)
                cell[metric] = {
                    "mean": float(values.mean()) if len(values) else None,
                    "median": float(values.median()) if len(values) else None,
                }
                if season == TARGET:
                    cell[metric]["smd_vs_reference"] = _smd(values, ref[metric])
            cells[league][season] = cell

    shifts: dict[str, Any] = {}
    # Broad coverage shift: >=10 percentage points in at least 4/5 leagues, same sign.
    coverage_deltas = {}
    for league in LEAGUES:
        target_share = cells[league][TARGET]["reconstruction_share"]
        ref_source = sum(cells[league][s]["source_rows"] for s in REFERENCE)
        ref_rows = sum(cells[league][s]["reconstructed_rows"] for s in REFERENCE)
        ref_share = ref_rows / ref_source if ref_source else np.nan
        coverage_deltas[league] = float(target_share - ref_share)
    pos = sum(v >= 0.10 for v in coverage_deltas.values())
    neg = sum(v <= -0.10 for v in coverage_deltas.values())
    shifts["coverage"] = {
        "by_league_delta_vs_reference": coverage_deltas,
        "broad_shift": bool(max(pos, neg) >= 4),
    }

    ah_tv = {league: float(cells[league][TARGET]["ah_line_tv_vs_reference"]) for league in LEAGUES}
    shifts["ah_composition"] = {
        "tv_distance_by_league": ah_tv,
        "broad_shift": bool(sum(v >= 0.20 for v in ah_tv.values()) >= 4),
    }

    for metric in CONTINUOUS:
        smds = {
            league: cells[league][TARGET][metric]["smd_vs_reference"]
            for league in LEAGUES
        }
        usable = [v for v in smds.values() if v is not None]
        pos = sum(v >= 0.5 for v in usable)
        neg = sum(v <= -0.5 for v in usable)
        shifts[metric] = {
            "smd_by_league": smds,
            "broad_shift": bool(max(pos, neg) >= 4),
        }

    # Leave-one-league-out 2024/25 alignment diagnostic.
    target_rows = data[data["season"] == TARGET]
    loo = {}
    for league in LEAGUES:
        local = target_rows[target_rows["league"] != league]
        loo[league] = {
            "rows": int(len(local)),
            "mean_alignment_dot": float(local["alignment_dot"].mean()),
        }

    broad_families = [
        name for name, payload in shifts.items()
        if payload.get("broad_shift") is True
    ]
    schema_breaks = {
        league: cells_missing
        for league, seasons in schema.items()
        if (cells_missing := seasons[TARGET]["missing_required_columns"])
    }
    observable = bool(broad_families or schema_breaks)
    label = (
        "OBSERVABLE_SOURCE_MARKET_SHIFT_2024_25"
        if observable
        else "NO_OBSERVABLE_SOURCE_MARKET_EXPLANATION"
    )

    if observable:
        plain = (
            "В 2024/25 обнаружен широкий сдвиг хотя бы в одной заранее зафиксированной "
            f"source/market diagnostic family: {', '.join(broad_families) or 'schema'}. "
            "Это описательная диагностика и не меняет отрицательные frozen решения V1/V2."
        )
    else:
        plain = (
            "В 2024/25 не найден широкий source/schema, AH-composition, bookmaker-margin "
            "или structural-magnitude сдвиг, который одинаково проявляется минимум в 4/5 лигах. "
            "Поэтому ослабление alignment нельзя честно объяснить наблюдаемой общей сменой источника/рынка."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "POSTHOC_SOURCE_MARKET_DIAGNOSTIC",
        "posthoc": True,
        "confirmatory_support_allowed": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_model_operations": 0,
        "production_promotion": False,
        "rows": int(len(data)),
        "leagues": list(LEAGUES),
        "seasons": list(SEASONS),
        "target_season": TARGET,
        "reference_seasons": list(REFERENCE),
        "adjacent_seasons": list(ADJACENT),
        "cells": cells,
        "schema": schema,
        "large_shift_rule": {
            "continuous_abs_smd": 0.5,
            "coverage_absolute_share_delta": 0.10,
            "ah_line_total_variation": 0.20,
            "broad_league_count": 4,
        },
        "shifts": shifts,
        "broad_shift_families": broad_families,
        "schema_breaks_2024_25": schema_breaks,
        "leave_one_league_out_2024_25": loo,
        "diagnostic_label": label,
        "formal_v1_v2_decisions_unchanged": True,
        "result": "NO_BET",
        "summary": {"plain_language": plain},
    }
