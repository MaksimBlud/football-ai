"""Independent Bundesliga/Ligue 1 replication of CROSS_MARKET_LEAD_LAG_V1.

Research-only. The protocol is preregistered in
research/CROSS_MARKET_LEAD_LAG_INDEPENDENT_REPLICATION_V1.md.
No match outcomes, 2026/27 data, paid provider calls, Supabase writes, model
training, or production promotion are allowed.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

import cross_market_lead_lag_v1 as parent
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from ligue1_runtime_config import LIGUE1_RUNTIME_CONFIG
from historical_football_signal_runner import BASE


EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_INDEPENDENT_REPLICATION_V1"
PARENT_EXPERIMENT_ID = parent.EXPERIMENT_ID
LEAGUE_IDS = ("BUNDESLIGA", "LIGUE_1")
LEAGUE_CONFIGS = {
    "BUNDESLIGA": BUNDESLIGA_RUNTIME_CONFIG,
    "LIGUE_1": LIGUE1_RUNTIME_CONFIG,
}

REFERENCE_SEASONS = parent.REFERENCE_SEASONS
VALIDATION_SEASON = parent.VALIDATION_SEASON
TEST_SEASON = parent.TEST_SEASON
ALLOWED_SEASONS = set(REFERENCE_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}

CLOSING_1X2_COLUMNS = parent.CLOSING_1X2_COLUMNS
MIN_ROWS_PER_LEAGUE = parent.MIN_ROWS_PER_LEAGUE
PERMUTATION_DRAWS = parent.PERMUTATION_DRAWS
BOOTSTRAP_DRAWS = parent.BOOTSTRAP_DRAWS
RANDOM_SEED = parent.RANDOM_SEED
OUTCOME_COLUMNS = parent.OUTCOME_COLUMNS


def _download_league_raw(league: str) -> pd.DataFrame:
    """Download only the frozen seasons and remove outcome fields immediately."""
    config = LEAGUE_CONFIGS[league]
    frames: list[pd.DataFrame] = []

    for code, season in config.historical_source.season_codes.items():
        if season not in ALLOWED_SEASONS:
            continue

        response = requests.get(
            BASE.format(
                code=code,
                comp=config.historical_source.competition_code,
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

    # Outcome / post-match fields are physically present in Football-Data but
    # are deleted before the frozen feature/target logic can inspect them.
    raw = raw.drop(
        columns=[column for column in OUTCOME_COLUMNS if column in raw.columns]
    )

    forbidden = OUTCOME_COLUMNS.intersection(raw.columns)
    if forbidden:
        raise RuntimeError(
            f"{league}: forbidden outcome columns survived drop: {sorted(forbidden)}"
        )

    return raw.sort_values(
        ["season", "match_date", "HomeTeam", "AwayTeam"],
        kind="stable",
    ).reset_index(drop=True)


def _permutation_test(frame: pd.DataFrame) -> dict[str, float | int]:
    """Exact V1 shuffled-link null, transferred unchanged to two leagues."""
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
        for league in LEAGUE_IDS
    }
    if any(len(indices) == 0 for indices in groups.values()):
        raise RuntimeError("permutation split missing a frozen league")

    draws = np.empty(PERMUTATION_DRAWS, dtype=float)
    for draw in range(PERMUTATION_DRAWS):
        permuted_lead = lead.copy()
        for indices in groups.values():
            permuted_lead[indices] = lead[rng.permutation(indices)]
        dots = np.sum(permuted_lead * move, axis=1)
        draws[draw] = float(dots.mean())

    p_one_sided = float(
        (1 + np.sum(draws >= observed))
        / (PERMUTATION_DRAWS + 1)
    )
    return {
        "draws": PERMUTATION_DRAWS,
        "seed": RANDOM_SEED,
        "observed_mean_alignment_dot": observed,
        "null_mean": float(draws.mean()),
        "null_ci95_low": float(np.quantile(draws, 0.025)),
        "null_ci95_high": float(np.quantile(draws, 0.975)),
        "one_sided_p": p_one_sided,
    }


def _bootstrap_mean_alignment(frame: pd.DataFrame) -> dict[str, float | int]:
    """Exact V1 stratified bootstrap, with the frozen replication leagues."""
    if frame.empty:
        raise ValueError("bootstrap frame is empty")

    rng = np.random.default_rng(RANDOM_SEED)
    groups = {
        league: frame.loc[
            frame["league"].astype(str) == league,
            "alignment_dot",
        ].to_numpy(dtype=float)
        for league in LEAGUE_IDS
    }
    if any(len(values) == 0 for values in groups.values()):
        raise RuntimeError("bootstrap split missing a frozen league")

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
        raise RuntimeError(f"{season}: empty lead-lag split")

    by_league: dict[str, dict[str, object]] = {}
    positive_leagues = 0
    rows_ok = True

    for league in LEAGUE_IDS:
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
        "league_count": len(LEAGUE_IDS),
        "minimum_rows_per_league": MIN_ROWS_PER_LEAGUE,
        "rows_ok": bool(rows_ok),
        "by_league": by_league,
        "component_correlations": parent._component_correlations(split),
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
    frames: list[pd.DataFrame] = []
    coverage: dict[str, object] = {}

    for league in LEAGUE_IDS:
        raw = _download_league_raw(league)
        league_frame, league_coverage = parent._build_league_rows(raw, league)
        frames.append(league_frame)
        coverage[league] = league_coverage

    combined = pd.concat(frames, ignore_index=True)
    reference = combined[
        combined["season"].astype(str).isin(REFERENCE_SEASONS)
    ].copy()

    validation = _split_report(combined, VALIDATION_SEASON)
    test = _split_report(combined, TEST_SEASON)

    sample_gate = bool(validation["rows_ok"] and test["rows_ok"])

    validation_admissible = bool(
        validation["rows_ok"]
        and validation["mean_alignment_dot"] > 0.0
        and validation["positive_mean_alignment_leagues"] == len(LEAGUE_IDS)
        and validation["permutation"]["one_sided_p"] < 0.05
    )

    test_gate = bool(
        test["rows_ok"]
        and test["mean_alignment_dot"] > 0.0
        and test["positive_mean_alignment_leagues"] == len(LEAGUE_IDS)
        and test["permutation"]["one_sided_p"] < 0.05
        and test["bootstrap"]["ci95_low"] > 0.0
    )

    supported = bool(validation_admissible and test_gate)

    if not sample_gate:
        decision = "INSUFFICIENT_SAMPLE"
    elif supported:
        decision = "INDEPENDENT_LEAGUE_REPLICATION_SUPPORTED"
    else:
        decision = "INDEPENDENT_LEAGUE_REPLICATION_NOT_SUPPORTED"

    return {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "evidence_class": "INDEPENDENT_HISTORICAL_OPEN_CLOSE_LEAD_LAG_REPLICATION",
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_reads": 0,
        "supabase_writes": 0,
        "same_bookmaker": "BET365",
        "replication_leagues": list(LEAGUE_IDS),
        "reference_seasons": list(REFERENCE_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "source_contract": {
            "opening_1x2": list(parent.ONE_X_TWO_COLUMNS),
            "opening_total": list(parent.TOTAL_COLUMNS),
            "opening_ah": list(parent.AH_COLUMNS),
            "opening_ah_line": list(parent.AH_LINE_COLUMNS),
            "closing_1x2": list(CLOSING_1X2_COLUMNS),
            "half_goal_ah_only": True,
        },
        "primary_statistic": "alignment_dot",
        "primary_null": "within_league_permutation_of_opening_lead_vectors",
        "coverage": coverage,
        "reference_feature_only": {
            "rows": int(len(reference)),
            "mean_alignment_dot": float(reference["alignment_dot"].mean()),
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
        "sample_gate": sample_gate,
        "supported": supported,
        "decision": decision,
        "result": "NO_BET",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/"
            "cross_market_lead_lag_independent_replication_v1/"
            "report.json"
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
