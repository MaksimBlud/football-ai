"""CROSS_MARKET_LEAD_LAG_REPLICATION_V2.

Independent-league, outcome-free replication of the frozen V1 opening
cross-market -> closing 1X2 alignment statistic on Bundesliga and Ligue 1.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from historical_football_signal_runner import BASE
from cross_market_lead_lag_v1 import (
    BOOTSTRAP_DRAWS,
    MIN_ROWS_PER_LEAGUE,
    OUTCOME_COLUMNS,
    PERMUTATION_DRAWS,
    RANDOM_SEED,
    _build_league_rows,
    _component_correlations,
)

EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_REPLICATION_V2"
REPLICATION_LEAGUES = ("BUNDESLIGA", "LIGUE_1")
REFERENCE_SEASONS = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
ALLOWED_SEASONS = set(REFERENCE_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}

SEASON_CODES = {
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}
COMPETITION_CODES = {
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}


def _download_league_raw(league: str) -> pd.DataFrame:
    if league not in COMPETITION_CODES:
        raise ValueError(f"unsupported replication league: {league}")

    competition_code = COMPETITION_CODES[league]
    frames: list[pd.DataFrame] = []

    for code, season in SEASON_CODES.items():
        if season not in ALLOWED_SEASONS:
            continue

        response = requests.get(
            BASE.format(
                code=code,
                comp=competition_code,
            ),
            timeout=60,
        )
        response.raise_for_status()
        frame = pd.read_csv(pd.io.common.BytesIO(response.content))
        frame["season"] = season
        frames.append(frame)

    if not frames:
        raise RuntimeError(f"{league}: no historical source frames")

    raw = pd.concat(frames, ignore_index=True)
    raw["match_date"] = pd.to_datetime(
        raw.get("Date"),
        dayfirst=True,
        errors="coerce",
    )

    raw = raw.drop(
        columns=[c for c in OUTCOME_COLUMNS if c in raw.columns],
    )

    return raw.sort_values(
        ["season", "match_date", "HomeTeam", "AwayTeam"],
        kind="stable",
    ).reset_index(drop=True)


def _permutation_test(frame: pd.DataFrame) -> dict[str, float | int]:
    if frame.empty:
        raise ValueError("permutation frame is empty")

    observed = float(frame["alignment_dot"].mean())
    rng = np.random.default_rng(RANDOM_SEED)

    move = frame[
        ["move_home", "move_draw", "move_away"]
    ].to_numpy(dtype=float)
    lead = frame[
        ["lead_home", "lead_draw", "lead_away"]
    ].to_numpy(dtype=float)
    leagues = frame["league"].astype(str).to_numpy()

    groups = {
        league: np.flatnonzero(leagues == league)
        for league in REPLICATION_LEAGUES
    }
    if any(len(indices) == 0 for indices in groups.values()):
        raise RuntimeError("replication permutation missing a frozen league")

    draws = np.empty(PERMUTATION_DRAWS, dtype=float)
    for draw in range(PERMUTATION_DRAWS):
        permuted = lead.copy()
        for indices in groups.values():
            permuted[indices] = lead[rng.permutation(indices)]
        draws[draw] = float(
            np.sum(permuted * move, axis=1).mean()
        )

    return {
        "draws": PERMUTATION_DRAWS,
        "seed": RANDOM_SEED,
        "observed_mean_alignment_dot": observed,
        "null_mean": float(draws.mean()),
        "null_ci95_low": float(np.quantile(draws, 0.025)),
        "null_ci95_high": float(np.quantile(draws, 0.975)),
        "one_sided_p": float(
            (1 + np.sum(draws >= observed))
            / (PERMUTATION_DRAWS + 1)
        ),
    }


def _bootstrap_mean_alignment(
    frame: pd.DataFrame,
) -> dict[str, float | int]:
    if frame.empty:
        raise ValueError("bootstrap frame is empty")

    rng = np.random.default_rng(RANDOM_SEED)
    groups = {
        league: frame.loc[
            frame["league"].astype(str) == league,
            "alignment_dot",
        ].to_numpy(dtype=float)
        for league in REPLICATION_LEAGUES
    }
    if any(len(values) == 0 for values in groups.values()):
        raise RuntimeError("replication bootstrap missing a frozen league")

    total_rows = sum(len(values) for values in groups.values())
    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)

    for draw in range(BOOTSTRAP_DRAWS):
        total = 0.0
        for values in groups.values():
            total += float(
                rng.choice(
                    values,
                    size=len(values),
                    replace=True,
                ).sum()
            )
        draws[draw] = total / total_rows

    return {
        "draws": BOOTSTRAP_DRAWS,
        "seed": RANDOM_SEED,
        "mean": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "probability_positive": float((draws > 0.0).mean()),
    }


def _split_report(
    frame: pd.DataFrame,
    season: str,
) -> dict[str, object]:
    split = frame[frame["season"].astype(str) == season].copy()
    if split.empty:
        raise RuntimeError(f"{season}: empty replication split")

    by_league: dict[str, dict[str, object]] = {}
    positive_leagues = 0
    rows_ok = True

    for league in REPLICATION_LEAGUES:
        local = split[split["league"] == league]
        mean_alignment = (
            float(local["alignment_dot"].mean())
            if len(local)
            else None
        )
        positive_leagues += int(
            mean_alignment is not None and mean_alignment > 0.0
        )
        rows_ok = rows_ok and len(local) >= MIN_ROWS_PER_LEAGUE

        by_league[league] = {
            "rows": int(len(local)),
            "mean_alignment_dot": mean_alignment,
            "median_alignment_dot": (
                float(local["alignment_dot"].median())
                if len(local)
                else None
            ),
            "positive_alignment_rate": (
                float(local["positive_alignment"].mean())
                if len(local)
                else None
            ),
            "mean_gap_open_tv": (
                float(local["gap_open_tv"].mean())
                if len(local)
                else None
            ),
            "mean_gap_reduction_tv": (
                float(local["gap_reduction_tv"].mean())
                if len(local)
                else None
            ),
            "mean_open_to_close_move_tv": (
                float(local["open_to_close_move_tv"].mean())
                if len(local)
                else None
            ),
        }

    permutation = _permutation_test(split)
    bootstrap = _bootstrap_mean_alignment(split)

    return {
        "season": season,
        "rows": int(len(split)),
        "mean_alignment_dot": float(split["alignment_dot"].mean()),
        "median_alignment_dot": float(split["alignment_dot"].median()),
        "positive_alignment_rate": float(
            split["positive_alignment"].mean()
        ),
        "mean_alignment_cosine": (
            float(split["alignment_cosine"].dropna().mean())
            if split["alignment_cosine"].notna().any()
            else None
        ),
        "mean_gap_open_tv": float(split["gap_open_tv"].mean()),
        "mean_gap_close_to_open_score_tv": float(
            split["gap_close_to_open_score_tv"].mean()
        ),
        "mean_gap_reduction_tv": float(
            split["gap_reduction_tv"].mean()
        ),
        "mean_open_to_close_move_tv": float(
            split["open_to_close_move_tv"].mean()
        ),
        "positive_mean_alignment_leagues": int(positive_leagues),
        "league_count": len(REPLICATION_LEAGUES),
        "minimum_rows_per_league": MIN_ROWS_PER_LEAGUE,
        "rows_ok": bool(rows_ok),
        "by_league": by_league,
        "component_correlations": _component_correlations(split),
        "permutation": permutation,
        "bootstrap": bootstrap,
        "ah_fit_abs_error": {
            "mean": float(split["ah_fit_abs_error"].mean()),
            "median": float(split["ah_fit_abs_error"].median()),
            "p95": float(split["ah_fit_abs_error"].quantile(0.95)),
            "max": float(split["ah_fit_abs_error"].max()),
        },
    }


def evaluate() -> dict[str, object]:
    frames = []
    coverage: dict[str, object] = {}

    for league in REPLICATION_LEAGUES:
        raw = _download_league_raw(league)
        league_frame, league_coverage = _build_league_rows(
            raw,
            league,
        )
        frames.append(league_frame)
        coverage[league] = league_coverage

    combined = pd.concat(frames, ignore_index=True)

    reference = combined[
        combined["season"].astype(str).isin(REFERENCE_SEASONS)
    ].copy()

    validation = _split_report(combined, VALIDATION_SEASON)
    validation_admissible = bool(
        validation["rows_ok"]
        and validation["mean_alignment_dot"] > 0.0
        and validation["positive_mean_alignment_leagues"]
        == len(REPLICATION_LEAGUES)
        and validation["permutation"]["one_sided_p"] < 0.05
    )

    test = _split_report(combined, TEST_SEASON)
    test_gate = bool(
        test["rows_ok"]
        and test["mean_alignment_dot"] > 0.0
        and test["positive_mean_alignment_leagues"]
        == len(REPLICATION_LEAGUES)
        and test["permutation"]["one_sided_p"] < 0.05
        and test["bootstrap"]["ci95_low"] > 0.0
    )

    supported = bool(validation_admissible and test_gate)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_LEAGUE_HISTORICAL_OPEN_CLOSE_REPLICATION",
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "inherited_from": "CROSS_MARKET_LEAD_LAG_V1",
        "inherited_primary_statistic": "alignment_dot",
        "inherited_seed": RANDOM_SEED,
        "replication_leagues": list(REPLICATION_LEAGUES),
        "reference_seasons": list(REFERENCE_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "coverage": coverage,
        "reference_feature_only": {
            "rows": int(len(reference)),
            "mean_alignment_dot": float(
                reference["alignment_dot"].mean()
            ),
            "positive_alignment_rate": float(
                reference["positive_alignment"].mean()
            ),
            "mean_gap_reduction_tv": float(
                reference["gap_reduction_tv"].mean()
            ),
        },
        "validation": validation,
        "validation_admissible": validation_admissible,
        "test": test,
        "test_gate": test_gate,
        "supported": supported,
        "decision": (
            "INDEPENDENT_LEAGUE_LEAD_LAG_REPLICATION_SUPPORTED"
            if supported
            else "LEAD_LAG_REPLICATION_NOT_SUPPORTED"
        ),
        "result": "NO_BET",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/cross_market_lead_lag_replication_v2/report.json"
        ),
    )
    args = parser.parse_args()

    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
