"""CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1.

Post-hoc, outcome-free season stability audit for the already-frozen V1/V2
alignment_dot statistic across EPL, La Liga, Serie A, Bundesliga and Ligue 1.

This module cannot create confirmatory support or authorize paid acquisition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

import cross_market_lead_lag_v1 as v1
import cross_market_lead_lag_replication_v2 as v2
from cross_league_direct_markets_transport import (
    _official_or_pinned_mirror_get as _primary_transport_get,
)
from cross_market_lead_lag_replication_transport import (
    _replication_get,
)

EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_REGIME_AUDIT_V1"
LEAGUES = ("EPL", "LA_LIGA", "SERIE_A", "BUNDESLIGA", "LIGUE_1")
SEASONS = (
    "2019-2020",
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
)
TARGET_SEASON = "2025-2026"
PRIOR_SEASONS = SEASONS[:-1]
PERMUTATION_DRAWS = 10000
BOOTSTRAP_DRAWS = 10000
RANDOM_SEED = 20261004


def _load_all_rows() -> tuple[pd.DataFrame, dict[str, Any]]:
    original_get = requests.get
    frames: list[pd.DataFrame] = []
    coverage: dict[str, Any] = {}

    try:
        requests.get = _primary_transport_get
        for league in ("EPL", "LA_LIGA", "SERIE_A"):
            raw = v1._download_league_raw(league)
            frame, cov = v1._build_league_rows(raw, league)
            frames.append(frame)
            coverage[league] = cov

        requests.get = _replication_get
        for league in ("BUNDESLIGA", "LIGUE_1"):
            raw = v2._download_league_raw(league)
            frame, cov = v1._build_league_rows(raw, league)
            frames.append(frame)
            coverage[league] = cov
    finally:
        requests.get = original_get

    combined = pd.concat(frames, ignore_index=True)
    combined["league"] = combined["league"].astype(str)
    combined["season"] = combined["season"].astype(str)

    unexpected_leagues = set(combined["league"]) - set(LEAGUES)
    unexpected_seasons = set(combined["season"]) - set(SEASONS)
    if unexpected_leagues:
        raise RuntimeError(
            f"unexpected regime-audit leagues: {sorted(unexpected_leagues)}"
        )
    if unexpected_seasons:
        raise RuntimeError(
            f"unexpected regime-audit seasons: {sorted(unexpected_seasons)}"
        )

    for league in LEAGUES:
        for season in SEASONS:
            if not (
                (combined["league"] == league)
                & (combined["season"] == season)
            ).any():
                raise RuntimeError(
                    f"missing frozen league-season cell: {league}/{season}"
                )

    return combined, coverage


def _component_correlations(
    frame: pd.DataFrame,
) -> dict[str, dict[str, float | None]]:
    result: dict[str, dict[str, float | None]] = {}
    for outcome in ("home", "draw", "away"):
        x = frame[f"lead_{outcome}"].astype(float)
        y = frame[f"move_{outcome}"].astype(float)
        pearson = float(x.corr(y, method="pearson"))
        spearman = float(x.corr(y, method="spearman"))
        result[outcome] = {
            "pearson": pearson if np.isfinite(pearson) else None,
            "spearman": spearman if np.isfinite(spearman) else None,
        }
    return result


def _season_permutation(
    frame: pd.DataFrame,
) -> dict[str, float | int]:
    if frame.empty:
        raise ValueError("season permutation frame is empty")

    rng = np.random.default_rng(RANDOM_SEED)
    observed = float(frame["alignment_dot"].mean())
    lead = frame[
        ["lead_home", "lead_draw", "lead_away"]
    ].to_numpy(dtype=float)
    move = frame[
        ["move_home", "move_draw", "move_away"]
    ].to_numpy(dtype=float)
    leagues = frame["league"].astype(str).to_numpy()
    groups = {
        league: np.flatnonzero(leagues == league)
        for league in LEAGUES
    }
    if any(len(indices) == 0 for indices in groups.values()):
        raise RuntimeError("season permutation missing frozen league")

    draws = np.empty(PERMUTATION_DRAWS, dtype=float)
    for draw in range(PERMUTATION_DRAWS):
        permuted = lead.copy()
        for indices in groups.values():
            permuted[indices] = lead[
                rng.permutation(indices)
            ]
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


def _season_bootstrap(
    frame: pd.DataFrame,
) -> dict[str, float | int]:
    if frame.empty:
        raise ValueError("season bootstrap frame is empty")

    rng = np.random.default_rng(RANDOM_SEED)
    groups = {
        league: frame.loc[
            frame["league"] == league,
            "alignment_dot",
        ].to_numpy(dtype=float)
        for league in LEAGUES
    }
    if any(len(values) == 0 for values in groups.values()):
        raise RuntimeError("season bootstrap missing frozen league")

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


def _season_report(
    combined: pd.DataFrame,
    season: str,
) -> dict[str, Any]:
    frame = combined[combined["season"] == season].copy()
    if frame.empty:
        raise RuntimeError(f"{season}: empty season frame")

    by_league: dict[str, dict[str, Any]] = {}
    positive_leagues = 0

    for league in LEAGUES:
        local = frame[frame["league"] == league]
        if local.empty:
            raise RuntimeError(
                f"{season}: missing {league} rows"
            )
        mean_alignment = float(local["alignment_dot"].mean())
        positive_leagues += int(mean_alignment > 0.0)
        by_league[league] = {
            "rows": int(len(local)),
            "mean_alignment_dot": mean_alignment,
            "median_alignment_dot": float(
                local["alignment_dot"].median()
            ),
            "positive_alignment_rate": float(
                local["positive_alignment"].mean()
            ),
            "mean_gap_open_tv": float(
                local["gap_open_tv"].mean()
            ),
            "mean_gap_reduction_tv": float(
                local["gap_reduction_tv"].mean()
            ),
            "mean_open_to_close_move_tv": float(
                local["open_to_close_move_tv"].mean()
            ),
        }

    return {
        "season": season,
        "rows": int(len(frame)),
        "mean_alignment_dot": float(
            frame["alignment_dot"].mean()
        ),
        "median_alignment_dot": float(
            frame["alignment_dot"].median()
        ),
        "positive_alignment_rate": float(
            frame["positive_alignment"].mean()
        ),
        "positive_mean_alignment_leagues": int(
            positive_leagues
        ),
        "league_count": len(LEAGUES),
        "by_league": by_league,
        "mean_gap_open_tv": float(
            frame["gap_open_tv"].mean()
        ),
        "mean_gap_reduction_tv": float(
            frame["gap_reduction_tv"].mean()
        ),
        "mean_open_to_close_move_tv": float(
            frame["open_to_close_move_tv"].mean()
        ),
        "component_correlations": _component_correlations(
            frame
        ),
        "permutation": _season_permutation(frame),
        "bootstrap": _season_bootstrap(frame),
    }


def _target_minus_prior_bootstrap(
    combined: pd.DataFrame,
) -> dict[str, Any]:
    target = combined[
        combined["season"] == TARGET_SEASON
    ].copy()
    prior = combined[
        combined["season"].isin(PRIOR_SEASONS)
    ].copy()

    if target.empty or prior.empty:
        raise RuntimeError("target/prior audit sample empty")

    rng = np.random.default_rng(RANDOM_SEED)
    target_groups = {
        league: target.loc[
            target["league"] == league,
            "alignment_dot",
        ].to_numpy(dtype=float)
        for league in LEAGUES
    }
    prior_groups = {
        league: prior.loc[
            prior["league"] == league,
            "alignment_dot",
        ].to_numpy(dtype=float)
        for league in LEAGUES
    }

    if any(
        len(target_groups[league]) == 0
        or len(prior_groups[league]) == 0
        for league in LEAGUES
    ):
        raise RuntimeError(
            "target/prior bootstrap missing frozen league"
        )

    target_total_rows = sum(
        len(values) for values in target_groups.values()
    )
    prior_total_rows = sum(
        len(values) for values in prior_groups.values()
    )

    draws = np.empty(BOOTSTRAP_DRAWS, dtype=float)
    for draw in range(BOOTSTRAP_DRAWS):
        target_sum = 0.0
        prior_sum = 0.0
        for league in LEAGUES:
            t = target_groups[league]
            p = prior_groups[league]
            target_sum += float(
                rng.choice(t, size=len(t), replace=True).sum()
            )
            prior_sum += float(
                rng.choice(p, size=len(p), replace=True).sum()
            )
        draws[draw] = (
            target_sum / target_total_rows
            - prior_sum / prior_total_rows
        )

    observed = float(
        target["alignment_dot"].mean()
        - prior["alignment_dot"].mean()
    )

    by_league = {}
    positive_differences = 0
    for league in LEAGUES:
        target_mean = float(
            target.loc[
                target["league"] == league,
                "alignment_dot",
            ].mean()
        )
        prior_mean = float(
            prior.loc[
                prior["league"] == league,
                "alignment_dot",
            ].mean()
        )
        delta = target_mean - prior_mean
        positive_differences += int(delta > 0.0)
        by_league[league] = {
            "target_2025_26_mean": target_mean,
            "prior_2019_20_to_2024_25_mean": prior_mean,
            "target_minus_prior": delta,
        }

    return {
        "target_season": TARGET_SEASON,
        "target_rows": int(len(target)),
        "prior_rows": int(len(prior)),
        "target_mean_alignment_dot": float(
            target["alignment_dot"].mean()
        ),
        "prior_mean_alignment_dot": float(
            prior["alignment_dot"].mean()
        ),
        "observed_target_minus_prior": observed,
        "bootstrap_draws": BOOTSTRAP_DRAWS,
        "seed": RANDOM_SEED,
        "bootstrap_ci95_low": float(
            np.quantile(draws, 0.025)
        ),
        "bootstrap_ci95_high": float(
            np.quantile(draws, 0.975)
        ),
        "bootstrap_probability_positive": float(
            (draws > 0.0).mean()
        ),
        "positive_within_league_differences": int(
            positive_differences
        ),
        "by_league": by_league,
    }


def evaluate() -> dict[str, Any]:
    combined, coverage = _load_all_rows()

    season_reports = {
        season: _season_report(combined, season)
        for season in SEASONS
    }

    means = {
        season: float(
            season_reports[season]["mean_alignment_dot"]
        )
        for season in SEASONS
    }
    league_counts = {
        season: int(
            season_reports[season][
                "positive_mean_alignment_leagues"
            ]
        )
        for season in SEASONS
    }

    target_mean = means[TARGET_SEASON]
    target_league_count = league_counts[TARGET_SEASON]

    mean_rank = (
        1
        + sum(
            value > target_mean
            for season, value in means.items()
            if season != TARGET_SEASON
        )
    )
    league_count_rank = (
        1
        + sum(
            value > target_league_count
            for season, value in league_counts.items()
            if season != TARGET_SEASON
        )
    )

    exceptionality = _target_minus_prior_bootstrap(
        combined
    )

    broad_pattern = bool(
        target_mean > 0.0
        and target_league_count >= 4
        and exceptionality[
            "observed_target_minus_prior"
        ] > 0.0
    )

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "POSTHOC_REGIME_STABILITY_DIAGNOSTIC",
        "research_only": True,
        "posthoc": True,
        "confirmatory_support_allowed": False,
        "betting_enabled": False,
        "production_promotion": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "inherited_statistic": "alignment_dot",
        "inherited_seed": RANDOM_SEED,
        "leagues": list(LEAGUES),
        "seasons": list(SEASONS),
        "rows": int(len(combined)),
        "coverage": coverage,
        "season_reports": season_reports,
        "target_2025_26_exceptionality": {
            **exceptionality,
            "mean_alignment_rank_among_7_seasons": int(
                mean_rank
            ),
            "positive_league_count_rank_among_7_seasons": int(
                league_count_rank
            ),
        },
        "diagnostic_label": (
            "BROAD_2025_26_POSITIVE_REGIME_PATTERN"
            if broad_pattern
            else "NO_BROAD_2025_26_REGIME_PATTERN"
        ),
        "formal_v1_v2_decisions_unchanged": True,
        "result": "NO_BET",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/cross_market_lead_lag_regime_audit_v1/report.json"
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
