"""MARKET_DEVIG_BOOKMAKER_TIMING_V1.

Research-only comparison of de-vig methods by Football-Data bookmaker/source
and standard/closing price columns. Zero paid API calls and no production writes.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from market_devig_methods_v1 import (
    ALTERNATIVES,
    METHODS,
    apply_method,
    per_match_losses,
)


EXPERIMENT_ID = "MARKET_DEVIG_BOOKMAKER_TIMING_V1"
OUTPUT_DIR = Path("artifacts/market_devig_bookmaker_timing_v1")
OUTPUT_PATH = OUTPUT_DIR / "report.json"

SEASON_CODES = {
    "2019/2020": "1920",
    "2020/2021": "2021",
    "2021/2022": "2122",
    "2022/2023": "2223",
    "2023/2024": "2324",
    "2024/2025": "2425",
    "2025/2026": "2526",
}
SEASONS = list(SEASON_CODES)
DISCOVERY_SEASONS = SEASONS[:5]
VALIDATION_SEASON = "2024/2025"
TEST_SEASON = "2025/2026"

SOURCE_COLUMNS = {
    "AVG_STANDARD": ("AvgH", "AvgD", "AvgA"),
    "BET365_STANDARD": ("B365H", "B365D", "B365A"),
    "PINNACLE_STANDARD": ("PSH", "PSD", "PSA"),
    "AVG_CLOSING": ("AvgCH", "AvgCD", "AvgCA"),
    "BET365_CLOSING": ("B365CH", "B365CD", "B365CA"),
    "PINNACLE_CLOSING": ("PSCH", "PSCD", "PSCA"),
}

MIN_SEASON_COVERAGE = 0.90
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/E0.csv"


def download_history() -> pd.DataFrame:
    frames = []
    for season, code in SEASON_CODES.items():
        url = BASE_URL.format(code=code)
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        frame = pd.read_csv(io.BytesIO(response.content))
        if len(frame) != 380:
            raise RuntimeError(
                f"{season}: expected 380 EPL rows, got {len(frame)}"
            )
        frame = frame.copy()
        frame["season"] = season
        frame["_season_row"] = np.arange(len(frame), dtype=int)
        frames.append(frame)

    combined = pd.concat(frames, ignore_index=True)
    if len(combined) != 2660:
        raise RuntimeError(f"Expected 2660 rows, got {len(combined)}")
    if not combined["FTR"].astype(str).isin(["H", "D", "A"]).all():
        raise RuntimeError("Historical outcomes contain invalid values")
    return combined


def source_valid_mask(frame: pd.DataFrame, source: str) -> pd.Series:
    columns = SOURCE_COLUMNS[source]
    if not all(column in frame.columns for column in columns):
        return pd.Series(False, index=frame.index, dtype=bool)

    odds = frame[list(columns)].apply(pd.to_numeric, errors="coerce")
    return odds.gt(1.0).all(axis=1)


def source_availability(frame: pd.DataFrame, source: str) -> dict:
    columns = SOURCE_COLUMNS[source]
    columns_present = all(column in frame.columns for column in columns)
    mask = source_valid_mask(frame, source)

    by_season = {}
    eligible = columns_present
    for season in SEASONS:
        season_mask = frame["season"].eq(season)
        total = int(season_mask.sum())
        valid = int((season_mask & mask).sum())
        coverage = valid / total if total else 0.0
        by_season[season] = {
            "rows": total,
            "valid_rows": valid,
            "coverage": coverage,
        }
        if coverage < MIN_SEASON_COVERAGE:
            eligible = False

    return {
        "columns": list(columns),
        "columns_present": columns_present,
        "minimum_required_coverage": MIN_SEASON_COVERAGE,
        "by_season": by_season,
        "eligible": bool(eligible),
        "valid_rows_total": int(mask.sum()),
    }


def source_frame(frame: pd.DataFrame, source: str) -> pd.DataFrame:
    columns = SOURCE_COLUMNS[source]
    mask = source_valid_mask(frame, source)
    selected = frame.loc[
        mask,
        ["season", "_season_row", "FTR", *columns],
    ].copy()
    selected = selected.rename(
        columns={
            columns[0]: "home_odds",
            columns[1]: "draw_odds",
            columns[2]: "away_odds",
            "FTR": "result",
        }
    )
    for column in ("home_odds", "draw_odds", "away_odds"):
        selected[column] = pd.to_numeric(selected[column], errors="raise")
    return selected.reset_index(drop=True)


def score(frame: pd.DataFrame, method: str) -> tuple[dict, pd.DataFrame]:
    probabilities, details = apply_method(frame, method)
    losses = per_match_losses(frame, probabilities)
    return {
        "matches": int(len(frame)),
        "logloss": float(losses["logloss"].mean()),
        "brier": float(losses["brier"].mean()),
        "accuracy": float(
            (
                probabilities.argmax(axis=1)
                == frame["result"].map({"H": 0, "D": 1, "A": 2}).to_numpy()
            ).mean()
        ),
        "mean_overround": float(details["overround"].mean()),
        "mean_power_k": (
            float(details["k"].mean())
            if method == "POWER"
            else None
        ),
        "mean_shin_z": (
            float(details["z"].mean())
            if method == "SHIN"
            else None
        ),
    }, losses.reset_index(drop=True)


def evaluate_source(frame: pd.DataFrame) -> tuple[dict, dict[str, pd.DataFrame]]:
    reports = {}
    losses = {}
    for method in METHODS:
        overall, method_losses = score(frame, method)
        by_season = {}
        for season in SEASONS:
            season_frame = frame[frame["season"].eq(season)].reset_index(drop=True)
            season_report, _ = score(season_frame, method)
            by_season[season] = season_report
        reports[method] = {"overall": overall, "by_season": by_season}
        losses[method] = method_losses
    return reports, losses


def _weighted_window(reports: dict, method: str, seasons: list[str]) -> dict:
    rows = [reports[method]["by_season"][season] for season in seasons]
    weights = np.asarray([row["matches"] for row in rows], dtype=float)
    return {
        "matches": int(weights.sum()),
        "logloss": float(
            np.average([row["logloss"] for row in rows], weights=weights)
        ),
        "brier": float(
            np.average([row["brier"] for row in rows], weights=weights)
        ),
    }


def select_method(reports: dict) -> tuple[str, dict]:
    baseline = _weighted_window(
        reports,
        "MULTIPLICATIVE",
        DISCOVERY_SEASONS,
    )
    alternatives = {}

    for method in ALTERNATIVES:
        metrics = _weighted_window(reports, method, DISCOVERY_SEASONS)
        joint_wins = 0
        deltas = {}
        for season in DISCOVERY_SEASONS:
            base = reports["MULTIPLICATIVE"]["by_season"][season]
            candidate = reports[method]["by_season"][season]
            dll = candidate["logloss"] - base["logloss"]
            db = candidate["brier"] - base["brier"]
            if dll < 0.0 and db < 0.0:
                joint_wins += 1
            deltas[season] = {"logloss": float(dll), "brier": float(db)}

        eligible = bool(
            metrics["logloss"] < baseline["logloss"]
            and metrics["brier"] < baseline["brier"]
            and joint_wins >= 3
        )
        alternatives[method] = {
            **metrics,
            "delta_logloss_vs_multiplicative":
                metrics["logloss"] - baseline["logloss"],
            "delta_brier_vs_multiplicative":
                metrics["brier"] - baseline["brier"],
            "joint_season_wins": joint_wins,
            "eligible": eligible,
            "season_deltas": deltas,
        }

    eligible = [
        method for method in ALTERNATIVES
        if alternatives[method]["eligible"]
    ]
    selected = (
        min(
            eligible,
            key=lambda method: (
                alternatives[method]["logloss"],
                alternatives[method]["brier"],
                method,
            ),
        )
        if eligible
        else "MULTIPLICATIVE"
    )
    return selected, {
        "baseline": baseline,
        "alternatives": alternatives,
    }


def bootstrap_delta(
    candidate: pd.DataFrame,
    baseline: pd.DataFrame,
    metric: str,
) -> dict:
    delta = (
        candidate[metric].to_numpy(dtype=float)
        - baseline[metric].to_numpy(dtype=float)
    )
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    n = len(delta)
    means = np.empty(BOOTSTRAP_SAMPLES, dtype=float)
    for index in range(BOOTSTRAP_SAMPLES):
        sample = rng.integers(0, n, size=n)
        means[index] = float(delta[sample].mean())
    return {
        "mean_delta_candidate_minus_baseline": float(delta.mean()),
        "ci95_low": float(np.quantile(means, 0.025)),
        "ci95_high": float(np.quantile(means, 0.975)),
        "bootstrap_probability_candidate_better": float((means < 0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def evaluate_source_family(
    source: str,
    frame: pd.DataFrame,
    availability: dict,
) -> dict:
    if not availability["eligible"]:
        return {
            "source": source,
            "availability": availability,
            "evaluated": False,
            "interpretation": "SOURCE_UNAVAILABLE",
        }

    local = source_frame(frame, source)
    reports, losses = evaluate_source(local)
    selected, discovery = select_method(reports)

    base_val = reports["MULTIPLICATIVE"]["by_season"][VALIDATION_SEASON]
    cand_val = reports[selected]["by_season"][VALIDATION_SEASON]
    validation_pass = bool(
        selected != "MULTIPLICATIVE"
        and cand_val["logloss"] < base_val["logloss"]
        and cand_val["brier"] < base_val["brier"]
    )

    base_test = reports["MULTIPLICATIVE"]["by_season"][TEST_SEASON]
    cand_test = reports[selected]["by_season"][TEST_SEASON]
    test_pass = bool(
        selected != "MULTIPLICATIVE"
        and cand_test["logloss"] < base_test["logloss"]
        and cand_test["brier"] < base_test["brier"]
    )

    bootstrap = {
        metric: bootstrap_delta(
            losses[selected],
            losses["MULTIPLICATIVE"],
            metric,
        )
        for metric in ("logloss", "brier")
    }
    alternative_bootstrap = {
        method: {
            metric: bootstrap_delta(
                losses[method],
                losses["MULTIPLICATIVE"],
                metric,
            )
            for metric in ("logloss", "brier")
        }
        for method in ALTERNATIVES
    }

    robust = bool(
        selected != "MULTIPLICATIVE"
        and validation_pass
        and test_pass
        and bootstrap["logloss"]["ci95_high"] < 0.0
        and bootstrap["brier"]["ci95_high"] < 0.0
    )

    return {
        "source": source,
        "availability": availability,
        "evaluated": True,
        "selected_on_discovery": selected,
        "discovery": discovery,
        "validation": {
            "baseline": {
                "logloss": base_val["logloss"],
                "brier": base_val["brier"],
            },
            "candidate": {
                "logloss": cand_val["logloss"],
                "brier": cand_val["brier"],
            },
            "passed": validation_pass,
        },
        "test": {
            "baseline": {
                "logloss": base_test["logloss"],
                "brier": base_test["brier"],
            },
            "candidate": {
                "logloss": cand_test["logloss"],
                "brier": cand_test["brier"],
            },
            "passed": test_pass,
        },
        "selected_bootstrap": bootstrap,
        "alternative_bootstrap": alternative_bootstrap,
        "all_methods": reports,
        "robust_support": robust,
        "interpretation": (
            "ROBUST_SOURCE_DEVIG_SUPPORT"
            if robust
            else "KEEP_SOURCE_MULTIPLICATIVE"
        ),
    }


def common_fixture_diagnostic(
    frame: pd.DataFrame,
    availability: dict[str, dict],
) -> dict:
    eligible = [
        source for source, info in availability.items()
        if info["eligible"]
    ]
    if not eligible:
        return {
            "eligible_sources": [],
            "common_rows": 0,
            "by_source": {},
        }

    mask = pd.Series(True, index=frame.index, dtype=bool)
    for source in eligible:
        mask &= source_valid_mask(frame, source)

    common_raw = frame.loc[mask].copy()
    by_source = {}
    for source in eligible:
        columns = SOURCE_COLUMNS[source]
        local = common_raw[
            ["season", "_season_row", "FTR", *columns]
        ].rename(
            columns={
                columns[0]: "home_odds",
                columns[1]: "draw_odds",
                columns[2]: "away_odds",
                "FTR": "result",
            }
        ).reset_index(drop=True)
        report, _ = score(local, "MULTIPLICATIVE")
        by_source[source] = report

    return {
        "eligible_sources": eligible,
        "common_rows": int(len(common_raw)),
        "by_source": by_source,
    }


def evaluate(frame: pd.DataFrame) -> dict:
    availability = {
        source: source_availability(frame, source)
        for source in SOURCE_COLUMNS
    }
    source_reports = {
        source: evaluate_source_family(
            source,
            frame,
            availability[source],
        )
        for source in SOURCE_COLUMNS
    }

    supported = [
        source for source, report in source_reports.items()
        if report.get("robust_support") is True
    ]

    return {
        "availability": availability,
        "source_reports": source_reports,
        "supported_sources": supported,
        "common_fixture_diagnostic": common_fixture_diagnostic(
            frame,
            availability,
        ),
        "interpretation": (
            "SOURCE_SPECIFIC_DEVIG_SUPPORT"
            if supported
            else "NO_SOURCE_SPECIFIC_DEVIG_SUPPORT"
        ),
    }


def main() -> int:
    frame = download_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_HOLDOUT",
        "research_only": True,
        "production_promotion": False,
        "supabase_reads": False,
        "supabase_writes": False,
        "paid_odds_api_calls": False,
        "candidate_artifact_saved": False,
        "source": "Football-Data EPL CSV",
        "seasons": SEASONS,
        "source_rows": int(len(frame)),
        "source_columns": {
            key: list(value)
            for key, value in SOURCE_COLUMNS.items()
        },
        "minimum_season_coverage": MIN_SEASON_COVERAGE,
        "result": result,
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "requests": requests.__version__,
        },
    }

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    print("Research only; zero paid API calls; production unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
