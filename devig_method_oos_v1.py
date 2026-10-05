"""Deterministic OOS comparison of 1X2 de-vig methods.

Research-only evaluator for Issue #533. It compares four preregistered transforms
of bookmaker decimal odds into fair probabilities:

- multiplicative / proportional normalization
- additive
- power
- Shin

The methods are parameter-free per fixture. 2024/25 is used to select a single
alternative candidate; 2025/26 is untouched confirmation. The primary horizon is
closing 1X2 odds, with opening odds as a frozen sensitivity check.

No paid API, Supabase write, production operation, betting action or automatic
promotion is performed here.
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

EXPERIMENT_ID = "DEVIG_METHOD_OOS_V1"
REFERENCE = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
ALLOWED = set(REFERENCE) | {VALIDATION, TEST}
LEAGUE_ORDER = ("EPL", "LA_LIGA", "SERIE_A")
METHODS = ("multiplicative", "additive", "power", "shin")
ALTERNATIVES = ("additive", "power", "shin")
HORIZONS = ("opening", "closing")
OUTCOME_ORDER = ("H", "D", "A")
MIN_METHOD_COVERAGE = 0.99
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


def _normalize(values: np.ndarray) -> np.ndarray | None:
    values = np.asarray(values, dtype=float)
    if (
        values.shape != (3,)
        or not np.all(np.isfinite(values))
        or np.any(values <= 0.0)
    ):
        return None
    total = float(values.sum())
    if not math.isfinite(total) or total <= 0.0:
        return None
    out = values / total
    if np.any(out <= 0.0) or np.any(out >= 1.0):
        return None
    return out


def _inverse_odds(odds: tuple[float, float, float]) -> np.ndarray | None:
    arr = np.asarray(odds, dtype=float)
    if arr.shape != (3,) or not np.all(np.isfinite(arr)) or np.any(arr <= 1.0):
        return None
    return 1.0 / arr


def _multiplicative(odds: tuple[float, float, float]) -> np.ndarray | None:
    q = _inverse_odds(odds)
    if q is None:
        return None
    return _normalize(q)


def _additive(odds: tuple[float, float, float]) -> np.ndarray | None:
    q = _inverse_odds(odds)
    if q is None:
        return None
    margin = float(q.sum() - 1.0)
    p = q - margin / len(q)
    return _normalize(p)


def _power(odds: tuple[float, float, float]) -> np.ndarray | None:
    q = _inverse_odds(odds)
    if q is None:
        return None

    # sum(q_i ** k) is monotone decreasing for q_i in (0, 1).
    lo, hi = 0.0, 100.0
    for _ in range(160):
        mid = (lo + hi) / 2.0
        total = float(np.power(q, mid).sum())
        if total > 1.0:
            lo = mid
        else:
            hi = mid
    k = (lo + hi) / 2.0
    return _normalize(np.power(q, k))


def _shin(odds: tuple[float, float, float]) -> np.ndarray | None:
    q = _inverse_odds(odds)
    if q is None:
        return None
    total_q = float(q.sum())
    if total_q < 1.0 - 1e-10:
        # Standard non-negative-insider Shin model does not identify a solution
        # for an underround book. Fail closed rather than inventing a z < 0 rule.
        return None
    if abs(total_q - 1.0) <= 1e-10:
        return _normalize(q)

    def probabilities(z: float) -> np.ndarray:
        inside = z * z + 4.0 * (1.0 - z) * (q * q) / total_q
        # Algebraically equivalent stable form of the standard Shin solution.
        return 2.0 * (q * q) / total_q / (np.sqrt(inside) + z)

    lo, hi = 0.0, 1.0
    if float(probabilities(lo).sum()) < 1.0:
        return None
    if float(probabilities(hi).sum()) > 1.0:
        return None
    for _ in range(160):
        mid = (lo + hi) / 2.0
        if float(probabilities(mid).sum()) > 1.0:
            lo = mid
        else:
            hi = mid
    z = (lo + hi) / 2.0
    return _normalize(probabilities(z))


TRANSFORMS = {
    "multiplicative": _multiplicative,
    "additive": _additive,
    "power": _power,
    "shin": _shin,
}


def _outcome_index(value: Any) -> int | None:
    text = str(value).strip().upper()
    if text not in OUTCOME_ORDER:
        return None
    return OUTCOME_ORDER.index(text)


def _losses(probabilities: np.ndarray, outcomes: np.ndarray) -> dict[str, np.ndarray]:
    rows = np.arange(len(outcomes))
    chosen = np.clip(probabilities[rows, outcomes], 1e-15, 1.0)
    log_loss = -np.log(chosen)

    one_hot = np.zeros_like(probabilities)
    one_hot[rows, outcomes] = 1.0
    brier = np.sum((probabilities - one_hot) ** 2, axis=1)

    pred_cum = np.cumsum(probabilities, axis=1)[:, :-1]
    obs_cum = np.cumsum(one_hot, axis=1)[:, :-1]
    rps = np.mean((pred_cum - obs_cum) ** 2, axis=1)
    return {"log_loss": log_loss, "brier": brier, "rps": rps}


def _calibration_binary(probability: np.ndarray, outcome: np.ndarray) -> dict[str, float | None]:
    p = np.clip(np.asarray(probability, dtype=float), 1e-6, 1.0 - 1e-6)
    y = np.asarray(outcome, dtype=float)
    if len(p) < 20 or len(np.unique(y)) < 2:
        return {"intercept": None, "slope": None, "ece": None}

    x = np.log(p / (1.0 - p))
    design = np.column_stack([np.ones(len(x)), x])
    beta = np.array([0.0, 1.0], dtype=float)
    for _ in range(60):
        eta = np.clip(design @ beta, -30.0, 30.0)
        mu = 1.0 / (1.0 + np.exp(-eta))
        weight = np.clip(mu * (1.0 - mu), 1e-8, None)
        hessian = design.T @ (design * weight[:, None])
        gradient = design.T @ (y - mu)
        try:
            step = np.linalg.solve(hessian + np.eye(2) * 1e-10, gradient)
        except np.linalg.LinAlgError:
            return {"intercept": None, "slope": None, "ece": None}
        beta = beta + step
        if float(np.max(np.abs(step))) < 1e-9:
            break

    ece = 0.0
    for left in np.linspace(0.0, 0.9, 10):
        right = left + 0.1
        if right >= 1.0:
            mask = (p >= left) & (p <= right)
        else:
            mask = (p >= left) & (p < right)
        count = int(mask.sum())
        if count:
            ece += (count / len(p)) * abs(float(p[mask].mean() - y[mask].mean()))

    return {
        "intercept": float(beta[0]),
        "slope": float(beta[1]),
        "ece": float(ece),
    }


def _method_metrics(frame: pd.DataFrame, method: str) -> dict[str, Any]:
    if frame.empty:
        return {
            "rows": 0,
            "log_loss": None,
            "brier": None,
            "rps": None,
            "entropy": None,
            "calibration": {},
        }
    p = np.vstack(frame[f"{method}_p"].to_numpy())
    y = frame["outcome_index"].to_numpy(dtype=int)
    losses = _losses(p, y)
    calibration: dict[str, Any] = {}
    for idx, outcome_name in enumerate(OUTCOME_ORDER):
        calibration[outcome_name] = _calibration_binary(
            p[:, idx], (y == idx).astype(int)
        )
    entropy = -np.sum(p * np.log(np.clip(p, 1e-15, 1.0)), axis=1)
    return {
        "rows": int(len(frame)),
        "log_loss": float(losses["log_loss"].mean()),
        "brier": float(losses["brier"].mean()),
        "rps": float(losses["rps"].mean()),
        "entropy": float(entropy.mean()),
        "calibration": calibration,
    }


def _group_report(frame: pd.DataFrame) -> dict[str, Any]:
    common = frame[frame["common_valid"]].copy()
    pooled = {method: _method_metrics(common, method) for method in METHODS}
    by_league: dict[str, Any] = {}
    by_bookmaker: dict[str, Any] = {}
    for league in LEAGUE_ORDER:
        part = common[common["league"] == league]
        by_league[league] = {
            method: _method_metrics(part, method) for method in METHODS
        }
    for bookmaker in BOOKMAKERS:
        part = common[common["bookmaker"] == bookmaker]
        if not part.empty:
            by_bookmaker[bookmaker] = {
                method: _method_metrics(part, method) for method in METHODS
            }
    return {
        "source_rows": int(len(frame)),
        "common_rows": int(len(common)),
        "common_coverage": float(len(common) / len(frame)) if len(frame) else 0.0,
        "method_valid_coverage": {
            method: float(frame[f"{method}_valid"].mean()) if len(frame) else 0.0
            for method in METHODS
        },
        "pooled": pooled,
        "by_league": by_league,
        "by_bookmaker": by_bookmaker,
    }


def _mean_loss_delta(frame: pd.DataFrame, method: str, metric: str) -> float | None:
    common = frame[frame["common_valid"]].copy()
    if common.empty:
        return None
    p_base = np.vstack(common["multiplicative_p"].to_numpy())
    p_alt = np.vstack(common[f"{method}_p"].to_numpy())
    y = common["outcome_index"].to_numpy(dtype=int)
    base = _losses(p_base, y)[metric]
    alt = _losses(p_alt, y)[metric]
    return float(np.mean(alt - base))


def _fixture_level_delta(frame: pd.DataFrame, method: str) -> pd.DataFrame:
    common = frame[frame["common_valid"]].copy()
    if common.empty:
        return pd.DataFrame(columns=["league", "fixture_key", "delta"])
    p_base = np.vstack(common["multiplicative_p"].to_numpy())
    p_alt = np.vstack(common[f"{method}_p"].to_numpy())
    y = common["outcome_index"].to_numpy(dtype=int)
    base = _losses(p_base, y)["log_loss"]
    alt = _losses(p_alt, y)["log_loss"]
    common["delta"] = alt - base
    return (
        common.groupby(["league", "fixture_key"], as_index=False)["delta"]
        .mean()
        .sort_values(["league", "fixture_key"])
        .reset_index(drop=True)
    )


def _paired_cluster_bootstrap(frame: pd.DataFrame, method: str) -> dict[str, Any]:
    fixture = _fixture_level_delta(frame, method)
    if fixture.empty:
        return {
            "draws": BOOTSTRAP_DRAWS,
            "mean_delta": None,
            "ci95_low": None,
            "ci95_high": None,
        }
    rng = np.random.default_rng(SEED)
    groups = {
        league: part["delta"].to_numpy(dtype=float)
        for league, part in fixture.groupby("league")
    }
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for i in range(BOOTSTRAP_DRAWS):
        sampled: list[np.ndarray] = []
        for values in groups.values():
            indices = rng.integers(0, len(values), size=len(values))
            sampled.append(values[indices])
        draws[i] = float(np.concatenate(sampled).mean())
    return {
        "draws": BOOTSTRAP_DRAWS,
        "mean_delta": float(fixture["delta"].mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
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
    eligibility = {bookmaker: True for bookmaker in BOOKMAKERS}
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
                header = pd.read_csv(BytesIO(payload), nrows=0)
                columns = set(header.columns)
                row_count = int(len(pd.read_csv(BytesIO(payload), usecols=["Date"])))
                file_info: dict[str, Any] = {
                    "rows": row_count,
                    "has_outcome_column": "FTR" in columns,
                    "bookmakers": {},
                }
                for bookmaker, horizon_map in BOOKMAKERS.items():
                    missing: list[str] = []
                    for cols in horizon_map.values():
                        missing.extend(sorted(set(cols) - columns))
                    file_info["bookmakers"][bookmaker] = {
                        "missing_required_columns": sorted(set(missing))
                    }
                    if (
                        season in {VALIDATION, TEST}
                        and missing
                    ):
                        eligibility[bookmaker] = False
                source_files[f"{league}:{season}"] = file_info
    finally:
        requests.get = original_get

    included = [bookmaker for bookmaker, ok in eligibility.items() if ok]
    audit = {
        "outcome_read_before_audit": False,
        "candidate_bookmakers": list(BOOKMAKERS),
        "included_bookmakers": included,
        "excluded_bookmakers": [
            bookmaker for bookmaker in BOOKMAKERS if bookmaker not in included
        ],
        "source_files": source_files,
        "validation_test_column_gate_passed": len(included) >= 1,
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
            for cols in BOOKMAKERS[bookmaker].values():
                required.update(cols)
        frame = pd.read_csv(
            BytesIO(payload),
            usecols=lambda c: c in required,
        )
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
                    columns = BOOKMAKERS[bookmaker][horizon]
                    try:
                        odds = tuple(float(row.get(col)) for col in columns)
                    except (TypeError, ValueError):
                        continue
                    if len(odds) != 3 or any(
                        not math.isfinite(value) or value <= 1.0 for value in odds
                    ):
                        continue
                    transformed = {
                        method: TRANSFORMS[method](odds) for method in METHODS
                    }
                    record: dict[str, Any] = {
                        "league": league,
                        "season": season,
                        "split": split,
                        "fixture_key": fixture_key,
                        "bookmaker": bookmaker,
                        "horizon": horizon,
                        "outcome_index": outcome_index,
                        "overround": float(sum(1.0 / value for value in odds)),
                    }
                    valid_flags: list[bool] = []
                    for method, probabilities in transformed.items():
                        valid = probabilities is not None
                        valid_flags.append(valid)
                        record[f"{method}_valid"] = valid
                        record[f"{method}_p"] = probabilities
                    record["common_valid"] = all(valid_flags)
                    records.append(record)
    return pd.DataFrame(records)


def _validation_winner(validation_closing: pd.DataFrame) -> str | None:
    common = validation_closing[validation_closing["common_valid"]]
    if common.empty:
        return None
    baseline = _method_metrics(common, "multiplicative")["log_loss"]
    if baseline is None:
        return None

    eligible: list[tuple[float, str]] = []
    for method in ALTERNATIVES:
        coverage = float(validation_closing[f"{method}_valid"].mean())
        metric = _method_metrics(common, method)["log_loss"]
        if (
            coverage >= MIN_METHOD_COVERAGE
            and metric is not None
            and metric < baseline
        ):
            eligible.append((float(metric), method))
    if not eligible:
        return None
    eligible.sort()
    return eligible[0][1]


def _stability(frame: pd.DataFrame, method: str) -> dict[str, Any]:
    by_bookmaker: dict[str, Any] = {}
    by_league: dict[str, Any] = {}
    for bookmaker in sorted(frame["bookmaker"].unique()):
        part = frame[frame["bookmaker"] == bookmaker]
        by_bookmaker[bookmaker] = _mean_loss_delta(part, method, "log_loss")
    for league in LEAGUE_ORDER:
        part = frame[frame["league"] == league]
        by_league[league] = _mean_loss_delta(part, method, "log_loss")
    return {"by_bookmaker": by_bookmaker, "by_league": by_league}


def _confirmation_gate(
    test_closing: pd.DataFrame,
    test_opening: pd.DataFrame,
    method: str | None,
    included_bookmakers: list[str],
) -> dict[str, Any]:
    if method is None:
        return {
            "candidate": None,
            "confirmed": False,
            "reason": "NO_ALTERNATIVE_BEAT_MULTIPLICATIVE_IN_VALIDATION",
        }

    coverage = (
        float(test_closing[f"{method}_valid"].mean()) if len(test_closing) else 0.0
    )
    bootstrap = _paired_cluster_bootstrap(test_closing, method)
    deltas = {
        metric: _mean_loss_delta(test_closing, method, metric)
        for metric in ("log_loss", "brier", "rps")
    }
    opening_log_loss_delta = _mean_loss_delta(
        test_opening, method, "log_loss"
    )
    stability = _stability(test_closing, method)
    bookmaker_deltas = [
        value for value in stability["by_bookmaker"].values() if value is not None
    ]
    league_deltas = [
        value for value in stability["by_league"].values() if value is not None
    ]

    confirmed = bool(
        len(included_bookmakers) >= 2
        and coverage >= MIN_METHOD_COVERAGE
        and deltas["log_loss"] is not None
        and deltas["log_loss"] < 0.0
        and bootstrap["ci95_high"] is not None
        and bootstrap["ci95_high"] < 0.0
        and deltas["brier"] is not None
        and deltas["brier"] <= 0.0
        and deltas["rps"] is not None
        and deltas["rps"] <= 0.0
        and opening_log_loss_delta is not None
        and opening_log_loss_delta <= 0.0
        and len(bookmaker_deltas) >= 2
        and all(value < 0.0 for value in bookmaker_deltas)
        and sum(value < 0.0 for value in league_deltas) >= 2
    )
    return {
        "candidate": method,
        "confirmed": confirmed,
        "method_valid_coverage": coverage,
        "closing_deltas_vs_multiplicative": deltas,
        "opening_log_loss_delta_vs_multiplicative": opening_log_loss_delta,
        "paired_fixture_cluster_bootstrap": bootstrap,
        "stability": stability,
        "gate": {
            "at_least_two_bookmakers": len(included_bookmakers) >= 2,
            "coverage_ge_0_99": coverage >= MIN_METHOD_COVERAGE,
            "closing_log_loss_improves": (
                deltas["log_loss"] is not None and deltas["log_loss"] < 0.0
            ),
            "bootstrap_ci95_upper_below_zero": (
                bootstrap["ci95_high"] is not None
                and bootstrap["ci95_high"] < 0.0
            ),
            "brier_not_worse": (
                deltas["brier"] is not None and deltas["brier"] <= 0.0
            ),
            "rps_not_worse": (
                deltas["rps"] is not None and deltas["rps"] <= 0.0
            ),
            "opening_sensitivity_not_worse": (
                opening_log_loss_delta is not None
                and opening_log_loss_delta <= 0.0
            ),
            "both_bookmakers_improve": (
                len(bookmaker_deltas) >= 2
                and all(value < 0.0 for value in bookmaker_deltas)
            ),
            "at_least_two_leagues_improve": (
                sum(value < 0.0 for value in league_deltas) >= 2
            ),
        },
    }


def _source_gap_result(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_DEVIG_COMPARISON",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "source_audit": audit,
        "reference_rows": 0,
        "validation": {"opening": {}, "closing": {}},
        "test": {"opening": {}, "closing": {}},
        "validation_winner": None,
        "confirmation": {"candidate": None, "confirmed": False, "reason": reason},
        "supported": False,
        "decision": "BLOCKED_BY_SOURCE_GAP",
        "interpretation_guard": (
            "The frozen bookmaker/source coverage needed for the preregistered "
            "multi-bookmaker OOS comparison was not available. No proxy or paid "
            "source was substituted."
        ),
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, included_bookmakers = _download_and_audit()
    if len(included_bookmakers) < 2:
        return _source_gap_result(
            audit, "FEWER_THAN_TWO_FROZEN_BOOKMAKERS_HAVE_VALIDATION_TEST_COLUMNS"
        )

    rows = _build_rows(payloads, included_bookmakers)
    if rows.empty:
        return _source_gap_result(audit, "NO_VALID_1X2_ROWS")

    split_reports: dict[str, Any] = {}
    for split in ("validation", "test"):
        split_reports[split] = {}
        for horizon in HORIZONS:
            part = rows[
                (rows["split"] == split) & (rows["horizon"] == horizon)
            ].copy()
            split_reports[split][horizon] = _group_report(part)

    reference_rows = int((rows["split"] == "reference").sum())
    validation_closing = rows[
        (rows["split"] == "validation") & (rows["horizon"] == "closing")
    ].copy()
    test_closing = rows[
        (rows["split"] == "test") & (rows["horizon"] == "closing")
    ].copy()
    test_opening = rows[
        (rows["split"] == "test") & (rows["horizon"] == "opening")
    ].copy()

    winner = _validation_winner(validation_closing)
    confirmation = _confirmation_gate(
        test_closing, test_opening, winner, included_bookmakers
    )

    if confirmation["confirmed"]:
        decision = "PROJECT_BEST_DEVIG_CANDIDATE"
        interpretation = (
            f"{winner} was selected on frozen 2024/25 validation closing odds and "
            "then confirmed against multiplicative normalization on untouched "
            "2025/26 closing odds with paired fixture-cluster uncertainty, both "
            "bookmakers, and cross-league stability. This is a research candidate "
            "only; it is not production promotion or a betting edge."
        )
    else:
        decision = "NO_STABLE_DEVIG_WINNER"
        interpretation = (
            "No alternative de-vig method cleared every frozen validation-selection "
            "and untouched OOT confirmation gate against multiplicative normalization. "
            "Do not replace the current market anchor on these results."
        )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "TEMPORAL_OOS_DEVIG_COMPARISON",
        "research_only": True,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "methods": list(METHODS),
        "primary_horizon": "closing",
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "untouched_test": TEST,
            "validation_selects_candidate": True,
            "test_selects_candidate": False,
        },
        "source_audit": {
            **audit,
            "outcome_read_after_audit": True,
        },
        "reference_rows": reference_rows,
        "validation": split_reports["validation"],
        "test": split_reports["test"],
        "validation_winner": winner,
        "confirmation": confirmation,
        "supported": bool(confirmation["confirmed"]),
        "decision": decision,
        "interpretation_guard": interpretation,
        "result": "RESEARCH_ONLY_NO_BET",
    }


if __name__ == "__main__":
    import json

    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
