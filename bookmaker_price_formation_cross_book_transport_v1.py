"""Frozen cross-book/cross-league transport of Issue #532 price formation.

The source audit is outcome-free.  It requires an independent Bundesliga and
Ligue 1 population plus at least one predeclared third bookmaker with >=90%
finite opening+closing coverage in validation and OOT for both leagues.  No
bookmaker is selected with match outcomes.
"""
from __future__ import annotations

from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd

import bookmaker_price_formation_v1 as parent
from cross_league_bookmaker_source import LEAGUES, download_and_audit

EXPERIMENT_ID = "BOOKMAKER_PRICE_FORMATION_CROSS_BOOK_TRANSPORT_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
HORIZONS = ("opening", "closing")
COVERAGE_THRESHOLD = 0.90
ANCHORS = ("BET365", "PINNACLE")
ADDITIONAL = ("BW", "IW", "WH", "VC")
BOOKMAKERS = {
    "BET365": {"opening": ("B365H", "B365D", "B365A"), "closing": ("B365CH", "B365CD", "B365CA")},
    "PINNACLE": {"opening": ("PSH", "PSD", "PSA"), "closing": ("PSCH", "PSCD", "PSCA")},
    "BW": {"opening": ("BWH", "BWD", "BWA"), "closing": ("BWCH", "BWCD", "BWCA")},
    "IW": {"opening": ("IWH", "IWD", "IWA"), "closing": ("IWCH", "IWCD", "IWCA")},
    "WH": {"opening": ("WHH", "WHD", "WHA"), "closing": ("WHCH", "WHCD", "WHCA")},
    "VC": {"opening": ("VCH", "VCD", "VCA"), "closing": ("VCCH", "VCCD", "VCCA")},
}
CONSENSUS = {"opening": ("AvgH", "AvgD", "AvgA"), "closing": ("AvgCH", "AvgCD", "AvgCA")}


def _all_columns(mapping: dict[str, tuple[str, str, str]]) -> tuple[str, ...]:
    return tuple(column for horizon in HORIZONS for column in mapping[horizon])


def _valid_price_rows(frame: pd.DataFrame, columns: tuple[str, ...]) -> np.ndarray:
    if not set(columns).issubset(frame.columns):
        return np.zeros(len(frame), dtype=bool)
    values = frame.loc[:, list(columns)].apply(pd.to_numeric, errors="coerce").to_numpy(float)
    return np.isfinite(values).all(axis=1) & (values > 1.0).all(axis=1)


def _coverage_audit(payloads: dict[tuple[str, str], bytes]) -> tuple[dict[str, Any], list[str], bool]:
    """Freeze bookmaker eligibility using prices only, before FTR is loaded."""
    coverage: dict[str, dict[str, Any]] = {book: {} for book in (*ANCHORS, *ADDITIONAL, "AVG")}
    eligible_additional: list[str] = []
    required_splits = {VALIDATION, TEST}
    for (league, season), payload in sorted(payloads.items()):
        if season not in required_splits:
            continue
        frame = pd.read_csv(BytesIO(payload))
        key = f"{league}:{season}"
        for book in (*ANCHORS, *ADDITIONAL):
            columns = _all_columns(BOOKMAKERS[book])
            valid = _valid_price_rows(frame, columns)
            coverage[book][key] = {
                "rows": int(len(frame)),
                "valid_opening_closing_rows": int(valid.sum()),
                "coverage": float(valid.mean()) if len(frame) else 0.0,
                "missing_columns": sorted(set(columns) - set(frame.columns)),
            }
        columns = _all_columns(CONSENSUS)
        valid = _valid_price_rows(frame, columns)
        coverage["AVG"][key] = {
            "rows": int(len(frame)),
            "valid_opening_closing_rows": int(valid.sum()),
            "coverage": float(valid.mean()) if len(frame) else 0.0,
            "missing_columns": sorted(set(columns) - set(frame.columns)),
        }

    expected = {f"{league}:{season}" for league in LEAGUES for season in required_splits}
    for book in ADDITIONAL:
        records = coverage[book]
        if set(records) == expected and all(record["coverage"] >= COVERAGE_THRESHOLD for record in records.values()):
            eligible_additional.append(book)

    # Anchors and external AVG must exist on each required league-season.  The
    # >=90% rule is intentionally applied only to the predeclared third books,
    # exactly as preregistered; incomplete anchor rows are dropped pairwise.
    anchor_consensus_present = all(
        set(coverage[book]) == expected
        and all(not record["missing_columns"] and record["valid_opening_closing_rows"] > 0 for record in coverage[book].values())
        for book in (*ANCHORS, "AVG")
    )
    gate = anchor_consensus_present and bool(eligible_additional)
    return {
        "outcome_read_before_audit": False,
        "coverage_threshold": COVERAGE_THRESHOLD,
        "predeclared_additional_bookmakers": list(ADDITIONAL),
        "eligible_additional_bookmakers": eligible_additional,
        "coverage": coverage,
        "anchor_consensus_columns_present": anchor_consensus_present,
        "source_gate_passed": gate,
    }, eligible_additional, gate


def _split_name(season: str) -> str | None:
    if season in REFERENCE:
        return "reference"
    if season == VALIDATION:
        return "validation"
    if season == TEST:
        return "test"
    return None


def _build_rows(
    payloads: dict[tuple[str, str], bytes], included_books: list[str]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    fixture_rows: list[dict[str, Any]] = []
    book_rows: list[dict[str, Any]] = []
    required = {"FTR"}
    for book in included_books:
        required.update(_all_columns(BOOKMAKERS[book]))
    required.update(_all_columns(CONSENSUS))

    for (league, season), payload in sorted(payloads.items()):
        split = _split_name(season)
        if split is None:
            continue
        frame = pd.read_csv(BytesIO(payload), usecols=lambda column: column in required)
        for source_row, row in frame.iterrows():
            outcome = parent.source._outcome_index(row.get("FTR"))
            if outcome is None:
                continue
            consensus: dict[str, np.ndarray] = {}
            fair: dict[str, dict[str, np.ndarray]] = {horizon: {} for horizon in HORIZONS}
            overround: dict[str, dict[str, float]] = {horizon: {} for horizon in HORIZONS}
            valid = True
            for horizon in HORIZONS:
                try:
                    avg_odds = tuple(float(row.get(column)) for column in CONSENSUS[horizon])
                except (TypeError, ValueError):
                    valid = False
                    break
                avg_p = parent.source._multiplicative(avg_odds)
                if avg_p is None:
                    valid = False
                    break
                consensus[horizon] = avg_p
                for book in included_books:
                    try:
                        odds = tuple(float(row.get(column)) for column in BOOKMAKERS[book][horizon])
                    except (TypeError, ValueError):
                        valid = False
                        break
                    p = parent.source._multiplicative(odds)
                    if p is None:
                        valid = False
                        break
                    fair[horizon][book] = p
                    overround[horizon][book] = float(sum(1.0 / value for value in odds) - 1.0)
                if not valid:
                    break
            if not valid:
                continue

            open_ll, open_brier = parent._loss(consensus["opening"], outcome)
            close_ll, close_brier = parent._loss(consensus["closing"], outcome)
            key = f"{league}|{season}|{source_row}"
            fixture_rows.append({
                "league": league,
                "season": season,
                "split": split,
                "fixture_key": key,
                "common_log_loss_delta": close_ll - open_ll,
                "common_brier_delta": close_brier - open_brier,
                "common_move_norm_sq": float(np.sum((consensus["closing"] - consensus["opening"]) ** 2)),
            })
            for book in included_books:
                residual_open = fair["opening"][book] - consensus["opening"]
                residual_close = fair["closing"][book] - consensus["closing"]
                specific_move = residual_close - residual_open
                total_move = fair["closing"][book] - fair["opening"][book]
                close_book_ll, close_book_brier = parent._loss(fair["closing"][book], outcome)
                book_rows.append({
                    "league": league,
                    "season": season,
                    "split": split,
                    "fixture_key": key,
                    "bookmaker": book,
                    "margin_move": overround["closing"][book] - overround["opening"][book],
                    "residual_open_norm_sq": float(np.sum(residual_open ** 2)),
                    "residual_close_norm_sq": float(np.sum(residual_close ** 2)),
                    "residual_persistence_dot": float(np.dot(residual_open, residual_close)),
                    "specific_move_norm_sq": float(np.sum(specific_move ** 2)),
                    "total_move_norm_sq": float(np.sum(total_move ** 2)),
                    "specific_h": float(specific_move[0]),
                    "specific_d": float(specific_move[1]),
                    "specific_a": float(specific_move[2]),
                    "incremental_close_log_loss": close_book_ll - close_ll,
                    "incremental_close_brier": close_book_brier - close_brier,
                })
    return pd.DataFrame(fixture_rows), pd.DataFrame(book_rows)


def _split_report(fixtures: pd.DataFrame, books: pd.DataFrame, included_books: list[str]) -> dict[str, Any]:
    common = {
        "log_loss": parent._bootstrap(fixtures, "common_log_loss_delta"),
        "brier": parent._bootstrap(fixtures, "common_brier_delta"),
        "by_league_log_loss": {
            league: (float(part["common_log_loss_delta"].mean()) if len(part) else None)
            for league in LEAGUES
            for part in [fixtures[fixtures["league"] == league]]
        },
    }
    by_bookmaker: dict[str, Any] = {}
    for book in included_books:
        part = books[books["bookmaker"] == book]
        decomposition = parent._variance_diagnostics(part)
        decomposition["mean_specific_move"] = {
            outcome: (float(part[column].mean()) if len(part) else None)
            for outcome, column in (("H", "specific_h"), ("D", "specific_d"), ("A", "specific_a"))
        }
        by_bookmaker[book] = {
            "rows": int(len(part)),
            "incremental_close_log_loss_vs_consensus": parent._bootstrap(part, "incremental_close_log_loss"),
            "incremental_close_brier_vs_consensus": parent._bootstrap(part, "incremental_close_brier"),
            "decomposition": decomposition,
        }
    return {
        "fixtures": int(len(fixtures)),
        "common_information": common,
        "pooled_decomposition": parent._variance_diagnostics(books),
        "by_bookmaker": by_bookmaker,
    }


def _behavior_consistent(validation: dict[str, Any], test: dict[str, Any], books: list[str]) -> bool:
    for book in books:
        v = validation["by_bookmaker"][book]["decomposition"]["mean_specific_move"]
        t = test["by_bookmaker"][book]["decomposition"]["mean_specific_move"]
        v_array = np.asarray([v[key] for key in ("H", "D", "A")], dtype=float)
        t_array = np.asarray([t[key] for key in ("H", "D", "A")], dtype=float)
        if not np.all(np.isfinite(v_array)) or not np.all(np.isfinite(t_array)) or float(np.dot(v_array, t_array)) < 0.0:
            return False
    return True


def _formal_gate(
    validation: dict[str, Any], test: dict[str, Any], additional_books: list[str], source_gate: bool
) -> dict[str, Any]:
    common = test["common_information"]["log_loss"]
    by_league = test["common_information"]["by_league_log_loss"]
    shares = [test["by_bookmaker"][book]["decomposition"]["specific_variance_share"] for book in additional_books]
    residuals = [test["by_bookmaker"][book]["decomposition"]["variance_after_margin_fraction"] for book in additional_books]
    gates = {
        "source_gate_with_third_book": source_gate and bool(additional_books),
        "common_move_improves_oot_log_loss": common["mean"] is not None and common["mean"] < 0.0,
        "common_move_ci95_upper_below_zero": common["ci95_high"] is not None and common["ci95_high"] < 0.0,
        "both_transport_leagues_improve": len(by_league) == 2 and all(value is not None and value < 0.0 for value in by_league.values()),
        "each_additional_book_specific_share_ge_0_05": bool(shares) and all(value is not None and value >= parent.MIN_SPECIFIC_VARIANCE_SHARE for value in shares),
        "each_additional_book_variance_after_margin_ge_0_25": bool(residuals) and all(value is not None and value >= parent.MIN_VARIANCE_AFTER_MARGIN for value in residuals),
        "additional_book_behavior_not_contradictory": bool(additional_books) and _behavior_consistent(validation, test, additional_books),
    }
    return {
        "supported": all(gates.values()),
        "gates": gates,
        "frozen_thresholds": {
            "minimum_additional_book_coverage": COVERAGE_THRESHOLD,
            "minimum_specific_variance_share": parent.MIN_SPECIFIC_VARIANCE_SHARE,
            "minimum_variance_after_margin_fraction": parent.MIN_VARIANCE_AFTER_MARGIN,
            "behavior_consistency": "validation/test mean specific-move vector dot product >= 0",
        },
    }


def evaluate() -> dict[str, Any]:
    source_books = {**BOOKMAKERS, "AVG": CONSENSUS}
    payloads, header_audit, _ = download_and_audit(source_books)
    coverage_audit, additional_books, source_gate = _coverage_audit(payloads)
    audit = {**header_audit, **coverage_audit}
    if not source_gate:
        return {
            "experiment_id": EXPERIMENT_ID,
            "parent_issue": 532,
            "research_only": True,
            "source_audit": audit,
            "included_bookmakers": [],
            "reference": {},
            "validation": {"common_information": {}, "by_bookmaker": {}},
            "test": {"common_information": {}, "by_bookmaker": {}},
            "formal_gate": {"supported": False, "reason": "NO_QUALIFYING_ADDITIONAL_BOOKMAKER"},
            "supported": False,
            "decision": "BLOCKED_BY_SOURCE_GAP",
            "interpretation_guard": "No predeclared third bookmaker met the frozen >=90% opening+closing coverage gate in both leagues and both OOS seasons; outcomes were not read.",
            "paid_odds_api_calls": 0,
            "supabase_writes": 0,
            "production_operations": False,
            "production_promotion": False,
            "result": "RESEARCH_ONLY_NO_BET",
        }

    included_books = [*ANCHORS, *additional_books]
    fixtures, books = _build_rows(payloads, included_books)
    if fixtures.empty or books.empty:
        return {
            "experiment_id": EXPERIMENT_ID,
            "parent_issue": 532,
            "research_only": True,
            "source_audit": {**audit, "outcome_read_after_audit": True},
            "included_bookmakers": included_books,
            "reference": {},
            "validation": {"common_information": {}, "by_bookmaker": {}},
            "test": {"common_information": {}, "by_bookmaker": {}},
            "formal_gate": {"supported": False, "reason": "NO_COMPLETE_PAIRED_ROWS"},
            "supported": False,
            "decision": "BLOCKED_BY_SOURCE_GAP",
            "interpretation_guard": "The source audit passed but no complete same-fixture rows survived the frozen pairwise construction.",
            "paid_odds_api_calls": 0,
            "supabase_writes": 0,
            "production_operations": False,
            "production_promotion": False,
            "result": "RESEARCH_ONLY_NO_BET",
        }

    reports = {
        split: _split_report(fixtures[fixtures["split"] == split], books[books["split"] == split], included_books)
        for split in ("reference", "validation", "test")
    }
    gate = _formal_gate(reports["validation"], reports["test"], additional_books, source_gate)
    supported = bool(gate["supported"])
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_CROSS_BOOK_CROSS_LEAGUE_PRICE_COMPONENT_TRANSPORT",
        "parent_issue": 532,
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "source_audit": {**audit, "outcome_read_after_audit": True},
        "temporal_design": {"reference": list(REFERENCE), "validation": VALIDATION, "untouched_test": TEST},
        "consensus": "Football-Data Avg opening/closing 1X2, multiplicatively de-vigged",
        "included_bookmakers": included_books,
        "reference": reports["reference"],
        "validation": reports["validation"],
        "test": reports["test"],
        "formal_gate": gate,
        "supported": supported,
        "decision": "SUPPORTED_CROSS_BOOK_PRICE_COMPONENT_TRANSPORT" if supported else "NO_CROSS_BOOK_PRICE_COMPONENT_CONFIRMATION",
        "interpretation_guard": (
            "The frozen decomposition transported to both new leagues and qualifying third books; this does not identify bettor flow, liabilities, intent or a betting edge."
            if supported else
            "The independent transport did not clear every frozen gate. The negative Issue #532 result remains binding."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
