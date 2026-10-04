"""CROSS_MARKET_LEAD_LAG_V1.

Historical open->close proxy for cross-market lead-lag:
does Bet365 opening O/U + AH imply the direction of later Bet365 closing 1X2?

Research-only, NO_BET, outcome-free, no 2026/27 data.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from historical_football_signal_runner import BASE, LEAGUES
from cross_market_score_coherence_v1 import (
    AH_COLUMNS,
    AH_LINE_COLUMNS,
    ONE_X_TWO_COLUMNS,
    TOTAL_COLUMNS,
    _binary_devig,
    _first_line,
    _is_half_goal_line,
    _reconstruct,
    _three_way_devig,
    _valid_prices,
)

EXPERIMENT_ID = "CROSS_MARKET_LEAD_LAG_V1"
LEAGUE_IDS = ("EPL", "LA_LIGA", "SERIE_A")
REFERENCE_SEASONS = tuple(f"{year}-{year + 1}" for year in range(2019, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
ALLOWED_SEASONS = set(REFERENCE_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}

CLOSING_1X2_COLUMNS = ("B365CH", "B365CD", "B365CA")
MIN_ROWS_PER_LEAGUE = 40
PERMUTATION_DRAWS = 10000
BOOTSTRAP_DRAWS = 10000
RANDOM_SEED = 20261004
EPS = 1e-15

# These fields may physically exist in the source CSV but V1 does not use them.
OUTCOME_COLUMNS = {
    "FTHG",
    "FTAG",
    "FTR",
    "HTHG",
    "HTAG",
    "HTR",
    "HS",
    "AS",
    "HST",
    "AST",
    "HC",
    "AC",
}


def _download_league_raw(league: str) -> pd.DataFrame:
    config = LEAGUES[league]
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

    # Outcome fields are explicitly removed before any feature or target logic.
    raw = raw.drop(columns=[c for c in OUTCOME_COLUMNS if c in raw.columns])

    return raw.sort_values(
        ["season", "match_date", "HomeTeam", "AwayTeam"],
        kind="stable",
    ).reset_index(drop=True)


def _build_league_rows(
    raw: pd.DataFrame,
    league: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    coverage: dict[str, dict[str, int]] = {}
    failures = Counter()
    line_distribution = Counter()
    fit_methods = Counter()

    for season in sorted(ALLOWED_SEASONS):
        source_rows = int((raw["season"].astype(str) == season).sum())
        coverage[season] = {
            "source_rows": source_rows,
            "complete_open_close_same_book_rows": 0,
            "half_goal_ah_rows": 0,
            "reconstructed_rows": 0,
        }

    for _, row in raw.iterrows():
        season = str(row.get("season"))
        if season not in coverage:
            continue

        opening_1x2 = _valid_prices(row, ONE_X_TWO_COLUMNS)
        closing_1x2 = _valid_prices(row, CLOSING_1X2_COLUMNS)
        total = _valid_prices(row, TOTAL_COLUMNS)
        ah = _valid_prices(row, AH_COLUMNS)
        line_info = _first_line(row)

        if (
            opening_1x2 is None
            or closing_1x2 is None
            or total is None
            or ah is None
            or line_info is None
        ):
            continue

        coverage[season]["complete_open_close_same_book_rows"] += 1

        ah_line, line_source = line_info
        if not _is_half_goal_line(ah_line):
            continue

        coverage[season]["half_goal_ah_rows"] += 1

        try:
            p_open = _three_way_devig(opening_1x2)
            p_close = _three_way_devig(closing_1x2)
            p_over25 = _binary_devig(total[0], total[1])
            p_ah_home = _binary_devig(ah[0], ah[1])
            reconstructed = _reconstruct(
                p_over25,
                ah_line,
                p_ah_home,
            )
        except (ValueError, RuntimeError) as exc:
            failures[f"{type(exc).__name__}:{exc}"] += 1
            continue

        p_score = np.asarray(
            [
                reconstructed["score_home_prob"],
                reconstructed["score_draw_prob"],
                reconstructed["score_away_prob"],
            ],
            dtype=float,
        )

        lead = p_score - p_open
        move = p_close - p_open
        alignment_dot = float(np.dot(lead, move))
        lead_norm = float(np.linalg.norm(lead))
        move_norm = float(np.linalg.norm(move))

        if lead_norm > EPS and move_norm > EPS:
            alignment_cosine = float(
                alignment_dot / (lead_norm * move_norm)
            )
        else:
            alignment_cosine = None

        gap_open_tv = float(
            0.5 * np.abs(p_score - p_open).sum()
        )
        gap_close_to_open_score_tv = float(
            0.5 * np.abs(p_score - p_close).sum()
        )
        gap_reduction_tv = float(
            gap_open_tv - gap_close_to_open_score_tv
        )
        move_tv = float(
            0.5 * np.abs(p_close - p_open).sum()
        )

        rows.append(
            {
                "league": league,
                "season": season,
                "match_date": row.get("match_date"),
                "home_team": str(row.get("HomeTeam")),
                "away_team": str(row.get("AwayTeam")),
                "ah_line": float(ah_line),
                "ah_line_source": line_source,
                "open_home_prob": float(p_open[0]),
                "open_draw_prob": float(p_open[1]),
                "open_away_prob": float(p_open[2]),
                "close_home_prob": float(p_close[0]),
                "close_draw_prob": float(p_close[1]),
                "close_away_prob": float(p_close[2]),
                "score_home_prob": float(p_score[0]),
                "score_draw_prob": float(p_score[1]),
                "score_away_prob": float(p_score[2]),
                "lead_home": float(lead[0]),
                "lead_draw": float(lead[1]),
                "lead_away": float(lead[2]),
                "move_home": float(move[0]),
                "move_draw": float(move[1]),
                "move_away": float(move[2]),
                "lead_norm": lead_norm,
                "move_norm": move_norm,
                "alignment_dot": alignment_dot,
                "alignment_cosine": alignment_cosine,
                "positive_alignment": bool(alignment_dot > 0.0),
                "gap_open_tv": gap_open_tv,
                "gap_close_to_open_score_tv": gap_close_to_open_score_tv,
                "gap_reduction_tv": gap_reduction_tv,
                "open_to_close_move_tv": move_tv,
                "over25_prob": float(p_over25),
                "ah_home_prob": float(p_ah_home),
                "lambda_total": float(reconstructed["lambda_total"]),
                "lambda_home": float(reconstructed["lambda_home"]),
                "lambda_away": float(reconstructed["lambda_away"]),
                "ah_fit_abs_error": float(reconstructed["ah_fit_abs_error"]),
                "ah_fit_method": str(reconstructed["ah_fit_method"]),
            }
        )
        coverage[season]["reconstructed_rows"] += 1
        line_distribution[f"{ah_line:+.1f}"] += 1
        fit_methods[str(reconstructed["ah_fit_method"])] += 1

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"{league}: no lead-lag rows")

    return frame, {
        "source_rows": int(len(raw)),
        "lead_lag_rows": int(len(frame)),
        "by_season": coverage,
        "ah_line_distribution": dict(sorted(line_distribution.items())),
        "ah_fit_method_distribution": dict(sorted(fit_methods.items())),
        "reconstruction_failures": dict(failures),
    }


def _component_correlations(frame: pd.DataFrame) -> dict[str, dict[str, float | None]]:
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


def _permutation_test(frame: pd.DataFrame) -> dict[str, float | int]:
    if frame.empty:
        raise ValueError("permutation frame is empty")

    observed = float(frame["alignment_dot"].mean())
    rng = np.random.default_rng(RANDOM_SEED)

    move = frame[["move_home", "move_draw", "move_away"]].to_numpy(dtype=float)
    lead = frame[["lead_home", "lead_draw", "lead_away"]].to_numpy(dtype=float)
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
            permuted_lead[indices] = lead[
                rng.permutation(indices)
            ]
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

    for league in LEAGUE_IDS:
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
    validation = _split_report(
        combined,
        VALIDATION_SEASON,
    )

    validation_admissible = bool(
        validation["rows_ok"]
        and validation["mean_alignment_dot"] > 0.0
        and validation["positive_mean_alignment_leagues"] >= 2
        and validation["permutation"]["one_sided_p"] < 0.05
    )

    test = _split_report(
        combined,
        TEST_SEASON,
    )
    test_gate = bool(
        test["rows_ok"]
        and test["mean_alignment_dot"] > 0.0
        and test["positive_mean_alignment_leagues"] >= 2
        and test["permutation"]["one_sided_p"] < 0.05
        and test["bootstrap"]["ci95_low"] > 0.0
    )

    supported = bool(validation_admissible and test_gate)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_OPEN_CLOSE_LEAD_LAG_PROXY",
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "match_outcomes_used": False,
        "opened_2026_27_data_used": False,
        "paid_odds_api_calls": 0,
        "supabase_writes": 0,
        "live_intraday_source_audit": {
            "league_multi_market_snapshot_rows": 2,
            "unique_events": 2,
            "snapshots_per_event": 1,
            "observed_league": "EREDIVISIE",
            "provider_market_keys": ["spreads", "totals"],
            "true_intraday_lead_lag_feasible": False,
        },
        "same_bookmaker": "BET365",
        "reference_seasons": list(REFERENCE_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "source_contract": {
            "opening_1x2": list(ONE_X_TWO_COLUMNS),
            "opening_total": list(TOTAL_COLUMNS),
            "opening_ah": list(AH_COLUMNS),
            "opening_ah_line": list(AH_LINE_COLUMNS),
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
        "supported": supported,
        "decision": (
            "OPEN_CROSS_MARKET_LEADS_CLOSE_1X2_SUPPORTED"
            if supported
            else "NO_OPEN_TO_CLOSE_CROSS_MARKET_LEAD_SIGNAL"
        ),
        "result": "NO_BET",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/cross_market_lead_lag_v1/report.json"
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
