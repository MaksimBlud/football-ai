"""Deterministic decomposition of 1X2 opening-to-closing price movement.

Issue #532 research-only evaluator.

For each matched fixture:
- COMMON_MOVE = market-average fair close - market-average fair open
- BOOK_RESIDUAL_OPEN = bookmaker fair open - market fair open
- BOOK_RESIDUAL_CLOSE = bookmaker fair close - market fair close
- BOOK_SPECIFIC_MOVE = residual close - residual open
- OVERROUND_MOVE = bookmaker overround close - bookmaker overround open

The external consensus is the Football-Data market-average 1X2 vector
(AvgH/AvgD/AvgA and AvgCH/AvgCD/AvgCA), multiplicatively de-vigged.
Frozen books are Bet365 and Pinnacle.

This is an observational decomposition only. It cannot identify bettor flow,
bookmaker liabilities, risk appetite or intent.
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

EXPERIMENT_ID = "BOOKMAKER_PRICE_FORMATION_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
BOOK_ORDER = ("BET365", "PINNACLE")
OUTCOME_ORDER = ("H", "D", "A")
BOOTSTRAP_DRAWS = 5000
SEED = 20261005
MIN_SPECIFIC_ENERGY_SHARE = 0.05
MAX_MARGIN_EXPLANATION_CORR = 0.80

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


def _overround(odds: tuple[float, float, float]) -> float | None:
    q = _inverse(odds)
    if q is None:
        return None
    return float(q.sum() - 1.0)


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


def _safe_pearson(x: np.ndarray, y: np.ndarray) -> float | None:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 3 or len(y) != len(x):
        return None
    if float(np.std(x)) <= 1e-15 or float(np.std(y)) <= 1e-15:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def _slope(x: np.ndarray, y: np.ndarray) -> float | None:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    if len(x) < 2:
        return None
    denom = float(np.sum((x - x.mean()) ** 2))
    if denom <= 1e-15:
        return None
    return float(np.sum((x - x.mean()) * (y - y.mean())) / denom)


def _download_and_audit() -> tuple[
    dict[tuple[str, str], bytes], dict[str, Any], bool
]:
    payloads: dict[tuple[str, str], bytes] = {}
    files: dict[str, Any] = {}
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
                    required.update(BOOKMAKERS[bookmaker]["opening"])
                    required.update(BOOKMAKERS[bookmaker]["closing"])
                required.update(CONSENSUS["opening"])
                required.update(CONSENSUS["closing"])
                missing = sorted(required - columns)
                if season in {VALIDATION, TEST} and missing:
                    gate = False
                files[f"{league}:{season}"] = {
                    "missing_required_price_columns": missing,
                    "has_outcome_column": "FTR" in columns,
                }
    finally:
        requests.get = original_get

    return payloads, {
        "outcome_read_before_audit": False,
        "frozen_bookmakers": list(BOOK_ORDER),
        "consensus": "Football-Data Avg opening/closing 1X2",
        "source_files": files,
        "validation_test_column_gate_passed": gate,
        "intraday_snapshot_gaps": {
            "24h": "No exact timestamped 24h snapshot in frozen source.",
            "6h": "No exact timestamped 6h snapshot in frozen source.",
            "1h": "No exact timestamped 1h snapshot in frozen source.",
        },
    }, gate


def _build_rows(
    payloads: dict[tuple[str, str], bytes]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixture_rows: list[dict[str, Any]] = []
    selection_rows: list[dict[str, Any]] = []

    for (league, season), payload in sorted(payloads.items()):
        split = _split_name(season)
        if split is None:
            continue

        required = {"Date", "HomeTeam", "AwayTeam", "FTR"}
        for bookmaker in BOOK_ORDER:
            required.update(BOOKMAKERS[bookmaker]["opening"])
            required.update(BOOKMAKERS[bookmaker]["closing"])
        required.update(CONSENSUS["opening"])
        required.update(CONSENSUS["closing"])
        frame = pd.read_csv(BytesIO(payload), usecols=lambda c: c in required)

        for source_row, row in frame.iterrows():
            outcome_idx = _outcome_index(row.get("FTR"))
            if outcome_idx is None:
                continue
            fixture_key = (
                f"{league}|{season}|{source_row}|"
                f"{str(row.get('HomeTeam', '')).strip()}|"
                f"{str(row.get('AwayTeam', '')).strip()}"
            )
            try:
                c_open_odds = tuple(float(row.get(c)) for c in CONSENSUS["opening"])
                c_close_odds = tuple(float(row.get(c)) for c in CONSENSUS["closing"])
            except (TypeError, ValueError):
                continue
            c_open = _multiplicative(c_open_odds)
            c_close = _multiplicative(c_close_odds)
            if c_open is None or c_close is None:
                continue
            common = c_close - c_open
            common_energy = float(np.dot(common, common))

            for bookmaker in BOOK_ORDER:
                try:
                    b_open_odds = tuple(
                        float(row.get(c)) for c in BOOKMAKERS[bookmaker]["opening"]
                    )
                    b_close_odds = tuple(
                        float(row.get(c)) for c in BOOKMAKERS[bookmaker]["closing"]
                    )
                except (TypeError, ValueError):
                    continue
                b_open = _multiplicative(b_open_odds)
                b_close = _multiplicative(b_close_odds)
                o_open = _overround(b_open_odds)
                o_close = _overround(b_close_odds)
                if (
                    b_open is None
                    or b_close is None
                    or o_open is None
                    or o_close is None
                ):
                    continue

                residual_open = b_open - c_open
                residual_close = b_close - c_close
                specific = residual_close - residual_open
                total_move = b_close - b_open
                specific_energy = float(np.dot(specific, specific))
                energy_den = common_energy + specific_energy
                share = specific_energy / energy_den if energy_den > 0.0 else 0.0

                candidate = c_close + specific
                candidate_valid = bool(
                    np.all(np.isfinite(candidate))
                    and np.all(candidate > 0.0)
                    and np.all(candidate < 1.0)
                    and abs(float(candidate.sum()) - 1.0) <= 1e-8
                )

                fixture_rows.append(
                    {
                        "league": league,
                        "season": season,
                        "split": split,
                        "fixture_key": fixture_key,
                        "bookmaker": bookmaker,
                        "common_norm": float(np.linalg.norm(common)),
                        "specific_norm": float(np.linalg.norm(specific)),
                        "total_move_norm": float(np.linalg.norm(total_move)),
                        "specific_energy_share": float(share),
                        "overround_open": float(o_open),
                        "overround_close": float(o_close),
                        "overround_move": float(o_close - o_open),
                        "residual_open_norm": float(np.linalg.norm(residual_open)),
                        "residual_close_norm": float(np.linalg.norm(residual_close)),
                        "candidate_valid": candidate_valid,
                    }
                )

                for idx, outcome_type in enumerate(OUTCOME_ORDER):
                    selection_rows.append(
                        {
                            "league": league,
                            "season": season,
                            "split": split,
                            "fixture_key": fixture_key,
                            "bookmaker": bookmaker,
                            "outcome_index": outcome_idx,
                            "outcome_type": outcome_type,
                            "consensus_open_p": float(c_open[idx]),
                            "consensus_close_p": float(c_close[idx]),
                            "book_open_p": float(b_open[idx]),
                            "book_close_p": float(b_close[idx]),
                            "common_move": float(common[idx]),
                            "residual_open": float(residual_open[idx]),
                            "residual_close": float(residual_close[idx]),
                            "book_specific_move": float(specific[idx]),
                            "candidate_p": float(candidate[idx])
                            if candidate_valid
                            else None,
                            "candidate_valid": candidate_valid,
                        }
                    )

    return pd.DataFrame(fixture_rows), pd.DataFrame(selection_rows)


def _fixture_outcomes(selection_rows: pd.DataFrame) -> pd.DataFrame:
    # De-duplicate bookmaker repeats; consensus is fixture-level.
    cols = [
        "league",
        "fixture_key",
        "outcome_index",
        "consensus_open_p",
        "consensus_close_p",
        "outcome_type",
    ]
    base = selection_rows[cols].drop_duplicates()
    return base


def _proper_loss_rows(selection_rows: pd.DataFrame) -> pd.DataFrame:
    base = _fixture_outcomes(selection_rows)
    records: list[dict[str, Any]] = []
    for (league, fixture_key), part in base.groupby(["league", "fixture_key"]):
        part = part.sort_values("outcome_type")
        # restore H,D,A order explicitly
        probs_open = np.array(
            [
                float(part[part["outcome_type"] == outcome]["consensus_open_p"].iloc[0])
                for outcome in OUTCOME_ORDER
            ]
        )
        probs_close = np.array(
            [
                float(part[part["outcome_type"] == outcome]["consensus_close_p"].iloc[0])
                for outcome in OUTCOME_ORDER
            ]
        )
        y = int(part["outcome_index"].iloc[0])
        onehot = np.zeros(3)
        onehot[y] = 1.0
        records.append(
            {
                "league": league,
                "fixture_key": fixture_key,
                "open_logloss": float(-math.log(max(probs_open[y], 1e-15))),
                "close_logloss": float(-math.log(max(probs_close[y], 1e-15))),
                "open_brier": float(np.sum((probs_open - onehot) ** 2)),
                "close_brier": float(np.sum((probs_close - onehot) ** 2)),
            }
        )
    return pd.DataFrame(records)


def _candidate_loss_rows(
    selection_rows: pd.DataFrame, bookmaker: str
) -> pd.DataFrame:
    rows = selection_rows[
        (selection_rows["bookmaker"] == bookmaker)
        & (selection_rows["candidate_valid"])
    ]
    records: list[dict[str, Any]] = []
    for (league, fixture_key), part in rows.groupby(["league", "fixture_key"]):
        if len(part) != 3:
            continue
        p_close = np.array(
            [
                float(part[part["outcome_type"] == outcome]["consensus_close_p"].iloc[0])
                for outcome in OUTCOME_ORDER
            ]
        )
        candidate = np.array(
            [
                float(part[part["outcome_type"] == outcome]["candidate_p"].iloc[0])
                for outcome in OUTCOME_ORDER
            ]
        )
        y = int(part["outcome_index"].iloc[0])
        records.append(
            {
                "league": league,
                "fixture_key": fixture_key,
                "delta_logloss": float(
                    -math.log(max(candidate[y], 1e-15))
                    + math.log(max(p_close[y], 1e-15))
                ),
            }
        )
    return pd.DataFrame(records)


def _bootstrap_mean(
    frame: pd.DataFrame, column: str
) -> dict[str, float | int | None]:
    if frame.empty:
        return {
            "rows": 0,
            "mean": None,
            "ci95_low": None,
            "ci95_high": None,
            "draws": BOOTSTRAP_DRAWS,
        }
    rng = np.random.default_rng(SEED)
    groups = {
        league: part[column].to_numpy(dtype=float)
        for league, part in frame.groupby("league")
    }
    draws = np.empty(BOOTSTRAP_DRAWS)
    for i in range(BOOTSTRAP_DRAWS):
        pieces: list[np.ndarray] = []
        for values in groups.values():
            idx = rng.integers(0, len(values), size=len(values))
            pieces.append(values[idx])
        draws[i] = float(np.concatenate(pieces).mean())
    return {
        "rows": int(len(frame)),
        "mean": float(frame[column].mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "draws": BOOTSTRAP_DRAWS,
    }


def _book_diagnostics(
    fixture_rows: pd.DataFrame,
    selection_rows: pd.DataFrame,
    bookmaker: str,
) -> dict[str, Any]:
    f = fixture_rows[fixture_rows["bookmaker"] == bookmaker]
    s = selection_rows[selection_rows["bookmaker"] == bookmaker]
    reversion = _slope(
        s["residual_open"].to_numpy(dtype=float),
        s["book_specific_move"].to_numpy(dtype=float),
    )
    persistence = _safe_pearson(
        s["residual_open"].to_numpy(dtype=float),
        s["residual_close"].to_numpy(dtype=float),
    )
    margin_corr = _safe_pearson(
        f["specific_norm"].to_numpy(dtype=float),
        np.abs(f["overround_move"].to_numpy(dtype=float)),
    )
    candidate_losses = _candidate_loss_rows(s, bookmaker)
    return {
        "fixtures": int(f["fixture_key"].nunique()),
        "median_specific_energy_share": (
            float(f["specific_energy_share"].median()) if len(f) else None
        ),
        "mean_specific_energy_share": (
            float(f["specific_energy_share"].mean()) if len(f) else None
        ),
        "residual_persistence_pearson": persistence,
        "specific_move_on_open_residual_slope": reversion,
        "specific_norm_vs_abs_overround_move_pearson": margin_corr,
        "candidate_valid_coverage": (
            float(f["candidate_valid"].mean()) if len(f) else 0.0
        ),
        "candidate_incremental_logloss_vs_close_consensus": _bootstrap_mean(
            candidate_losses, "delta_logloss"
        ),
    }


def _league_specific_share(
    fixture_rows: pd.DataFrame, bookmaker: str
) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for league in LEAGUE_ORDER:
        part = fixture_rows[
            (fixture_rows["bookmaker"] == bookmaker)
            & (fixture_rows["league"] == league)
        ]
        out[league] = (
            float(part["specific_energy_share"].median()) if len(part) else None
        )
    return out


def _split_report(
    fixture_rows: pd.DataFrame, selection_rows: pd.DataFrame
) -> dict[str, Any]:
    losses = _proper_loss_rows(selection_rows)
    if len(losses):
        losses = losses.copy()
        losses["logloss_delta_close_minus_open"] = (
            losses["close_logloss"] - losses["open_logloss"]
        )
        losses["brier_delta_close_minus_open"] = (
            losses["close_brier"] - losses["open_brier"]
        )
    common_info = {
        "logloss": _bootstrap_mean(losses, "logloss_delta_close_minus_open")
        if len(losses)
        else _bootstrap_mean(pd.DataFrame(), "x"),
        "brier": _bootstrap_mean(losses, "brier_delta_close_minus_open")
        if len(losses)
        else _bootstrap_mean(pd.DataFrame(), "x"),
    }
    return {
        "fixtures": int(fixture_rows["fixture_key"].nunique())
        if len(fixture_rows)
        else 0,
        "common_information": common_info,
        "books": {
            bookmaker: _book_diagnostics(
                fixture_rows, selection_rows, bookmaker
            )
            for bookmaker in BOOK_ORDER
        },
        "specific_share_by_league": {
            bookmaker: _league_specific_share(fixture_rows, bookmaker)
            for bookmaker in BOOK_ORDER
        },
    }


def _formal_gate(validation: dict[str, Any], test: dict[str, Any]) -> dict[str, Any]:
    common_v = validation["common_information"]["logloss"]
    common_t = test["common_information"]["logloss"]

    common_validation_improves = (
        common_v["mean"] is not None and common_v["mean"] < 0.0
    )
    common_oot_significant = (
        common_t["mean"] is not None
        and common_t["mean"] < 0.0
        and common_t["ci95_high"] is not None
        and common_t["ci95_high"] < 0.0
    )

    share_ok = True
    margin_not_only = True
    books_stable = True
    detail: dict[str, Any] = {}
    for bookmaker in BOOK_ORDER:
        v = validation["books"][bookmaker]
        t = test["books"][bookmaker]
        v_share = v["median_specific_energy_share"]
        t_share = t["median_specific_energy_share"]
        book_share_ok = bool(
            v_share is not None
            and t_share is not None
            and v_share >= MIN_SPECIFIC_ENERGY_SHARE
            and t_share >= MIN_SPECIFIC_ENERGY_SHARE
        )
        share_ok = share_ok and book_share_ok

        corr = t["specific_norm_vs_abs_overround_move_pearson"]
        book_margin_ok = bool(corr is None or abs(corr) < MAX_MARGIN_EXPLANATION_CORR)
        margin_not_only = margin_not_only and book_margin_ok

        league_shares = test["specific_share_by_league"][bookmaker]
        league_count = sum(
            value is not None and value >= MIN_SPECIFIC_ENERGY_SHARE
            for value in league_shares.values()
        )
        book_stable = league_count >= 2
        books_stable = books_stable and book_stable
        detail[bookmaker] = {
            "validation_specific_share_ge_5pct": (
                v_share is not None and v_share >= MIN_SPECIFIC_ENERGY_SHARE
            ),
            "oot_specific_share_ge_5pct": (
                t_share is not None and t_share >= MIN_SPECIFIC_ENERGY_SHARE
            ),
            "oot_margin_correlation_abs_lt_0_80": book_margin_ok,
            "oot_leagues_specific_share_ge_5pct": league_count,
        }

    gates = {
        "validation_common_move_improves_logloss": common_validation_improves,
        "oot_common_move_improves_logloss_with_ci": common_oot_significant,
        "both_books_nontrivial_specific_component": share_ok,
        "specific_component_not_explained_only_by_margin": margin_not_only,
        "specific_component_stable_in_at_least_two_leagues_per_book": books_stable,
    }
    return {"supported": all(gates.values()), "gates": gates, "book_detail": detail}


def _source_gap_result(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_PRICE_COMPONENT_DECOMPOSITION",
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
            "The frozen same-fixture opening/closing bookmaker and consensus source "
            "contract was unavailable. No proxy, paid source or interpolated "
            "intraday snapshot was substituted."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = _download_and_audit()
    if not source_gate:
        return _source_gap_result(
            audit, "MISSING_FROZEN_OPEN_CLOSE_BOOKMAKER_OR_CONSENSUS_COLUMNS"
        )

    fixtures, selections = _build_rows(payloads)
    if fixtures.empty or selections.empty:
        return _source_gap_result(audit, "NO_VALID_MATCHED_FIXTURE_ROWS")

    reports: dict[str, Any] = {}
    for split in ("reference", "validation", "test"):
        f = fixtures[fixtures["split"] == split].copy()
        s = selections[selections["split"] == split].copy()
        reports[split] = _split_report(f, s)

    gate = _formal_gate(reports["validation"], reports["test"])
    supported = bool(gate["supported"])
    decision = (
        "SUPPORTED_PRICE_COMPONENT_DECOMPOSITION"
        if supported
        else "NO_STABLE_BOOKMAKER_SPECIFIC_PRICE_COMPONENT"
    )

    if supported:
        interpretation = (
            "Opening-to-closing 1X2 movement contains a statistically useful common "
            "market-information component and a non-trivial bookmaker-specific "
            "component that remains visible after removing consensus movement and "
            "is not explained only by margin changes. This does NOT identify bettor "
            "flow, liabilities, risk management or bookmaker intent, and it does "
            "not establish a betting edge."
        )
    else:
        interpretation = (
            "The frozen decomposition did not clear every preregistered stability "
            "gate. Common closing information and bookmaker-specific deviations "
            "remain descriptive unless independently confirmed; do not convert them "
            "into production market-movement weights from this sample."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_PRICE_COMPONENT_DECOMPOSITION",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "decomposition": {
            "common_move": "consensus_close - consensus_open",
            "book_residual_open": "book_open - consensus_open",
            "book_residual_close": "book_close - consensus_close",
            "book_specific_move": "book_residual_close - book_residual_open",
            "overround_move": "overround_close - overround_open",
        },
        "specific_component_gate": {
            "minimum_median_energy_share": MIN_SPECIFIC_ENERGY_SHARE,
            "maximum_abs_margin_correlation": MAX_MARGIN_EXPLANATION_CORR,
        },
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "untouched_test": TEST,
            "opening_closing_required": True,
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
        "causal_limit": (
            "Observed bookmaker-specific residual movement cannot identify bet flow, "
            "liabilities, demand elasticity, client mix, risk appetite or intent."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
