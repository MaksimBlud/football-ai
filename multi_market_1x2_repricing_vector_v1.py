"""Deterministic multi-market state -> future 1X2 repricing-vector evaluator (#573).

Research-only and outcome-free. The baseline sees only contemporaneous 1X2
market geometry; the candidate additionally sees O/U 2.5 and Asian Handicap
state. Both predict later closing 1X2 repricing in two log-ratio coordinates.
"""
from __future__ import annotations

import math
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import requests
from scipy.stats import pearsonr, spearmanr
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from bookmaker_reconstruction_devig_v1 import power
from cross_league_direct_markets_transport import _official_or_pinned_mirror_get
from cross_market_lead_lag_replication_transport import _replication_get

EXPERIMENT_ID = "MULTI_MARKET_1X2_REPRICING_VECTOR_V1"
BASE = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"
LEAGUES = {
    "EPL": "E0",
    "LA_LIGA": "SP1",
    "SERIE_A": "I1",
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}
SEASON_CODES = {
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}
REFERENCE = tuple(f"{y}-{y + 1}" for y in range(2019, 2024))
VALIDATION = "2024-2025"
TEST = "2025-2026"
MIN_CELL_ROWS = 100
MIN_REFERENCE_SEASONS = 3
MIN_ELIGIBLE_LEAGUES = 4
BOOTSTRAP_DRAWS = 5000
SEED = 20261007

REQUIRED_FIXED_COLUMNS = (
    "B365H", "B365D", "B365A",
    "B365CH", "B365CD", "B365CA",
    "B365>2.5", "B365<2.5",
    "B365AHH", "B365AHA",
)
AH_LINE_COLUMNS = ("AHh", "B365AH")
BASELINE_FEATURES = ("p_home", "p_draw", "p_away")
CANDIDATE_FEATURES = (
    "p_home", "p_draw", "p_away",
    "p_over_2_5", "ah_line", "p_ah_home",
)
TARGET_COLUMNS = ("move_home_vs_draw", "move_away_vs_draw")


def _transport_get(url: str, *args, **kwargs):
    if url.endswith("/D1.csv") or url.endswith("/F1.csv"):
        return _replication_get(url, *args, **kwargs)
    return _official_or_pinned_mirror_get(url, *args, **kwargs)


def _finite_gt_one(frame: pd.DataFrame, columns) -> np.ndarray:
    values = frame[list(columns)].apply(
        pd.to_numeric, errors="coerce"
    ).to_numpy(float)
    return np.isfinite(values).all(axis=1) & (values > 1.0).all(axis=1)


def _proportional_two_way(first: np.ndarray, second: np.ndarray) -> np.ndarray:
    first = np.asarray(first, dtype=float)
    second = np.asarray(second, dtype=float)
    a = 1.0 / first
    b = 1.0 / second
    return a / (a + b)


def _power_probabilities(odds: np.ndarray) -> np.ndarray:
    odds = np.asarray(odds, dtype=float)
    if odds.ndim != 2 or odds.shape[1] != 3:
        raise ValueError("1X2 odds must have shape (n, 3)")
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("1X2 odds must be finite and > 1")
    return power(1.0 / odds)


def _line_columns(columns: set[str]) -> list[str]:
    return [column for column in AH_LINE_COLUMNS if column in columns]


def _cell_frame(payload: bytes, line_columns: list[str]) -> pd.DataFrame:
    columns = list(REQUIRED_FIXED_COLUMNS) + list(line_columns)
    frame = pd.read_csv(BytesIO(payload), usecols=columns)
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame


def _ah_line(frame: pd.DataFrame, line_columns: list[str]) -> np.ndarray:
    if not line_columns:
        return np.full(len(frame), np.nan)
    line = pd.to_numeric(
        frame[line_columns[0]], errors="coerce"
    ).to_numpy(float)
    for column in line_columns[1:]:
        fallback = pd.to_numeric(frame[column], errors="coerce").to_numpy(float)
        line = np.where(np.isfinite(line), line, fallback)
    return line


def _eligible_mask(frame: pd.DataFrame, line_columns: list[str]) -> np.ndarray:
    return (
        _finite_gt_one(frame, ("B365H", "B365D", "B365A"))
        & _finite_gt_one(frame, ("B365CH", "B365CD", "B365CA"))
        & _finite_gt_one(frame, ("B365>2.5", "B365<2.5"))
        & _finite_gt_one(frame, ("B365AHH", "B365AHA"))
        & np.isfinite(_ah_line(frame, line_columns))
    )


def _download_and_audit() -> tuple[
    dict[tuple[str, str], bytes], dict[str, Any], bool
]:
    """Freeze schema/coverage before computing any closing movement target."""
    payloads: dict[tuple[str, str], bytes] = {}
    files: dict[str, Any] = {}
    original_get = requests.get
    try:
        requests.get = _transport_get
        for league, competition in LEAGUES.items():
            for code, season in SEASON_CODES.items():
                response = requests.get(
                    BASE.format(code=code, competition=competition), timeout=60
                )
                response.raise_for_status()
                payload = response.content
                payloads[(league, season)] = payload

                header = pd.read_csv(BytesIO(payload), nrows=0)
                columns = set(header.columns)
                missing = sorted(set(REQUIRED_FIXED_COLUMNS) - columns)
                line_columns = _line_columns(columns)
                if not line_columns:
                    missing.append("AHh|B365AH")

                raw_rows = int(
                    len(pd.read_csv(BytesIO(payload), usecols=[header.columns[0]]))
                )
                eligible_rows = 0
                if not missing:
                    frame = _cell_frame(payload, line_columns)
                    eligible_rows = int(_eligible_mask(frame, line_columns).sum())

                files[f"{league}:{season}"] = {
                    "missing_required_columns": missing,
                    "ah_line_columns": line_columns,
                    "raw_rows": raw_rows,
                    "eligible_rows": eligible_rows,
                    "eligible_fraction": (
                        float(eligible_rows / raw_rows) if raw_rows else 0.0
                    ),
                    "minimum_required_rows": MIN_CELL_ROWS,
                    "cell_usable": bool(
                        not missing and eligible_rows >= MIN_CELL_ROWS
                    ),
                }
    finally:
        requests.get = original_get

    eligible_leagues: list[str] = []
    frozen_cells: dict[str, list[str]] = {}
    excluded_leagues: dict[str, Any] = {}
    for league in LEAGUES:
        ref = [
            season for season in REFERENCE
            if files[f"{league}:{season}"]["cell_usable"]
        ]
        validation_ok = files[f"{league}:{VALIDATION}"]["cell_usable"]
        test_ok = files[f"{league}:{TEST}"]["cell_usable"]
        ok = (
            len(ref) >= MIN_REFERENCE_SEASONS
            and validation_ok
            and test_ok
        )
        if ok:
            eligible_leagues.append(league)
            frozen_cells[league] = [*ref, VALIDATION, TEST]
        else:
            excluded_leagues[league] = {
                "usable_reference_seasons": ref,
                "validation_usable": validation_ok,
                "test_usable": test_ok,
            }

    source_gate = len(eligible_leagues) >= MIN_ELIGIBLE_LEAGUES
    audit = {
        "outcome_columns_loaded": False,
        "match_outcomes_used": False,
        "closing_movement_computed_during_audit": False,
        "files": files,
        "minimum_cell_rows": MIN_CELL_ROWS,
        "minimum_reference_seasons": MIN_REFERENCE_SEASONS,
        "minimum_eligible_leagues": MIN_ELIGIBLE_LEAGUES,
        "eligible_leagues": eligible_leagues,
        "excluded_leagues": excluded_leagues,
        "frozen_cells": frozen_cells,
        "source_gate_passed": source_gate,
        "standard_odds_are_exact_opening": False,
        "standard_state_name": "STANDARD/PRE-CLOSE",
    }
    return payloads, audit, source_gate


def _build_rows(
    payloads: dict[tuple[str, str], bytes],
    audit: dict[str, Any],
) -> pd.DataFrame:
    parts: list[pd.DataFrame] = []
    for league in audit["eligible_leagues"]:
        for season in audit["frozen_cells"][league]:
            payload = payloads[(league, season)]
            meta = audit["files"][f"{league}:{season}"]
            line_columns = list(meta["ah_line_columns"])
            if not line_columns:
                raise RuntimeError("frozen usable cell has no AH line column")
            frame = _cell_frame(payload, line_columns)
            local = frame.loc[_eligible_mask(frame, line_columns)].copy()
            if len(local) < MIN_CELL_ROWS:
                raise RuntimeError("frozen usable cell lost required coverage")

            standard_odds = local[["B365H", "B365D", "B365A"]].to_numpy(float)
            closing_odds = local[
                ["B365CH", "B365CD", "B365CA"]
            ].to_numpy(float)
            p_standard = _power_probabilities(standard_odds)
            p_close = _power_probabilities(closing_odds)
            p_over = _proportional_two_way(
                local["B365>2.5"].to_numpy(float),
                local["B365<2.5"].to_numpy(float),
            )
            p_ah_home = _proportional_two_way(
                local["B365AHH"].to_numpy(float),
                local["B365AHA"].to_numpy(float),
            )
            ah_line = _ah_line(local, line_columns)

            move_home = (
                np.log(p_close[:, 0] / p_close[:, 1])
                - np.log(p_standard[:, 0] / p_standard[:, 1])
            )
            move_away = (
                np.log(p_close[:, 2] / p_close[:, 1])
                - np.log(p_standard[:, 2] / p_standard[:, 1])
            )
            parts.append(
                pd.DataFrame(
                    {
                        "league": league,
                        "season": season,
                        "source_row": local.index.to_numpy(int),
                        "p_home": p_standard[:, 0],
                        "p_draw": p_standard[:, 1],
                        "p_away": p_standard[:, 2],
                        "p_over_2_5": p_over,
                        "ah_line": ah_line,
                        "p_ah_home": p_ah_home,
                        "move_home_vs_draw": move_home,
                        "move_away_vs_draw": move_away,
                    }
                )
            )
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=10.0)),
        ]
    )


def _fit_pair(train: pd.DataFrame, features) -> list[Pipeline]:
    targets = train[list(TARGET_COLUMNS)].to_numpy(float)
    models = []
    for index in range(2):
        model = _model()
        model.fit(train[list(features)], targets[:, index])
        models.append(model)
    return models


def _predict_pair(models, frame: pd.DataFrame, features) -> np.ndarray:
    return np.column_stack(
        [model.predict(frame[list(features)]) for model in models]
    )


def _safe_corr(
    actual: np.ndarray, predicted: np.ndarray, method: str
) -> float | None:
    if len(actual) < 3 or np.std(actual) == 0 or np.std(predicted) == 0:
        return None
    value = (
        pearsonr(actual, predicted).statistic
        if method == "pearson"
        else spearmanr(actual, predicted).statistic
    )
    return float(value) if math.isfinite(float(value)) else None


def _diagnostics(target: np.ndarray, predicted: np.ndarray) -> dict[str, Any]:
    coordinates = {}
    for index, name in enumerate(TARGET_COLUMNS):
        actual = target[:, index]
        pred = predicted[:, index]
        nonzero = ~np.isclose(actual, 0.0, atol=1e-12)
        coordinates[name] = {
            "pearson": _safe_corr(actual, pred, "pearson"),
            "spearman": _safe_corr(actual, pred, "spearman"),
            "nonzero_rows": int(nonzero.sum()),
            "sign_accuracy_nonzero": (
                float(
                    (
                        np.sign(actual[nonzero])
                        == np.sign(pred[nonzero])
                    ).mean()
                )
                if nonzero.any()
                else None
            ),
        }
    return {
        "coordinates": coordinates,
        "strongest_move_coordinate_accuracy": float(
            (
                np.argmax(np.abs(target), axis=1)
                == np.argmax(np.abs(predicted), axis=1)
            ).mean()
        ),
    }


def _evaluate_split(
    frame: pd.DataFrame,
    baseline_models,
    candidate_models,
) -> tuple[dict[str, Any], pd.DataFrame]:
    target = frame[list(TARGET_COLUMNS)].to_numpy(float)
    baseline = _predict_pair(baseline_models, frame, BASELINE_FEATURES)
    candidate = _predict_pair(candidate_models, frame, CANDIDATE_FEATURES)

    baseline_sq = np.mean((baseline - target) ** 2, axis=1)
    candidate_sq = np.mean((candidate - target) ** 2, axis=1)
    baseline_abs = np.mean(np.abs(baseline - target), axis=1)
    candidate_abs = np.mean(np.abs(candidate - target), axis=1)

    losses = frame[["league", "season", "source_row"]].copy()
    losses["squared_error_delta"] = candidate_sq - baseline_sq
    losses["absolute_error_delta"] = candidate_abs - baseline_abs

    by_league = {
        league: {
            "rows": int(len(part)),
            "candidate_minus_baseline_mse": float(
                part["squared_error_delta"].mean()
            ),
            "candidate_minus_baseline_mae": float(
                part["absolute_error_delta"].mean()
            ),
        }
        for league, part in losses.groupby("league")
    }
    report = {
        "rows": int(len(frame)),
        "baseline_mse": float(baseline_sq.mean()),
        "candidate_mse": float(candidate_sq.mean()),
        "candidate_minus_baseline_mse": float(
            (candidate_sq - baseline_sq).mean()
        ),
        "baseline_mae": float(baseline_abs.mean()),
        "candidate_mae": float(candidate_abs.mean()),
        "candidate_minus_baseline_mae": float(
            (candidate_abs - baseline_abs).mean()
        ),
        "by_league": by_league,
        "baseline_diagnostics": _diagnostics(target, baseline),
        "candidate_diagnostics": _diagnostics(target, candidate),
    }
    return report, losses


def _bootstrap(losses: pd.DataFrame) -> dict[str, Any]:
    groups = [
        part["squared_error_delta"].to_numpy(float)
        for _, part in losses.groupby("league")
    ]
    if not groups or any(len(values) == 0 for values in groups):
        return {
            "draws": BOOTSTRAP_DRAWS,
            "seed": SEED,
            "ci95_low": None,
            "ci95_high": None,
        }
    rng = np.random.default_rng(SEED)
    draws = np.empty(BOOTSTRAP_DRAWS)
    for index in range(BOOTSTRAP_DRAWS):
        sample = np.concatenate(
            [
                values[rng.integers(0, len(values), len(values))]
                for values in groups
            ]
        )
        draws[index] = float(sample.mean())
    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": SEED,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
    }


def _formal_gate(
    validation: dict[str, Any],
    test: dict[str, Any],
    *,
    source_gate: bool,
    eligible_leagues: int,
) -> dict[str, Any]:
    league_deltas = [
        item["candidate_minus_baseline_mse"]
        for item in test.get("by_league", {}).values()
    ]
    positive_leagues = sum(value > 0 for value in league_deltas)
    gates = {
        "source_gate_passed": source_gate,
        "at_least_four_eligible_leagues": (
            eligible_leagues >= MIN_ELIGIBLE_LEAGUES
        ),
        "validation_mse_improves": (
            validation.get("candidate_minus_baseline_mse", 0.0) < 0.0
        ),
        "validation_mae_improves": (
            validation.get("candidate_minus_baseline_mae", 0.0) < 0.0
        ),
        "test_mse_improves": (
            test.get("candidate_minus_baseline_mse", 0.0) < 0.0
        ),
        "test_mae_improves": (
            test.get("candidate_minus_baseline_mae", 0.0) < 0.0
        ),
        "test_mse_ci95_upper_below_zero": (
            test.get("bootstrap", {}).get("ci95_high") is not None
            and test["bootstrap"]["ci95_high"] < 0.0
        ),
        "test_positive_mse_leagues_at_most_one": (
            len(league_deltas) == eligible_leagues
            and positive_leagues <= 1
        ),
    }
    return {
        "supported": all(gates.values()),
        "gates": gates,
        "positive_test_mse_leagues": positive_leagues,
    }


def _empty_split() -> dict[str, Any]:
    return {
        "rows": 0,
        "baseline_mse": None,
        "candidate_mse": None,
        "candidate_minus_baseline_mse": None,
        "baseline_mae": None,
        "candidate_mae": None,
        "candidate_minus_baseline_mae": None,
        "by_league": {},
        "baseline_diagnostics": {},
        "candidate_diagnostics": {},
    }


def _blocked(audit: dict[str, Any], reason: str) -> dict[str, Any]:
    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": (
            "RETROSPECTIVE_PREREGISTERED_MARKET_REPRICING_REPRESENTATION"
        ),
        "research_only": True,
        "match_outcomes_used": False,
        "opened_2026_27_outcomes_used": False,
        "source_audit": audit,
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "test": TEST,
            "test_refit_includes_validation": True,
        },
        "validation": _empty_split(),
        "test": {
            **_empty_split(),
            "bootstrap": {
                "draws": BOOTSTRAP_DRAWS,
                "seed": SEED,
                "ci95_low": None,
                "ci95_high": None,
            },
        },
        "formal_gate": {
            "supported": False,
            "reason": reason,
            "gates": {},
        },
        "supported": False,
        "decision": "BLOCKED_BY_SOURCE_GAP",
        "interpretation_guard": reason,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate_payloads(
    payloads: dict[tuple[str, str], bytes],
    audit: dict[str, Any],
    source_gate: bool,
) -> dict[str, Any]:
    if not source_gate:
        return _blocked(
            audit,
            "Fewer than four frozen leagues satisfy the zero-cost "
            "market source/coverage gate.",
        )
    try:
        data = _build_rows(payloads, audit)
    except (ValueError, RuntimeError) as exc:
        return _blocked(
            audit,
            "Frozen market transform/source reconstruction failed: "
            f"{type(exc).__name__}: {exc}",
        )
    if data.empty:
        return _blocked(audit, "Frozen eligible market rows are empty.")

    reference = data[data["season"].isin(REFERENCE)].copy()
    validation_frame = data[data["season"] == VALIDATION].copy()
    test_frame = data[data["season"] == TEST].copy()
    if min(len(reference), len(validation_frame), len(test_frame)) == 0:
        return _blocked(audit, "Frozen temporal split is empty.")

    val_baseline = _fit_pair(reference, BASELINE_FEATURES)
    val_candidate = _fit_pair(reference, CANDIDATE_FEATURES)
    validation, _ = _evaluate_split(
        validation_frame, val_baseline, val_candidate
    )

    test_train = pd.concat([reference, validation_frame], ignore_index=True)
    test_baseline = _fit_pair(test_train, BASELINE_FEATURES)
    test_candidate = _fit_pair(test_train, CANDIDATE_FEATURES)
    test, test_losses = _evaluate_split(
        test_frame, test_baseline, test_candidate
    )
    test["bootstrap"] = _bootstrap(test_losses)

    eligible_leagues = list(audit["eligible_leagues"])
    gate = _formal_gate(
        validation,
        test,
        source_gate=True,
        eligible_leagues=len(eligible_leagues),
    )
    supported = bool(gate["supported"])

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": (
            "RETROSPECTIVE_PREREGISTERED_MARKET_REPRICING_REPRESENTATION"
        ),
        "research_only": True,
        "match_outcomes_used": False,
        "opened_2026_27_outcomes_used": False,
        "source_audit": audit,
        "temporal_design": {
            "reference": list(REFERENCE),
            "validation": VALIDATION,
            "test": TEST,
            "validation_fit": "reference_only",
            "test_fit": "reference_plus_validation",
            "historical_closing_targets_previously_opened_by_related_research": True,
            "untouched_confirmation_claim": False,
        },
        "representation_contract": {
            "one_x_two_devig": "POWER",
            "ou25_devig": "PROPORTIONAL",
            "ah_devig": "PROPORTIONAL",
            "baseline_features": list(BASELINE_FEATURES),
            "candidate_features": list(CANDIDATE_FEATURES),
            "targets": list(TARGET_COLUMNS),
            "ridge_alpha": 10.0,
            "standard_odds_are_exact_opening": False,
        },
        "validation": validation,
        "test": test,
        "formal_gate": gate,
        "supported": supported,
        "decision": (
            "REPRICING_STATE_SUPPORTED_FOR_PROSPECTIVE_CONFIRMATION"
            if supported
            else "NO_STABLE_MULTI_MARKET_REPRICING_SIGNAL"
        ),
        "interpretation_guard": (
            "The frozen direct O/U+AH augmentation passed every "
            "retrospective gate versus the identical 1X2-only baseline. "
            "Because the historical closing targets were opened by related "
            "research, this only justifies a separately frozen prospective "
            "confirmation; it is not betting or production evidence."
            if supported
            else
            "The frozen direct multi-market representation failed at least "
            "one validation, retrospective-test, uncertainty or cross-league "
            "gate. Do not rescue it by changing features, Ridge alpha, AH "
            "scope, target coordinates, league subset, sign rules or by "
            "adding corners to the same opened history."
        ),
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "production_operations": False,
        "production_promotion": False,
        "result": "RESEARCH_ONLY_NO_BET",
    }


def evaluate() -> dict[str, Any]:
    payloads, audit, source_gate = _download_and_audit()
    return evaluate_payloads(payloads, audit, source_gate)


if __name__ == "__main__":
    import json
    print(json.dumps(evaluate(), indent=2, ensure_ascii=False))
