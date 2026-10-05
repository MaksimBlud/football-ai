"""Deterministic OOS favourite-longshot calibration audit.

Issue #534 research-only evaluator.

Primary question:
Does a stable favourite-longshot bias exist in Football AI historical 1X2
bookmaker probabilities, and does it persist from opening to closing?

Frozen design:
- leagues: EPL, La Liga, Serie A
- bookmakers: Bet365 and Pinnacle
- no-vig transform: multiplicative/proportional normalization
- reference: 2019/20-2023/24
- validation: 2024/25
- untouched OOT: 2025/26
- primary structural statistic: slope of calibration residual (y - p) on p
- longshot aggregate: p < 0.30
- favourite aggregate: p >= 0.60
- fixed probability bins:
  [0,.20), [.20,.30), [.30,.40), [.40,.50), [.50,.60),
  [.60,.70), [.70,.80), [.80,1]

Positive residual slope means low-probability selections tend to be overestimated
and high-probability selections underestimated, i.e. the classic
favourite-longshot direction.

No paid API, Supabase write, production operation or automatic promotion.
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

EXPERIMENT_ID = "FAVOURITE_LONGSHOT_BIAS_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
HORIZONS = ("opening", "closing")
OUTCOME_ORDER = ("H", "D", "A")
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


def _outcome_index(value: Any) -> int | None:
    text = str(value).strip().upper()
    if text not in OUTCOME_ORDER:
        return None
    return OUTCOME_ORDER.index(text)


def _multiplicative(odds: tuple[float, float, float]) -> np.ndarray | None:
    arr = np.asarray(odds, dtype=float)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)) or np.any(arr <= 1.0):
        return None
    inverse = 1.0 / arr
    total = float(inverse.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    p = inverse / total
    if np.any(p <= 0.0) or np.any(p >= 1.0):
        return None
    return p


def _bin_label(probability: float) -> str | None:
    p = float(probability)
    for left, right, label in BINS:
        if left <= p < right:
            return label
    return None


def _wilson_interval(wins: int, total: int, z: float = 1.959963984540054) -> tuple[float | None, float | None]:
    if total <= 0:
        return None, None
    phat = wins / total
    denom = 1.0 + z * z / total
    centre = (phat + z * z / (2.0 * total)) / denom
    half = (
        z
        * math.sqrt(
            (phat * (1.0 - phat) / total) + (z * z / (4.0 * total * total))
        )
        / denom
    )
    return max(0.0, centre - half), min(1.0, centre + half)


def _residual_slope(frame: pd.DataFrame) -> float | None:
    if len(frame) < 2:
        return None
    x = frame["probability"].to_numpy(dtype=float)
    r = frame["calibration_residual"].to_numpy(dtype=float)
    variance = float(np.sum((x - x.mean()) ** 2))
    if variance <= 0.0:
        return None
    return float(np.sum((x - x.mean()) * (r - r.mean())) / variance)


def _fixture_sufficient_statistics(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame(
            columns=["league", "fixture_key", "n", "sx", "sr", "sx2", "sxr"]
        )
    data = frame.copy()
    data["x2"] = data["probability"] ** 2
    data["xr"] = data["probability"] * data["calibration_residual"]
    return (
        data.groupby(["league", "fixture_key"], as_index=False)
        .agg(
            n=("probability", "size"),
            sx=("probability", "sum"),
            sr=("calibration_residual", "sum"),
            sx2=("x2", "sum"),
            sxr=("xr", "sum"),
        )
        .reset_index(drop=True)
    )


def _slope_from_sufficient(stats: np.ndarray) -> float | None:
    # columns: n, sx, sr, sx2, sxr
    totals = stats.sum(axis=0)
    n, sx, sr, sx2, sxr = [float(value) for value in totals]
    if n <= 1:
        return None
    denominator = sx2 - sx * sx / n
    if denominator <= 0.0:
        return None
    numerator = sxr - sx * sr / n
    return numerator / denominator


def _slope_bootstrap(frame: pd.DataFrame) -> dict[str, Any]:
    point = _residual_slope(frame)
    grouped = _fixture_sufficient_statistics(frame)
    if point is None or grouped.empty:
        return {
            "draws": BOOTSTRAP_DRAWS,
            "slope": point,
            "ci95_low": None,
            "ci95_high": None,
        }

    rng = np.random.default_rng(SEED)
    arrays: dict[str, np.ndarray] = {}
    for league, part in grouped.groupby("league"):
        arrays[league] = part[["n", "sx", "sr", "sx2", "sxr"]].to_numpy(dtype=float)

    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    valid = np.ones(BOOTSTRAP_DRAWS, dtype=bool)
    for draw in range(BOOTSTRAP_DRAWS):
        pieces: list[np.ndarray] = []
        for values in arrays.values():
            idx = rng.integers(0, len(values), size=len(values))
            pieces.append(values[idx])
        slope = _slope_from_sufficient(np.concatenate(pieces, axis=0))
        if slope is None or not math.isfinite(slope):
            valid[draw] = False
            draws[draw] = np.nan
        else:
            draws[draw] = slope

    good = draws[valid]
    return {
        "draws": BOOTSTRAP_DRAWS,
        "valid_draws": int(len(good)),
        "slope": point,
        "ci95_low": float(np.quantile(good, 0.025)) if len(good) else None,
        "ci95_high": float(np.quantile(good, 0.975)) if len(good) else None,
    }


def _bin_report(frame: pd.DataFrame) -> list[dict[str, Any]]:
    reports: list[dict[str, Any]] = []
    for left, right, label in BINS:
        part = frame[(frame["probability"] >= left) & (frame["probability"] < right)]
        n = int(len(part))
        wins = int(part["won"].sum()) if n else 0
        mean_p = float(part["probability"].mean()) if n else None
        win_rate = float(part["won"].mean()) if n else None
        ci_low, ci_high = _wilson_interval(wins, n)
        gap = (win_rate - mean_p) if n and mean_p is not None else None
        reports.append(
            {
                "bin": label,
                "left_inclusive": left,
                "right_exclusive": right,
                "rows": n,
                "wins": wins,
                "mean_implied_probability": mean_p,
                "realized_frequency": win_rate,
                "frequency_ci95_low": ci_low,
                "frequency_ci95_high": ci_high,
                "calibration_gap_realized_minus_implied": gap,
                "gap_ci95_low_approx": (
                    ci_low - mean_p if ci_low is not None and mean_p is not None else None
                ),
                "gap_ci95_high_approx": (
                    ci_high - mean_p if ci_high is not None and mean_p is not None else None
                ),
                "average_raw_odds": float(part["raw_odds"].mean()) if n else None,
                "flat_stake_return": float(part["flat_return"].mean()) if n else None,
            }
        )
    return reports


def _aggregate_regions(frame: pd.DataFrame) -> dict[str, Any]:
    def report(part: pd.DataFrame) -> dict[str, Any]:
        if part.empty:
            return {"rows": 0, "mean_p": None, "win_rate": None, "gap": None}
        mean_p = float(part["probability"].mean())
        win_rate = float(part["won"].mean())
        return {
            "rows": int(len(part)),
            "mean_p": mean_p,
            "win_rate": win_rate,
            "gap": win_rate - mean_p,
            "flat_stake_return": float(part["flat_return"].mean()),
        }

    return {
        "longshot_p_lt_0_30": report(frame[frame["probability"] < 0.30]),
        "favourite_p_ge_0_60": report(frame[frame["probability"] >= 0.60]),
    }


def _simple_group_diagnostics(frame: pd.DataFrame, column: str) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for value, part in frame.groupby(column):
        out[str(value)] = {
            "rows": int(len(part)),
            "residual_slope": _residual_slope(part),
            "mean_calibration_gap": float(part["calibration_residual"].mean()),
        }
    return out


def _horizon_report(frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "rows": int(len(frame)),
        "fixtures": int(frame["fixture_key"].nunique()) if len(frame) else 0,
        "residual_slope": _slope_bootstrap(frame),
        "regions": _aggregate_regions(frame),
        "bins": _bin_report(frame),
        "by_bookmaker": _simple_group_diagnostics(frame, "bookmaker"),
        "by_league": _simple_group_diagnostics(frame, "league"),
        "by_outcome_type": _simple_group_diagnostics(frame, "outcome_type"),
    }


def _time_path(opening: dict[str, Any], closing: dict[str, Any]) -> dict[str, Any]:
    o = opening["residual_slope"]
    c = closing["residual_slope"]
    o_supported = (
        o["slope"] is not None
        and o["slope"] > 0.0
        and o["ci95_low"] is not None
        and o["ci95_low"] > 0.0
    )
    c_supported = (
        c["slope"] is not None
        and c["slope"] > 0.0
        and c["ci95_low"] is not None
        and c["ci95_low"] > 0.0
    )

    if o_supported and c_supported:
        if c["slope"] < o["slope"]:
            label = "BIAS_PERSISTS_BUT_REDUCES_BY_CLOSE"
        elif c["slope"] > o["slope"]:
            label = "BIAS_PERSISTS_AND_AMPLIFIES_BY_CLOSE"
        else:
            label = "BIAS_PERSISTS_UNCHANGED"
    elif o_supported and not c_supported:
        label = "OPENING_ONLY_BIAS_NOT_CONFIRMED_AT_CLOSE"
    elif (not o_supported) and c_supported:
        label = "CLOSING_ONLY_BIAS"
    else:
        label = "NO_CLEAR_TIME_PATH"

    return {
        "classification": label,
        "opening_supported": o_supported,
        "closing_supported": c_supported,
        "opening_slope": o["slope"],
        "closing_slope": c["slope"],
        "closing_minus_opening_slope": (
            c["slope"] - o["slope"]
            if c["slope"] is not None and o["slope"] is not None
            else None
        ),
    }


def _split_name(season: str) -> str | None:
    if season in REFERENCE:
        return "reference"
    if season == VALIDATION:
        return "validation"
    if season == TEST:
        return "test"
    return None


def _download_and_audit() -> tuple[
    dict[tuple[str, str], bytes],
    dict[str, Any],
    list[str],
]:
    payloads: dict[tuple[str, str], bytes] = {}
    source_files: dict[str, Any] = {}
    eligible = {bookmaker: True for bookmaker in BOOKMAKERS}
    original_get = requests.get
    try:
        requests.get = _official_or_pinned_mirror_get
        for league in LEAGUE_ORDER:
            config = LEAGUES[league]
            for code, season in config.historical_source.season_codes.items():
                if season not in ALLOWED:
                    continue
                url = BASE.format(
                    code=code,
                    comp=config.historical_source.competition_code,
                )
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                payload = response.content
                payloads[(league, season)] = payload
                header = pd.read_csv(BytesIO(payload), nrows=0)
                columns = set(header.columns)
                info: dict[str, Any] = {"bookmakers": {}}
                for bookmaker, horizon_map in BOOKMAKERS.items():
                    missing: list[str] = []
                    for cols in horizon_map.values():
                        missing.extend(sorted(set(cols) - columns))
                    info["bookmakers"][bookmaker] = {
                        "missing_required_columns": sorted(set(missing))
                    }
                    if season in {VALIDATION, TEST} and missing:
                        eligible[bookmaker] = False
                source_files[f"{league}:{season}"] = info
    finally:
        requests.get = original_get

    included = [bookmaker for bookmaker, ok in eligible.items() if ok]
    audit = {
        "outcome_read_before_audit": False,
        "candidate_bookmakers": list(BOOKMAKERS),
        "included_bookmakers": included,
        "excluded_bookmakers": [
            bookmaker for bookmaker in BOOKMAKERS if bookmaker not in included
        ],
        "source_files": source_files,
        "validation_test_column_gate_passed": len(included) >= 2,
        "intraday_snapshot_gaps": {
            "24h": "No exact timestamped 24h snapshot in frozen Football-Data source.",
            "6h": "No exact timestamped 6h snapshot in frozen Football-Data source.",
            "1h": "No exact timestamped 1h snapshot in frozen Football-Data source.",
        },
    }
    return payloads, audit, included


def _build_rows(
    payloads: dict[tuple[str, str], bytes],
    included_bookmakers: list[str],
) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for (league, season), payload in sorted(payloads.items()):
        split = _split_name(season)
        if split is None:
            continue
        required = {"Date", "HomeTeam", "AwayTeam", "FTR"}
        for bookmaker in included_bookmakers:
            for columns in BOOKMAKERS[bookmaker].values():
                required.update(columns)

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
            for bookmaker in included_bookmakers:
                for horizon in HORIZONS:
                    cols = BOOKMAKERS[bookmaker][horizon]
                    try:
                        odds = tuple(float(row.get(col)) for col in cols)
                    except (TypeError, ValueError):
                        continue
                    probabilities = _multiplicative(odds)
                    if probabilities is None:
                        continue
                    for outcome_idx, outcome_type in enumerate(OUTCOME_ORDER):
                        p = float(probabilities[outcome_idx])
                        won = int(outcome_index == outcome_idx)
                        raw_odds = float(odds[outcome_idx])
                        records.append(
                            {
                                "league": league,
                                "season": season,
                                "split": split,
                                "fixture_key": fixture_key,
                                "bookmaker": bookmaker,
                                "horizon": horizon,
                                "outcome_type": outcome_type,
                                "probability": p,
                                "won": won,
                                "calibration_residual": won - p,
                                "raw_odds": raw_odds,
                                "flat_return": (raw_odds - 1.0) if won else -1.0,
                                "bin": _bin_label(p),
                            }
                        )
    return pd.DataFrame(records)


def _formal_gate(validation: dict[str, Any], test: dict[str, Any]) -> dict[str, Any]:
    v_close = validation["closing"]
    t_close = test["closing"]

    def robust_positive(report: dict[str, Any]) -> bool:
        slope = report["residual_slope"]
        return bool(
            slope["slope"] is not None
            and slope["slope"] > 0.0
            and slope["ci95_low"] is not None
            and slope["ci95_low"] > 0.0
        )

    def region_direction(report: dict[str, Any]) -> bool:
        regions = report["regions"]
        long_gap = regions["longshot_p_lt_0_30"]["gap"]
        fav_gap = regions["favourite_p_ge_0_60"]["gap"]
        return bool(
            long_gap is not None
            and long_gap < 0.0
            and fav_gap is not None
            and fav_gap > 0.0
        )

    bookmaker_slopes = [
        payload["residual_slope"]
        for payload in t_close["by_bookmaker"].values()
        if payload["residual_slope"] is not None
    ]
    league_slopes = [
        payload["residual_slope"]
        for payload in t_close["by_league"].values()
        if payload["residual_slope"] is not None
    ]

    gates = {
        "validation_closing_slope_ci_above_zero": robust_positive(v_close),
        "test_closing_slope_ci_above_zero": robust_positive(t_close),
        "validation_longshot_negative_favourite_positive": region_direction(v_close),
        "test_longshot_negative_favourite_positive": region_direction(t_close),
        "both_bookmakers_positive_test_slope": (
            len(bookmaker_slopes) >= 2 and all(value > 0.0 for value in bookmaker_slopes)
        ),
        "at_least_two_leagues_positive_test_slope": (
            sum(value > 0.0 for value in league_slopes) >= 2
        ),
    }
    return {"supported": all(gates.values()), "gates": gates}


def _season_diagnostics(rows: pd.DataFrame) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for season, season_frame in rows.groupby("season"):
        out[season] = {}
        for horizon in HORIZONS:
            part = season_frame[season_frame["horizon"] == horizon]
            out[season][horizon] = {
                "rows": int(len(part)),
                "residual_slope": _residual_slope(part),
                "regions": _aggregate_regions(part),
            }
    return out


def _source_gap_result(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_FAVOURITE_LONGSHOT_CALIBRATION",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "source_audit": audit,
        "reference": {},
        "validation": {},
        "test": {},
        "season_diagnostics": {},
        "formal_gate": {"supported": False, "gates": {}, "reason": reason},
        "supported": False,
        "decision": "BLOCKED_BY_SOURCE_GAP",
        "interpretation_guard": (
            "The frozen paired multi-bookmaker source contract was unavailable. "
            "No paid source, proxy or interpolated intraday snapshot was substituted."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, included_bookmakers = _download_and_audit()
    if len(included_bookmakers) < 2:
        return _source_gap_result(
            audit,
            "FEWER_THAN_TWO_FROZEN_BOOKMAKERS_HAVE_VALIDATION_TEST_COVERAGE",
        )

    rows = _build_rows(payloads, included_bookmakers)
    if rows.empty:
        return _source_gap_result(audit, "NO_VALID_1X2_SELECTION_ROWS")

    reports: dict[str, Any] = {}
    for split in ("reference", "validation", "test"):
        reports[split] = {}
        for horizon in HORIZONS:
            part = rows[
                (rows["split"] == split) & (rows["horizon"] == horizon)
            ].copy()
            reports[split][horizon] = _horizon_report(part)
        reports[split]["time_path"] = _time_path(
            reports[split]["opening"], reports[split]["closing"]
        )

    gate = _formal_gate(reports["validation"], reports["test"])
    supported = bool(gate["supported"])
    decision = (
        "STABLE_FAVOURITE_LONGSHOT_BIAS"
        if supported
        else "NO_STABLE_FAVOURITE_LONGSHOT_BIAS"
    )

    if supported:
        interpretation = (
            "The preregistered favourite-longshot direction is stable on both "
            "validation and untouched OOT closing prices: low-probability outcomes "
            "are overestimated relative to realized frequency and high-probability "
            "outcomes underestimated, with a positive calibration-residual slope "
            "whose cluster-bootstrap interval stays above zero. This is research "
            "evidence about calibration, not an automatic betting edge."
        )
    else:
        interpretation = (
            "The frozen favourite-longshot pattern did not clear every stability "
            "gate on validation and untouched OOT data. Bin-level deviations may "
            "still exist descriptively, but they must not be converted into a live "
            "probability correction or betting rule from this sample."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_FAVOURITE_LONGSHOT_CALIBRATION",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "primary_devig": "multiplicative",
        "probability_bins": [
            {
                "left_inclusive": left,
                "right_exclusive": right,
                "label": label,
            }
            for left, right, label in BINS
        ],
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "untouched_test": TEST,
            "primary_horizons": list(HORIZONS),
            "intraday_24h_6h_1h": "SOURCE_GAP_NO_EXACT_TIMESTAMPED_SNAPSHOTS",
        },
        "source_audit": {**audit, "outcome_read_after_audit": True},
        "reference": reports["reference"],
        "validation": reports["validation"],
        "test": reports["test"],
        "season_diagnostics": _season_diagnostics(rows),
        "formal_gate": gate,
        "supported": supported,
        "decision": decision,
        "interpretation_guard": interpretation,
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
