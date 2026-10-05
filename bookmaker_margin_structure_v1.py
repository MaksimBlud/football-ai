"""Deterministic matched-fixture bookmaker margin/allocation audit.

Research-only evaluator for Issue #535.

The primary question is not merely whether one bookmaker has a larger total
overround. It is whether, after removing each bookmaker's total overround, the
remaining allocation across favourite / middle / longshot outcomes differs
systematically between Bet365 and Pinnacle on the SAME fixtures.

Primary external consensus is the Football-Data market-average 1X2 price vector
(AvgH/AvgD/AvgA and closing AvgCH/AvgCD/AvgCA), multiplicatively de-vigged.
A secondary sensitivity consensus is the simple mean of the two bookmaker
de-vigged fair-probability vectors.

No paid API, Supabase write, production operation, betting action or automatic
promotion is performed.
"""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import requests

from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from historical_football_signal_runner import BASE, LEAGUES

EXPERIMENT_ID = "BOOKMAKER_MARGIN_STRUCTURE_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
HORIZONS = ("opening", "closing")
OUTCOME_ORDER = ("H", "D", "A")
BOOK_ORDER = ("BET365", "PINNACLE")
BOOTSTRAP_DRAWS = 5000
SEED = 20261005

BOOKMAKERS = {
    "BET365": {
        "opening": ("B365H", "B365D", "B365A"),
        "closing": ("B365CH", "B365CD", "B365CA"),
    },
    "PINNACLE": {
        "opening": ("PSH", "PSD", "PSA"),
        "closing": ("PSCH", "PSCD", "PSCA"),
    },
}
CONSENSUS = {
    "opening": ("AvgH", "AvgD", "AvgA"),
    "closing": ("AvgCH", "AvgCD", "AvgCA"),
}
BINS = (
    (0.00, 0.20, "0-20%"),
    (0.20, 0.30, "20-30%"),
    (0.30, 0.40, "30-40%"),
    (0.40, 0.50, "40-50%"),
    (0.50, 0.60, "50-60%"),
    (0.60, 0.70, "60-70%"),
    (0.70, 0.80, "70-80%"),
    (0.80, 1.01, "80%+"),
)


def _inverse(odds: tuple[float, float, float]) -> np.ndarray | None:
    arr = np.asarray(odds, dtype=float)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)) or np.any(arr <= 1.0):
        return None
    return 1.0 / arr


def _multiplicative(odds: tuple[float, float, float]) -> np.ndarray | None:
    q = _inverse(odds)
    if q is None:
        return None
    total = float(q.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    p = q / total
    if np.any(p <= 0.0) or np.any(p >= 1.0):
        return None
    return p


def _allocation_tilt(
    odds: tuple[float, float, float], consensus_p: np.ndarray
) -> tuple[np.ndarray, float, np.ndarray] | None:
    q = _inverse(odds)
    if q is None:
        return None
    consensus_p = np.asarray(consensus_p, dtype=float)
    if (
        consensus_p.shape != (3,)
        or not np.all(np.isfinite(consensus_p))
        or np.any(consensus_p <= 0.0)
        or abs(float(consensus_p.sum()) - 1.0) > 1e-8
    ):
        return None
    implied_sum = float(q.sum())
    if implied_sum <= 0.0:
        return None
    expected_uniform = consensus_p * implied_sum
    tilt = q / expected_uniform - 1.0
    fair = q / implied_sum
    return tilt, implied_sum - 1.0, fair


def _rank_indices(consensus_p: np.ndarray) -> tuple[int, int, int]:
    order = np.argsort(np.asarray(consensus_p, dtype=float))
    longshot = int(order[0])
    middle = int(order[1])
    favourite = int(order[2])
    return favourite, middle, longshot


def _outcome_index(value: Any) -> int | None:
    text = str(value).strip().upper()
    return OUTCOME_ORDER.index(text) if text in OUTCOME_ORDER else None


def _split_name(season: str) -> str | None:
    if season in REFERENCE:
        return "reference"
    if season == VALIDATION:
        return "validation"
    if season == TEST:
        return "test"
    return None


def _bin_label(probability: float) -> str | None:
    p = float(probability)
    for left, right, label in BINS:
        if left <= p < right:
            return label
    return None


def _download_and_audit() -> tuple[
    dict[tuple[str, str], bytes], dict[str, Any], bool
]:
    payloads: dict[tuple[str, str], bytes] = {}
    source_files: dict[str, Any] = {}
    gate = True
    original_get = requests.get
    try:
        requests.get = _official_or_pinned_mirror_get
        for league in LEAGUE_ORDER:
            config = LEAGUES[league]
            for code, season in config.historical_source.season_codes.items():
                if season not in ALLOWED:
                    continue
                url = BASE.format(
                    code=code, comp=config.historical_source.competition_code
                )
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                payload = response.content
                payloads[(league, season)] = payload
                columns = set(pd.read_csv(BytesIO(payload), nrows=0).columns)
                required: set[str] = set()
                for bookmaker in BOOK_ORDER:
                    for horizon in HORIZONS:
                        required.update(BOOKMAKERS[bookmaker][horizon])
                for horizon in HORIZONS:
                    required.update(CONSENSUS[horizon])
                missing = sorted(required - columns)
                if season in {VALIDATION, TEST} and missing:
                    gate = False
                source_files[f"{league}:{season}"] = {
                    "missing_required_price_columns": missing,
                    "has_outcome_column": "FTR" in columns,
                }
    finally:
        requests.get = original_get

    audit = {
        "outcome_read_before_audit": False,
        "frozen_bookmakers": list(BOOK_ORDER),
        "external_consensus": "Football-Data Avg 1X2 columns",
        "source_files": source_files,
        "validation_test_column_gate_passed": gate,
        "intraday_snapshot_gaps": {
            "24h": "No exact timestamped 24h snapshot in frozen source.",
            "6h": "No exact timestamped 6h snapshot in frozen source.",
            "1h": "No exact timestamped 1h snapshot in frozen source.",
        },
    }
    return payloads, audit, gate


def _build_rows(
    payloads: dict[tuple[str, str], bytes]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixture_records: list[dict[str, Any]] = []
    selection_records: list[dict[str, Any]] = []

    for (league, season), payload in sorted(payloads.items()):
        split = _split_name(season)
        if split is None:
            continue

        required = {"Date", "HomeTeam", "AwayTeam", "FTR"}
        for bookmaker in BOOK_ORDER:
            for horizon in HORIZONS:
                required.update(BOOKMAKERS[bookmaker][horizon])
        for horizon in HORIZONS:
            required.update(CONSENSUS[horizon])

        frame = pd.read_csv(BytesIO(payload), usecols=lambda col: col in required)

        for source_row, row in frame.iterrows():
            outcome_index = _outcome_index(row.get("FTR"))
            if outcome_index is None:
                continue
            fixture_key = (
                f"{league}|{season}|{source_row}|"
                f"{str(row.get('HomeTeam', '')).strip()}|"
                f"{str(row.get('AwayTeam', '')).strip()}"
            )

            for horizon in HORIZONS:
                try:
                    consensus_odds = tuple(
                        float(row.get(col)) for col in CONSENSUS[horizon]
                    )
                except (TypeError, ValueError):
                    continue
                consensus_p = _multiplicative(consensus_odds)
                if consensus_p is None:
                    continue

                book_data: dict[str, dict[str, Any]] = {}
                valid_pair = True
                for bookmaker in BOOK_ORDER:
                    cols = BOOKMAKERS[bookmaker][horizon]
                    try:
                        odds = tuple(float(row.get(col)) for col in cols)
                    except (TypeError, ValueError):
                        valid_pair = False
                        break
                    primary = _allocation_tilt(odds, consensus_p)
                    fair = _multiplicative(odds)
                    if primary is None or fair is None:
                        valid_pair = False
                        break
                    tilt, overround, book_fair = primary
                    book_data[bookmaker] = {
                        "odds": odds,
                        "tilt": tilt,
                        "overround": overround,
                        "fair": book_fair,
                    }
                if not valid_pair:
                    continue

                alt_consensus = (
                    book_data["BET365"]["fair"] + book_data["PINNACLE"]["fair"]
                ) / 2.0
                favourite, middle, longshot = _rank_indices(consensus_p)

                for bookmaker in BOOK_ORDER:
                    data = book_data[bookmaker]
                    alt = _allocation_tilt(data["odds"], alt_consensus)
                    if alt is None:
                        continue
                    alt_tilt, _, _ = alt
                    tilt = data["tilt"]
                    fixture_records.append(
                        {
                            "league": league,
                            "season": season,
                            "split": split,
                            "fixture_key": fixture_key,
                            "horizon": horizon,
                            "bookmaker": bookmaker,
                            "overround": float(data["overround"]),
                            "fair_tv_vs_market_consensus": float(
                                0.5
                                * np.abs(
                                    data["fair"] - consensus_p
                                ).sum()
                            ),
                            "fl_allocation_contrast": float(
                                tilt[longshot] - tilt[favourite]
                            ),
                            "draw_allocation_tilt": float(tilt[1]),
                            "favourite_allocation_tilt": float(tilt[favourite]),
                            "longshot_allocation_tilt": float(tilt[longshot]),
                            "alt_fl_allocation_contrast": float(
                                alt_tilt[longshot] - alt_tilt[favourite]
                            ),
                        }
                    )
                    for idx, outcome_type in enumerate(OUTCOME_ORDER):
                        raw_odds = float(data["odds"][idx])
                        won = int(outcome_index == idx)
                        if idx == favourite:
                            rank = "FAVOURITE"
                        elif idx == longshot:
                            rank = "LONGSHOT"
                        else:
                            rank = "MIDDLE"
                        selection_records.append(
                            {
                                "league": league,
                                "season": season,
                                "split": split,
                                "fixture_key": fixture_key,
                                "horizon": horizon,
                                "bookmaker": bookmaker,
                                "outcome_type": outcome_type,
                                "rank": rank,
                                "consensus_probability": float(consensus_p[idx]),
                                "bin": _bin_label(float(consensus_p[idx])),
                                "raw_odds": raw_odds,
                                "won": won,
                                "flat_return": (raw_odds - 1.0) if won else -1.0,
                                "allocation_tilt": float(tilt[idx]),
                            }
                        )

    return pd.DataFrame(fixture_records), pd.DataFrame(selection_records)


def _paired_metric(frame: pd.DataFrame, metric: str) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(columns=["league", "fixture_key", "delta"])
    pivot = frame.pivot_table(
        index=["league", "fixture_key"],
        columns="bookmaker",
        values=metric,
        aggfunc="first",
    ).reset_index()
    if not all(book in pivot.columns for book in BOOK_ORDER):
        return pd.DataFrame(columns=["league", "fixture_key", "delta"])
    pivot = pivot.dropna(subset=list(BOOK_ORDER))
    pivot["delta"] = pivot["BET365"] - pivot["PINNACLE"]
    return pivot[["league", "fixture_key", "delta"]]


def _bootstrap_delta(frame: pd.DataFrame, metric: str) -> dict[str, Any]:
    paired = _paired_metric(frame, metric)
    if paired.empty:
        return {
            "rows": 0,
            "mean_delta_bet365_minus_pinnacle": None,
            "ci95_low": None,
            "ci95_high": None,
            "draws": BOOTSTRAP_DRAWS,
        }
    rng = np.random.default_rng(SEED)
    groups = {
        league: part["delta"].to_numpy(dtype=float)
        for league, part in paired.groupby("league")
    }
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for i in range(BOOTSTRAP_DRAWS):
        sampled: list[np.ndarray] = []
        for values in groups.values():
            idx = rng.integers(0, len(values), size=len(values))
            sampled.append(values[idx])
        draws[i] = float(np.concatenate(sampled).mean())
    return {
        "rows": int(len(paired)),
        "mean_delta_bet365_minus_pinnacle": float(paired["delta"].mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "draws": BOOTSTRAP_DRAWS,
    }


def _league_deltas(frame: pd.DataFrame, metric: str) -> dict[str, float | None]:
    paired = _paired_metric(frame, metric)
    out: dict[str, float | None] = {}
    for league in LEAGUE_ORDER:
        part = paired[paired["league"] == league]
        out[league] = float(part["delta"].mean()) if len(part) else None
    return out


def _book_summary(frame: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for bookmaker in BOOK_ORDER:
        part = frame[frame["bookmaker"] == bookmaker]
        out[bookmaker] = {
            "rows": int(len(part)),
            "mean_overround": float(part["overround"].mean()) if len(part) else None,
            "mean_fl_allocation_contrast": (
                float(part["fl_allocation_contrast"].mean()) if len(part) else None
            ),
            "mean_draw_allocation_tilt": (
                float(part["draw_allocation_tilt"].mean()) if len(part) else None
            ),
            "mean_fair_tv_vs_market_consensus": (
                float(part["fair_tv_vs_market_consensus"].mean())
                if len(part)
                else None
            ),
        }
    return out


def _economic_bins(selections: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for bookmaker in BOOK_ORDER:
        part = selections[selections["bookmaker"] == bookmaker]
        rows: list[dict[str, Any]] = []
        for _, _, label in BINS:
            bucket = part[part["bin"] == label]
            rows.append(
                {
                    "bin": label,
                    "rows": int(len(bucket)),
                    "mean_consensus_probability": (
                        float(bucket["consensus_probability"].mean())
                        if len(bucket)
                        else None
                    ),
                    "flat_stake_return": (
                        float(bucket["flat_return"].mean()) if len(bucket) else None
                    ),
                    "mean_allocation_tilt": (
                        float(bucket["allocation_tilt"].mean())
                        if len(bucket)
                        else None
                    ),
                }
            )
        out[bookmaker] = rows
    return out


def _draw_report(selections: pd.DataFrame) -> dict[str, Any]:
    draws = selections[selections["outcome_type"] == "D"]
    out: dict[str, Any] = {}
    for bookmaker in BOOK_ORDER:
        part = draws[draws["bookmaker"] == bookmaker]
        out[bookmaker] = {
            "rows": int(len(part)),
            "mean_allocation_tilt": (
                float(part["allocation_tilt"].mean()) if len(part) else None
            ),
            "flat_stake_return": (
                float(part["flat_return"].mean()) if len(part) else None
            ),
        }
    return out


def _horizon_report(
    fixture_rows: pd.DataFrame, selections: pd.DataFrame
) -> dict[str, Any]:
    metrics = (
        "overround",
        "fl_allocation_contrast",
        "draw_allocation_tilt",
        "alt_fl_allocation_contrast",
    )
    return {
        "fixtures": int(fixture_rows["fixture_key"].nunique())
        if len(fixture_rows)
        else 0,
        "book_summary": _book_summary(fixture_rows),
        "paired": {
            metric: _bootstrap_delta(fixture_rows, metric) for metric in metrics
        },
        "by_league": {
            metric: _league_deltas(fixture_rows, metric) for metric in metrics
        },
        "draw_specific": _draw_report(selections),
        "economic_bins": _economic_bins(selections),
    }


def _same_nonzero_sign(a: float | None, b: float | None) -> bool:
    if a is None or b is None or a == 0.0 or b == 0.0:
        return False
    return (a > 0.0) == (b > 0.0)


def _ci_excludes_zero(report: dict[str, Any]) -> bool:
    low, high = report["ci95_low"], report["ci95_high"]
    if low is None or high is None:
        return False
    return bool(low > 0.0 or high < 0.0)


def _formal_gate(validation: dict[str, Any], test: dict[str, Any]) -> dict[str, Any]:
    v = validation["closing"]["paired"]["fl_allocation_contrast"]
    t = test["closing"]["paired"]["fl_allocation_contrast"]
    t_alt = test["closing"]["paired"]["alt_fl_allocation_contrast"]
    opening = test["opening"]["paired"]["fl_allocation_contrast"]

    v_mean = v["mean_delta_bet365_minus_pinnacle"]
    t_mean = t["mean_delta_bet365_minus_pinnacle"]
    alt_mean = t_alt["mean_delta_bet365_minus_pinnacle"]
    opening_mean = opening["mean_delta_bet365_minus_pinnacle"]

    league_values = [
        value
        for value in test["closing"]["by_league"][
            "fl_allocation_contrast"
        ].values()
        if value is not None and t_mean is not None
    ]
    matching_leagues = sum(
        _same_nonzero_sign(value, t_mean) for value in league_values
    )

    gates = {
        "validation_allocation_ci_excludes_zero": _ci_excludes_zero(v),
        "oot_allocation_ci_excludes_zero": _ci_excludes_zero(t),
        "validation_and_oot_same_sign": _same_nonzero_sign(v_mean, t_mean),
        "opening_and_closing_oot_same_sign": _same_nonzero_sign(
            opening_mean, t_mean
        ),
        "alternate_consensus_oot_ci_excludes_zero": _ci_excludes_zero(t_alt),
        "alternate_consensus_same_sign": _same_nonzero_sign(alt_mean, t_mean),
        "at_least_two_leagues_same_oot_sign": matching_leagues >= 2,
    }
    return {
        "supported": all(gates.values()),
        "gates": gates,
        "matching_oot_leagues": matching_leagues,
    }


def _source_gap_result(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_BOOKMAKER_MARGIN_STRUCTURE",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "source_audit": audit,
        "reference": {},
        "validation": {},
        "test": {},
        "formal_gate": {"supported": False, "gates": {}, "reason": reason},
        "supported": False,
        "decision": "BLOCKED_BY_SOURCE_GAP",
        "interpretation_guard": (
            "The frozen same-fixture bookmaker/market-consensus source contract "
            "was unavailable. No proxy, paid source, or interpolated snapshot was used."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = _download_and_audit()
    if not source_gate:
        return _source_gap_result(
            audit, "MISSING_FROZEN_BOOKMAKER_OR_CONSENSUS_COLUMNS"
        )

    fixtures, selections = _build_rows(payloads)
    if fixtures.empty or selections.empty:
        return _source_gap_result(audit, "NO_VALID_MATCHED_FIXTURE_ROWS")

    reports: dict[str, Any] = {}
    for split in ("reference", "validation", "test"):
        reports[split] = {}
        for horizon in HORIZONS:
            f = fixtures[
                (fixtures["split"] == split)
                & (fixtures["horizon"] == horizon)
            ].copy()
            s = selections[
                (selections["split"] == split)
                & (selections["horizon"] == horizon)
            ].copy()
            reports[split][horizon] = _horizon_report(f, s)

    gate = _formal_gate(reports["validation"], reports["test"])
    supported = bool(gate["supported"])
    decision = (
        "SUPPORTED_BOOKMAKER_MARGIN_HETEROGENEITY"
        if supported
        else "NO_STABLE_BOOKMAKER_MARGIN_HETEROGENEITY"
    )
    if supported:
        interpretation = (
            "Bet365 and Pinnacle show a stable same-fixture difference in how "
            "1X2 margin is allocated between longshots and favourites after each "
            "bookmaker's total overround is removed. The pattern transfers from "
            "validation to untouched OOT, survives an alternate consensus, and is "
            "not merely a total-margin difference. This is observational market-"
            "structure evidence only, not a causal claim or betting edge."
        )
    else:
        interpretation = (
            "The frozen same-fixture comparison did not clear every stability "
            "gate for bookmaker-specific margin allocation. Total overround, draw "
            "pricing, and historical return differences remain descriptive only "
            "and must not be converted into bookmaker weights or a betting rule."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_BOOKMAKER_MARGIN_STRUCTURE",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "primary_pair": "BET365_MINUS_PINNACLE",
        "allocation_measure": (
            "q_i / (market_consensus_p_i * bookmaker_implied_sum) - 1"
        ),
        "primary_allocation_contrast": (
            "longshot_allocation_tilt - favourite_allocation_tilt"
        ),
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "untouched_test": TEST,
            "primary_horizon": "closing",
            "opening_sensitivity": True,
            "intraday_24h_6h_1h": "SOURCE_GAP_NO_EXACT_TIMESTAMPED_SNAPSHOTS",
        },
        "source_audit": {**audit, "outcome_read_after_audit": True},
        "reference": reports["reference"],
        "validation": reports["validation"],
        "test": reports["test"],
        "formal_gate": gate,
        "supported": supported,
        "decision": decision,
        "interpretation_guard": interpretation,
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
