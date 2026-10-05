"""Deterministic common-vs-book-specific price formation decomposition (#532)."""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd

import bookmaker_margin_structure_v1 as source

EXPERIMENT_ID = "BOOKMAKER_PRICE_FORMATION_V1"
BOOTSTRAP_DRAWS = 5000
SEED = 20261005
MIN_SPECIFIC_VARIANCE_SHARE = 0.05
MIN_VARIANCE_AFTER_MARGIN = 0.25


def _loss(p: np.ndarray, outcome: int) -> tuple[float, float]:
    p = np.asarray(p, dtype=float)
    y = np.zeros(3)
    y[outcome] = 1.0
    return -math.log(max(float(p[outcome]), 1e-15)), float(np.sum((p - y) ** 2))


def _build_rows(payloads: dict[tuple[str, str], bytes]) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixture_rows: list[dict[str, Any]] = []
    book_rows: list[dict[str, Any]] = []
    required = {"Date", "HomeTeam", "AwayTeam", "FTR"}
    for book in source.BOOK_ORDER:
        for cols in source.BOOKMAKERS[book].values():
            required.update(cols)
    for (league, season), payload in sorted(payloads.items()):
        split = source._split_name(season)
        if split is None:
            continue
        frame = pd.read_csv(BytesIO(payload), usecols=lambda c: c in required)
        for source_row, row in frame.iterrows():
            outcome = source._outcome_index(row.get("FTR"))
            if outcome is None:
                continue
            fair: dict[str, dict[str, np.ndarray]] = {h: {} for h in source.HORIZONS}
            overround: dict[str, dict[str, float]] = {h: {} for h in source.HORIZONS}
            valid = True
            for horizon in source.HORIZONS:
                for book in source.BOOK_ORDER:
                    try:
                        odds = tuple(float(row.get(c)) for c in source.BOOKMAKERS[book][horizon])
                    except (TypeError, ValueError):
                        valid = False
                        break
                    p = source._multiplicative(odds)
                    if p is None:
                        valid = False
                        break
                    fair[horizon][book] = p
                    overround[horizon][book] = float(sum(1.0 / x for x in odds) - 1.0)
                if not valid:
                    break
            if not valid:
                continue
            consensus_open = np.mean([fair["opening"][b] for b in source.BOOK_ORDER], axis=0)
            consensus_close = np.mean([fair["closing"][b] for b in source.BOOK_ORDER], axis=0)
            open_ll, open_brier = _loss(consensus_open, outcome)
            close_ll, close_brier = _loss(consensus_close, outcome)
            key = f"{league}|{season}|{source_row}"
            fixture_rows.append({
                "league": league, "season": season, "split": split, "fixture_key": key,
                "common_log_loss_delta": close_ll - open_ll,
                "common_brier_delta": close_brier - open_brier,
                "common_move_norm_sq": float(np.sum((consensus_close - consensus_open) ** 2)),
            })
            for book in source.BOOK_ORDER:
                residual_open = fair["opening"][book] - consensus_open
                residual_close = fair["closing"][book] - consensus_close
                specific_move = residual_close - residual_open
                total_move = fair["closing"][book] - fair["opening"][book]
                book_close_ll, book_close_brier = _loss(fair["closing"][book], outcome)
                margin_move = overround["closing"][book] - overround["opening"][book]
                book_rows.append({
                    "league": league, "season": season, "split": split, "fixture_key": key,
                    "bookmaker": book, "margin_move": margin_move,
                    "residual_open_norm_sq": float(np.sum(residual_open ** 2)),
                    "residual_close_norm_sq": float(np.sum(residual_close ** 2)),
                    "residual_persistence_dot": float(np.dot(residual_open, residual_close)),
                    "specific_move_norm_sq": float(np.sum(specific_move ** 2)),
                    "total_move_norm_sq": float(np.sum(total_move ** 2)),
                    "specific_h": float(specific_move[0]),
                    "specific_d": float(specific_move[1]),
                    "specific_a": float(specific_move[2]),
                    "incremental_close_log_loss": book_close_ll - close_ll,
                    "incremental_close_brier": book_close_brier - close_brier,
                })
    return pd.DataFrame(fixture_rows), pd.DataFrame(book_rows)


def _bootstrap(frame: pd.DataFrame, metric: str) -> dict[str, Any]:
    if frame.empty:
        return {"rows": 0, "mean": None, "ci95_low": None, "ci95_high": None, "draws": BOOTSTRAP_DRAWS}
    rng = np.random.default_rng(SEED)
    groups = [p[metric].to_numpy(float) for _, p in frame.groupby("league")]
    draws = np.empty(BOOTSTRAP_DRAWS)
    for i in range(BOOTSTRAP_DRAWS):
        draws[i] = np.concatenate([v[rng.integers(0, len(v), len(v))] for v in groups]).mean()
    return {"rows": int(len(frame)), "mean": float(frame[metric].mean()),
            "ci95_low": float(np.quantile(draws, .025)), "ci95_high": float(np.quantile(draws, .975)),
            "draws": BOOTSTRAP_DRAWS}


def _variance_diagnostics(frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {"specific_variance_share": None, "variance_after_margin_fraction": None}
    specific = float(frame["specific_move_norm_sq"].sum())
    total = float(frame["total_move_norm_sq"].sum())
    share = specific / total if total > 0 else None
    y = frame[["specific_h", "specific_d", "specific_a"]].to_numpy(float).reshape(-1)
    x = np.repeat(frame["margin_move"].to_numpy(float), 3)
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    fitted = design @ beta
    centered_ss = float(np.sum((y - y.mean()) ** 2))
    residual_ss = float(np.sum((y - fitted) ** 2))
    after_margin = residual_ss / centered_ss if centered_ss > 0 else None
    return {
        "specific_variance_share": share,
        "variance_after_margin_fraction": after_margin,
        "specific_move_margin_correlation": float(np.corrcoef(np.sqrt(frame["specific_move_norm_sq"]), frame["margin_move"])[0, 1]) if len(frame) > 2 else None,
        "mean_residual_open_norm_sq": float(frame["residual_open_norm_sq"].mean()),
        "mean_residual_close_norm_sq": float(frame["residual_close_norm_sq"].mean()),
        "mean_residual_persistence_dot": float(frame["residual_persistence_dot"].mean()),
    }


def _split_report(fixtures: pd.DataFrame, books: pd.DataFrame) -> dict[str, Any]:
    common = {
        "log_loss": _bootstrap(fixtures, "common_log_loss_delta"),
        "brier": _bootstrap(fixtures, "common_brier_delta"),
        "by_league_log_loss": {league: (float(part["common_log_loss_delta"].mean()) if len(part) else None)
            for league in source.LEAGUE_ORDER for part in [fixtures[fixtures["league"] == league]]},
    }
    by_book: dict[str, Any] = {}
    for book in source.BOOK_ORDER:
        part = books[books["bookmaker"] == book]
        by_book[book] = {
            "rows": int(len(part)),
            "incremental_close_log_loss_vs_consensus": _bootstrap(part, "incremental_close_log_loss"),
            "incremental_close_brier_vs_consensus": _bootstrap(part, "incremental_close_brier"),
            "decomposition": _variance_diagnostics(part),
        }
    return {"fixtures": int(len(fixtures)), "common_information": common,
            "pooled_decomposition": _variance_diagnostics(books), "by_bookmaker": by_book}


def _formal_gate(test: dict[str, Any], source_gate: bool) -> dict[str, Any]:
    common = test["common_information"]["log_loss"]
    decomposition = test["pooled_decomposition"]
    shares = [test["by_bookmaker"][b]["decomposition"]["specific_variance_share"] for b in source.BOOK_ORDER]
    negative_leagues = sum(v is not None and v < 0 for v in test["common_information"]["by_league_log_loss"].values())
    gates = {
        "source_gate": source_gate,
        "common_move_improves_oot_log_loss": common["mean"] is not None and common["mean"] < 0,
        "common_move_ci95_upper_below_zero": common["ci95_high"] is not None and common["ci95_high"] < 0,
        "specific_variance_share_ge_0_05": decomposition["specific_variance_share"] is not None and decomposition["specific_variance_share"] >= MIN_SPECIFIC_VARIANCE_SHARE,
        "both_books_have_nontrivial_specific_variance": all(v is not None and v >= MIN_SPECIFIC_VARIANCE_SHARE for v in shares),
        "specific_variance_not_explained_by_margin": decomposition["variance_after_margin_fraction"] is not None and decomposition["variance_after_margin_fraction"] >= MIN_VARIANCE_AFTER_MARGIN,
        "at_least_two_leagues_common_improvement": negative_leagues >= 2,
    }
    return {"supported": all(gates.values()), "gates": gates, "negative_oot_leagues": negative_leagues,
            "frozen_thresholds": {"minimum_specific_variance_share": MIN_SPECIFIC_VARIANCE_SHARE, "minimum_variance_after_margin_fraction": MIN_VARIANCE_AFTER_MARGIN}}


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = source._download_and_audit()
    fixtures, books = _build_rows(payloads) if source_gate else (pd.DataFrame(), pd.DataFrame())
    if not source_gate or fixtures.empty or books.empty:
        return {
            "experiment_id": EXPERIMENT_ID, "research_only": True, "source_audit": audit,
            "reference": {}, "validation": {}, "test": {}, "formal_gate": {"supported": False, "reason": "SOURCE_GAP"},
            "supported": False, "decision": "BLOCKED_BY_SOURCE_GAP",
            "interpretation_guard": "The frozen paired opening/closing two-book source contract failed; no proxy or interpolated snapshot was used.",
            "paid_odds_api_calls": 0, "supabase_writes": 0, "production_operations": False,
            "production_promotion": False, "result": "RESEARCH_ONLY_NO_BET",
        }
    reports = {}
    for split in ("reference", "validation", "test"):
        reports[split] = _split_report(fixtures[fixtures["split"] == split], books[books["split"] == split])
    gate = _formal_gate(reports["test"], source_gate)
    supported = bool(gate["supported"])
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_PRICE_COMPONENT_DECOMPOSITION",
        "research_only": True, "paid_odds_api_calls": 0, "supabase_writes": 0,
        "production_operations": False, "production_promotion": False,
        "source_audit": {**audit, "outcome_read_after_audit": True},
        "temporal_design": {"reference": list(source.REFERENCE), "validation": source.VALIDATION, "untouched_test": source.TEST},
        "reference": reports["reference"], "validation": reports["validation"], "test": reports["test"],
        "formal_gate": gate, "supported": supported,
        "decision": "SUPPORTED_PRICE_COMPONENT_DECOMPOSITION" if supported else "NO_STABLE_BOOKMAKER_SPECIFIC_PRICE_COMPONENT",
        "interpretation_guard": (
            "Opening-to-closing movement contains a stable common information component and non-trivial bookmaker-specific variation not reducible to total-margin movement. This is not causal evidence about liabilities or bettor flow."
            if supported else
            "The frozen OOT gates did not jointly establish stable common information plus non-trivial bookmaker-specific repricing beyond margin movement."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
