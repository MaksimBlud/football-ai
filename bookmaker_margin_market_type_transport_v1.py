"""Opening Asian-Handicap transport of the Issue #535 margin structure."""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd

import bookmaker_margin_structure_v1 as parent

EXPERIMENT_ID = "BOOKMAKER_MARGIN_MARKET_TYPE_TRANSPORT_V1"
BOOTSTRAP_DRAWS = 5000
SEED = 20261005
AH_BOOKS = {
    "BET365": ("B365AHH", "B365AHA"),
    "PINNACLE": ("PAHH", "PAHA"),
}


def _half_goal(value: Any) -> float | None:
    try:
        line = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(line):
        return None
    twice = round(line * 2.0)
    if abs(line * 2.0 - twice) > 1e-9 or twice % 2 == 0:
        return None
    return line


def _two_way(odds: tuple[float, float]) -> tuple[np.ndarray, np.ndarray, float] | None:
    arr = np.asarray(odds, dtype=float)
    if arr.shape != (2,) or not np.all(np.isfinite(arr)) or np.any(arr <= 1.0):
        return None
    q = 1.0 / arr
    total = float(q.sum())
    if total <= 0.0:
        return None
    return q, q / total, total - 1.0


def _download_and_audit() -> tuple[dict[tuple[str, str], bytes], dict[str, Any], bool]:
    payloads, audit, parent_gate = parent._download_and_audit()
    source_files: dict[str, Any] = {}
    gate = bool(parent_gate)
    for (league, season), payload in sorted(payloads.items()):
        columns = set(pd.read_csv(BytesIO(payload), nrows=0).columns)
        missing = sorted({c for pair in AH_BOOKS.values() for c in pair} - columns)
        has_line = "AHh" in columns or "B365AH" in columns
        if season in {parent.VALIDATION, parent.TEST} and (missing or not has_line):
            gate = False
        source_files[f"{league}:{season}"] = {
            "missing_ah_price_columns": missing,
            "has_ah_line": has_line,
        }
    return payloads, {
        **audit,
        "source_files_ah": source_files,
        "outcome_columns_not_read": True,
        "paired_opening_ah_gate_passed": gate,
    }, gate


def _build_rows(payloads: dict[tuple[str, str], bytes]) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    one_x_two = {
        "BET365": parent.BOOKMAKERS["BET365"]["opening"],
        "PINNACLE": parent.BOOKMAKERS["PINNACLE"]["opening"],
    }
    required = {"Date", "HomeTeam", "AwayTeam", "AHh", "B365AH"}
    required.update(parent.CONSENSUS["opening"])
    for cols in AH_BOOKS.values():
        required.update(cols)
    for cols in one_x_two.values():
        required.update(cols)

    for (league, season), payload in sorted(payloads.items()):
        split = parent._split_name(season)
        if split is None:
            continue
        frame = pd.read_csv(BytesIO(payload), usecols=lambda c: c in required)
        for source_row, row in frame.iterrows():
            line = _half_goal(row.get("AHh"))
            if line is None:
                line = _half_goal(row.get("B365AH"))
            if line is None:
                continue
            favourite, underdog = (0, 1) if line < 0 else (1, 0)
            ah: dict[str, tuple[np.ndarray, np.ndarray, float, tuple[float, float]]] = {}
            valid = True
            for book, cols in AH_BOOKS.items():
                try:
                    odds = tuple(float(row.get(c)) for c in cols)
                except (TypeError, ValueError):
                    valid = False
                    break
                parsed = _two_way(odds)
                if parsed is None:
                    valid = False
                    break
                q, fair, overround = parsed
                ah[book] = (q, fair, overround, odds)
            if not valid:
                continue
            ah_consensus = (ah["BET365"][1] + ah["PINNACLE"][1]) / 2.0

            try:
                consensus_odds = tuple(float(row.get(c)) for c in parent.CONSENSUS["opening"])
            except (TypeError, ValueError):
                continue
            consensus_1x2 = parent._multiplicative(consensus_odds)
            if consensus_1x2 is None:
                continue
            fav_1x2, _, long_1x2 = parent._rank_indices(consensus_1x2)

            ah_contrasts: dict[str, float] = {}
            ah_overrounds: dict[str, float] = {}
            x1_contrasts: dict[str, float] = {}
            for book in parent.BOOK_ORDER:
                q, _, overround, _ = ah[book]
                implied_sum = overround + 1.0
                tilt = q / (ah_consensus * implied_sum) - 1.0
                ah_contrasts[book] = float(tilt[underdog] - tilt[favourite])
                ah_overrounds[book] = float(overround)
                try:
                    odds_1x2 = tuple(float(row.get(c)) for c in one_x_two[book])
                except (TypeError, ValueError):
                    valid = False
                    break
                allocation = parent._allocation_tilt(odds_1x2, consensus_1x2)
                if allocation is None:
                    valid = False
                    break
                x1_tilt, _, _ = allocation
                x1_contrasts[book] = float(x1_tilt[long_1x2] - x1_tilt[fav_1x2])
            if not valid:
                continue

            ah_delta = ah_contrasts["BET365"] - ah_contrasts["PINNACLE"]
            x1_delta = x1_contrasts["BET365"] - x1_contrasts["PINNACLE"]
            records.append({
                "league": league,
                "season": season,
                "split": split,
                "fixture_key": f"{league}|{season}|{source_row}",
                "ah_line": line,
                "ah_allocation_delta": ah_delta,
                "ah_overround_delta": ah_overrounds["BET365"] - ah_overrounds["PINNACLE"],
                "x1_allocation_delta": x1_delta,
                "ah_minus_x1_allocation_delta": ah_delta - x1_delta,
            })
    return pd.DataFrame(records)


def _bootstrap(frame: pd.DataFrame, metric: str) -> dict[str, Any]:
    if frame.empty:
        return {"rows": 0, "mean": None, "ci95_low": None, "ci95_high": None, "draws": BOOTSTRAP_DRAWS}
    rng = np.random.default_rng(SEED)
    groups = [p[metric].to_numpy(float) for _, p in frame.groupby("league")]
    draws = np.empty(BOOTSTRAP_DRAWS)
    for i in range(BOOTSTRAP_DRAWS):
        draws[i] = np.concatenate([v[rng.integers(0, len(v), len(v))] for v in groups]).mean()
    return {
        "rows": int(len(frame)),
        "mean": float(frame[metric].mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "draws": BOOTSTRAP_DRAWS,
    }


def _report(frame: pd.DataFrame) -> dict[str, Any]:
    metrics = ("ah_allocation_delta", "ah_overround_delta", "x1_allocation_delta", "ah_minus_x1_allocation_delta")
    return {
        "fixtures": int(len(frame)),
        "paired": {m: _bootstrap(frame, m) for m in metrics},
        "by_league": {
            m: {league: (float(part[m].mean()) if len(part) else None)
                for league in parent.LEAGUE_ORDER
                for part in [frame[frame["league"] == league]]}
            for m in metrics
        },
    }


def _same_sign(a: float | None, b: float | None) -> bool:
    return a is not None and b is not None and a != 0.0 and b != 0.0 and ((a > 0) == (b > 0))


def _formal_gate(validation: dict[str, Any], test: dict[str, Any], source_gate: bool) -> dict[str, Any]:
    v = validation["paired"]["ah_allocation_delta"]
    t = test["paired"]["ah_allocation_delta"]
    matching = sum(_same_sign(x, t["mean"]) for x in test["by_league"]["ah_allocation_delta"].values())
    gates = {
        "source_gate": source_gate,
        "validation_and_test_same_sign": _same_sign(v["mean"], t["mean"]),
        "test_ci_excludes_zero": t["ci95_low"] is not None and (t["ci95_low"] > 0 or t["ci95_high"] < 0),
        "at_least_two_leagues_same_sign": matching >= 2,
        "total_overround_reported": test["paired"]["ah_overround_delta"]["mean"] is not None,
        "cross_market_contrast_reported": test["paired"]["ah_minus_x1_allocation_delta"]["ci95_low"] is not None,
    }
    return {"supported": all(gates.values()), "gates": gates, "matching_test_leagues": matching}


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = _download_and_audit()
    rows = _build_rows(payloads) if source_gate else pd.DataFrame()
    if not source_gate or rows.empty:
        return {
            "experiment_id": EXPERIMENT_ID, "research_only": True,
            "source_audit": audit, "validation": {}, "test": {},
            "formal_gate": {"supported": False, "reason": "PAIRED_AH_SOURCE_GAP"},
            "supported": False, "decision": "BLOCKED_BY_SOURCE_GAP",
            "interpretation_guard": "The frozen same-fixture Bet365/Pinnacle opening Asian Handicap source gate failed; no proxy source was substituted.",
            "paid_odds_api_calls": 0, "supabase_writes": 0,
            "production_operations": False, "production_promotion": False,
            "result": "RESEARCH_ONLY_NO_BET",
        }
    validation = _report(rows[rows["split"] == "validation"])
    test = _report(rows[rows["split"] == "test"])
    gate = _formal_gate(validation, test, source_gate)
    supported = bool(gate["supported"])
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "OUTCOME_FREE_CROSS_MARKET_MARGIN_TRANSPORT",
        "research_only": True, "paid_odds_api_calls": 0, "supabase_writes": 0,
        "production_operations": False, "production_promotion": False,
        "source_audit": audit,
        "temporal_design": {"reference": list(parent.REFERENCE), "validation": parent.VALIDATION, "untouched_test": parent.TEST, "primary_horizon": "opening"},
        "reference": _report(rows[rows["split"] == "reference"]),
        "validation": validation, "test": test, "formal_gate": gate,
        "supported": supported,
        "decision": "SUPPORTED_CROSS_MARKET_MARGIN_STRUCTURE" if supported else "NO_STABLE_CROSS_MARKET_MARGIN_STRUCTURE",
        "interpretation_guard": (
            "The bookmaker-specific allocation signature transported to opening Asian Handicap prices; magnitude remains market-dependent and non-causal."
            if supported else
            "The supported 1X2 parent effect did not clear every frozen Asian Handicap transport gate; the parent result is unchanged."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
