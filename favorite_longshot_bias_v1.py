"""FAVORITE_LONGSHOT_BIAS_V1.

Research-only cross-league test of probability-dependent Bet365 1X2 returns.
Zero paid API calls. No production writes or model changes.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests


EXPERIMENT_ID = "FAVORITE_LONGSHOT_BIAS_V1"
OUTPUT_DIR = Path("artifacts/favorite_longshot_bias_v1")
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

LEAGUES = {
    "EPL": "E0",
    "LA_LIGA": "SP1",
    "SERIE_A": "I1",
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}

STANDARD_COLUMNS = ("B365H", "B365D", "B365A")
CLOSING_COLUMNS = ("B365CH", "B365CD", "B365CA")
MAX_COLUMNS = ("MaxH", "MaxD", "MaxA")
SIDES = ("HOME", "DRAW", "AWAY")
RESULT_INDEX = {"H": 0, "D": 1, "A": 2}

BANDS = (
    ("P60_PLUS", 0.60, 1.0000000001),
    ("P50_60", 0.50, 0.60),
    ("P40_50", 0.40, 0.50),
    ("P30_40", 0.30, 0.40),
    ("P20_30", 0.20, 0.30),
    ("P10_20", 0.10, 0.20),
    ("P_LT10", 0.0, 0.10),
)

FAVORITE_MIN = 0.50
LONGSHOT_MAX = 0.20
MIN_SEASON_COVERAGE = 0.90
MIN_ELIGIBLE_LEAGUES = 4

BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"


def download_history() -> pd.DataFrame:
    frames: list[pd.DataFrame] = []

    for league, competition in LEAGUES.items():
        for season, code in SEASON_CODES.items():
            response = requests.get(
                BASE_URL.format(code=code, competition=competition),
                timeout=60,
            )
            response.raise_for_status()
            frame = pd.read_csv(io.BytesIO(response.content))
            if frame.empty:
                raise RuntimeError(f"{league} {season}: empty Football-Data file")
            frame = frame.copy()
            frame["league"] = league
            frame["season"] = season
            frame["_season_row"] = np.arange(len(frame), dtype=int)
            frames.append(frame)

    result = pd.concat(frames, ignore_index=True)
    if "FTR" not in result.columns:
        raise RuntimeError("Football-Data result column FTR is missing")
    return result


def numeric_triplet(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> pd.DataFrame:
    if not all(column in frame.columns for column in columns):
        return pd.DataFrame(
            np.nan,
            index=frame.index,
            columns=list(columns),
        )
    return frame[list(columns)].apply(pd.to_numeric, errors="coerce")


def valid_triplet_mask(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> pd.Series:
    odds = numeric_triplet(frame, columns)
    return odds.gt(1.0).all(axis=1)


def source_availability(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> dict:
    columns_present = all(column in frame.columns for column in columns)
    mask = valid_triplet_mask(frame, columns)
    by_league: dict[str, dict] = {}
    eligible_leagues: list[str] = []

    for league in LEAGUES:
        league_frame = frame[frame["league"].eq(league)]
        seasons = {}
        eligible = columns_present

        for season in SEASONS:
            season_mask = league_frame["season"].eq(season)
            total = int(season_mask.sum())
            valid = int(
                valid_triplet_mask(
                    league_frame.loc[season_mask],
                    columns,
                ).sum()
            )
            coverage = valid / total if total else 0.0
            seasons[season] = {
                "rows": total,
                "valid_rows": valid,
                "coverage": coverage,
            }
            if coverage < MIN_SEASON_COVERAGE:
                eligible = False

        by_league[league] = {
            "eligible": bool(eligible),
            "by_season": seasons,
            "valid_rows_total": int(
                (
                    frame["league"].eq(league)
                    & mask
                ).sum()
            ),
        }
        if eligible:
            eligible_leagues.append(league)

    return {
        "columns": list(columns),
        "columns_present": columns_present,
        "minimum_required_coverage": MIN_SEASON_COVERAGE,
        "eligible_leagues": eligible_leagues,
        "by_league": by_league,
    }


def normalized_inverse_probabilities(odds: np.ndarray) -> np.ndarray:
    values = np.asarray(odds, dtype=float)
    if values.shape != (3,):
        raise ValueError("1X2 odds must have exactly three outcomes")
    if not np.isfinite(values).all() or (values <= 1.0).any():
        raise ValueError("decimal odds must be finite and > 1")
    inverse = 1.0 / values
    total = float(inverse.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("invalid inverse-odds total")
    probabilities = inverse / total
    if not np.isclose(probabilities.sum(), 1.0, atol=1e-12):
        raise ValueError("probabilities do not sum to one")
    return probabilities


def probability_matrix(
    frame: pd.DataFrame,
    columns: tuple[str, str, str],
) -> np.ndarray:
    odds = numeric_triplet(frame, columns).to_numpy(dtype=float)
    probabilities = np.empty((len(frame), 3), dtype=float)
    for index, row in enumerate(odds):
        probabilities[index] = normalized_inverse_probabilities(row)
    return probabilities


def assign_band(probability: float) -> str:
    p = float(probability)
    for label, low, high in BANDS:
        if low <= p < high:
            return label
    raise ValueError(f"probability outside band contract: {p}")


def prepare_side_records(
    frame: pd.DataFrame,
    *,
    odds_columns: tuple[str, str, str],
    probability_columns: tuple[str, str, str] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return side-level records and fixture-level bootstrap contributions.

    If probability_columns is omitted, cohort probabilities come from odds_columns.
    This is used for STANDARD and CLOSING. For Max line-shopping diagnostics,
    probabilities remain frozen from STANDARD while returns use Max prices.
    """
    if probability_columns is None:
        probability_columns = odds_columns

    mask = (
        valid_triplet_mask(frame, odds_columns)
        & valid_triplet_mask(frame, probability_columns)
        & frame["FTR"].astype(str).isin(RESULT_INDEX)
    )
    local = frame.loc[mask].copy().reset_index(drop=True)

    odds = numeric_triplet(local, odds_columns).to_numpy(dtype=float)
    probabilities = probability_matrix(local, probability_columns)
    y = local["FTR"].astype(str).map(RESULT_INDEX).to_numpy(dtype=int)

    side_rows: list[dict] = []
    fixture_rows: list[dict] = []

    for row_index, row in local.iterrows():
        fav_sum = 0.0
        fav_count = 0
        long_sum = 0.0
        long_count = 0

        for side_index, side in enumerate(SIDES):
            probability = float(probabilities[row_index, side_index])
            side_odds = float(odds[row_index, side_index])
            won = int(y[row_index] == side_index)
            net_return = side_odds - 1.0 if won else -1.0
            favorite = probability >= FAVORITE_MIN
            longshot = probability <= LONGSHOT_MAX

            if favorite:
                fav_sum += net_return
                fav_count += 1
            if longshot:
                long_sum += net_return
                long_count += 1

            side_rows.append(
                {
                    "league": str(row["league"]),
                    "season": str(row["season"]),
                    "fixture_id": (
                        f"{row['league']}|{row['season']}|{int(row['_season_row'])}"
                    ),
                    "side": side,
                    "probability": probability,
                    "odds": side_odds,
                    "won": won,
                    "net_return": net_return,
                    "band": assign_band(probability),
                    "is_favorite": favorite,
                    "is_longshot": longshot,
                }
            )

        fixture_rows.append(
            {
                "league": str(row["league"]),
                "season": str(row["season"]),
                "fixture_id": (
                    f"{row['league']}|{row['season']}|{int(row['_season_row'])}"
                ),
                "favorite_return_sum": fav_sum,
                "favorite_count": fav_count,
                "longshot_return_sum": long_sum,
                "longshot_count": long_count,
            }
        )

    return pd.DataFrame(side_rows), pd.DataFrame(fixture_rows)


def side_metrics(rows: pd.DataFrame) -> dict:
    if rows.empty:
        return {
            "offers": 0,
            "wins": 0,
            "mean_probability": None,
            "observed_win_rate": None,
            "calibration_gap": None,
            "mean_odds": None,
            "roi": None,
        }

    observed = float(rows["won"].mean())
    mean_probability = float(rows["probability"].mean())
    return {
        "offers": int(len(rows)),
        "wins": int(rows["won"].sum()),
        "mean_probability": mean_probability,
        "observed_win_rate": observed,
        "calibration_gap": observed - mean_probability,
        "mean_odds": float(rows["odds"].mean()),
        "roi": float(rows["net_return"].mean()),
    }


def cohort_report(side_rows: pd.DataFrame) -> dict:
    favorite = side_rows[side_rows["is_favorite"]]
    longshot = side_rows[side_rows["is_longshot"]]
    favorite_metrics = side_metrics(favorite)
    longshot_metrics = side_metrics(longshot)

    if not favorite_metrics["offers"] or not longshot_metrics["offers"]:
        raise RuntimeError("favorite or longshot cohort is empty")

    return {
        "favorite": favorite_metrics,
        "longshot": longshot_metrics,
        "bias_delta_longshot_minus_favorite": (
            float(longshot_metrics["roi"] - favorite_metrics["roi"])
        ),
    }


def band_report(side_rows: pd.DataFrame) -> dict:
    return {
        label: side_metrics(side_rows[side_rows["band"].eq(label)])
        for label, _, _ in BANDS
    }


def temporal_report(side_rows: pd.DataFrame) -> dict:
    discovery = side_rows[side_rows["season"].isin(DISCOVERY_SEASONS)]
    validation = side_rows[side_rows["season"].eq(VALIDATION_SEASON)]
    test = side_rows[side_rows["season"].eq(TEST_SEASON)]

    return {
        "discovery": cohort_report(discovery),
        "validation": cohort_report(validation),
        "test": cohort_report(test),
        "overall": cohort_report(side_rows),
    }


def league_report(side_rows: pd.DataFrame, eligible_leagues: list[str]) -> dict:
    result = {}
    for league in eligible_leagues:
        local = side_rows[side_rows["league"].eq(league)]
        result[league] = cohort_report(local)
    return result


def bootstrap_bias_delta(fixtures: pd.DataFrame) -> dict:
    """Stratified match bootstrap, preserving all side records within a fixture.

    Sampling is vectorized by league-season stratum. The statistical contract is
    unchanged: each bootstrap draw resamples complete fixtures with replacement
    inside every stratum and aggregates their FAVORITE/LONGSHOT contributions.
    """
    required = {
        "league",
        "season",
        "favorite_return_sum",
        "favorite_count",
        "longshot_return_sum",
        "longshot_count",
    }
    if missing := required - set(fixtures.columns):
        raise ValueError("missing fixture columns: " + ", ".join(sorted(missing)))

    contribution_columns = [
        "favorite_return_sum",
        "favorite_count",
        "longshot_return_sum",
        "longshot_count",
    ]
    strata: list[np.ndarray] = []
    for _, group in fixtures.groupby(
        ["league", "season"],
        sort=True,
    ):
        values = group[contribution_columns].to_numpy(dtype=float)
        if len(values) == 0:
            raise RuntimeError("empty bootstrap stratum")
        strata.append(values)

    observed_totals = np.sum(
        np.vstack(strata),
        axis=0,
    )
    if observed_totals[1] <= 0 or observed_totals[3] <= 0:
        raise RuntimeError("bootstrap cohort count is zero")
    observed = (
        observed_totals[2] / observed_totals[3]
        - observed_totals[0] / observed_totals[1]
    )

    rng = np.random.default_rng(BOOTSTRAP_SEED)
    totals = np.zeros((BOOTSTRAP_SAMPLES, 4), dtype=float)

    for values in strata:
        n = len(values)
        indices = rng.integers(
            0,
            n,
            size=(BOOTSTRAP_SAMPLES, n),
        )
        totals += values[indices].sum(axis=1)

    if (totals[:, 1] <= 0).any() or (totals[:, 3] <= 0).any():
        raise RuntimeError("bootstrap draw produced empty cohort")

    draws = (
        totals[:, 2] / totals[:, 3]
        - totals[:, 0] / totals[:, 1]
    )

    return {
        "mean_bias_delta": float(observed),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "bootstrap_probability_negative": float((draws < 0.0).mean()),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def evaluate(frame: pd.DataFrame) -> dict:
    standard_availability = source_availability(frame, STANDARD_COLUMNS)
    eligible_leagues = standard_availability["eligible_leagues"]

    if len(eligible_leagues) < MIN_ELIGIBLE_LEAGUES:
        return {
            "standard_availability": standard_availability,
            "eligible_leagues": eligible_leagues,
            "standard": None,
            "closing_diagnostic": None,
            "max_line_shopping_diagnostic": None,
            "supported": False,
            "interpretation": "INSUFFICIENT_STANDARD_SOURCE_COVERAGE",
        }

    primary_frame = frame[frame["league"].isin(eligible_leagues)].copy()
    standard_sides, standard_fixtures = prepare_side_records(
        primary_frame,
        odds_columns=STANDARD_COLUMNS,
    )

    temporal = temporal_report(standard_sides)
    by_league = league_report(standard_sides, eligible_leagues)
    negative_leagues = int(
        sum(
            row["bias_delta_longshot_minus_favorite"] < 0.0
            for row in by_league.values()
        )
    )
    bootstrap = bootstrap_bias_delta(standard_fixtures)

    supported = bool(
        temporal["discovery"]["bias_delta_longshot_minus_favorite"] < 0.0
        and temporal["validation"]["bias_delta_longshot_minus_favorite"] < 0.0
        and temporal["test"]["bias_delta_longshot_minus_favorite"] < 0.0
        and negative_leagues >= 4
        and bootstrap["ci95_high"] < 0.0
    )

    closing_availability = source_availability(primary_frame, CLOSING_COLUMNS)
    closing_eligible = [
        league
        for league in eligible_leagues
        if league in closing_availability["eligible_leagues"]
    ]
    if closing_eligible:
        closing_frame = primary_frame[
            primary_frame["league"].isin(closing_eligible)
        ].copy()
        closing_sides, _ = prepare_side_records(
            closing_frame,
            odds_columns=CLOSING_COLUMNS,
        )
        closing_diagnostic = {
            "eligible_leagues": closing_eligible,
            "overall": cohort_report(closing_sides),
            "by_league": league_report(closing_sides, closing_eligible),
            "bands": band_report(closing_sides),
        }
    else:
        closing_diagnostic = {
            "eligible_leagues": [],
            "status": "CLOSING_SOURCE_UNAVAILABLE",
        }

    max_availability = source_availability(primary_frame, MAX_COLUMNS)
    max_eligible = [
        league
        for league in eligible_leagues
        if league in max_availability["eligible_leagues"]
    ]
    if max_eligible:
        max_frame = primary_frame[
            primary_frame["league"].isin(max_eligible)
        ].copy()
        max_sides, _ = prepare_side_records(
            max_frame,
            odds_columns=MAX_COLUMNS,
            probability_columns=STANDARD_COLUMNS,
        )
        max_diagnostic = {
            "eligible_leagues": max_eligible,
            "overall": cohort_report(max_sides),
            "by_league": league_report(max_sides, max_eligible),
            "bands": band_report(max_sides),
        }
    else:
        max_diagnostic = {
            "eligible_leagues": [],
            "status": "MAX_SOURCE_UNAVAILABLE",
        }

    return {
        "standard_availability": standard_availability,
        "eligible_leagues": eligible_leagues,
        "standard": {
            "side_offers": int(len(standard_sides)),
            "fixtures": int(len(standard_fixtures)),
            "temporal": temporal,
            "by_league": by_league,
            "negative_bias_leagues": negative_leagues,
            "bands": band_report(standard_sides),
            "bootstrap": bootstrap,
        },
        "closing_availability": closing_availability,
        "closing_diagnostic": closing_diagnostic,
        "max_availability": max_availability,
        "max_line_shopping_diagnostic": max_diagnostic,
        "supported": supported,
        "interpretation": (
            "FAVORITE_LONGSHOT_BIAS_SUPPORTED"
            if supported
            else "NO_ROBUST_FAVORITE_LONGSHOT_BIAS"
        ),
    }


def main() -> int:
    frame = download_history()
    result = evaluate(frame)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_CROSS_LEAGUE_TEMPORAL_HOLDOUT",
        "research_only": True,
        "production_promotion": False,
        "paid_odds_api_calls": False,
        "supabase_reads": False,
        "supabase_writes": False,
        "candidate_artifact_saved": False,
        "source": "Football-Data CSV / Bet365 1X2",
        "source_rows": int(len(frame)),
        "leagues": list(LEAGUES),
        "season_codes": SEASON_CODES,
        "discovery_seasons": DISCOVERY_SEASONS,
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "standard_columns": list(STANDARD_COLUMNS),
        "closing_columns": list(CLOSING_COLUMNS),
        "max_columns": list(MAX_COLUMNS),
        "favorite_probability_min": FAVORITE_MIN,
        "longshot_probability_max": LONGSHOT_MAX,
        "minimum_season_coverage": MIN_SEASON_COVERAGE,
        "minimum_eligible_leagues": MIN_ELIGIBLE_LEAGUES,
        "bootstrap_samples": BOOTSTRAP_SAMPLES,
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
