"""MARKET_MAX_AVG_SPREAD_REPLICATION_V2.

External cross-league replication of the post-hoc inverse EPL Max-vs-Avg spread
observation. EPL is excluded from all V2 support statistics.

Research only. Zero paid API calls. No production writes.
"""
from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from market_devig_methods_v1 import multiplicative_probabilities


EXPERIMENT_ID = "MARKET_MAX_AVG_SPREAD_REPLICATION_V2"
OUTPUT_DIR = Path("artifacts/market_max_avg_spread_replication_v2")
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

LEAGUES = {
    "LA_LIGA": "SP1",
    "SERIE_A": "I1",
    "BUNDESLIGA": "D1",
    "LIGUE_1": "F1",
}

AVG_COLUMNS = ("AvgH", "AvgD", "AvgA")
MAX_COLUMNS = ("MaxH", "MaxD", "MaxA")

# Exact EPL V1 discovery thresholds, transferred without re-estimation.
LOW_SPREAD_THRESHOLD = 0.04177782395388535
HIGH_SPREAD_THRESHOLD = 0.06264317681762262

MIN_SEASON_COVERAGE = 0.90
MIN_ELIGIBLE_LEAGUES = 3
MIN_GROUP_ROWS_PER_CELL = 5
MIN_MATCHED_CELLS = 20
CELL_NEGATIVE_FRACTION_GATE = 0.60

BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20260929
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"


def download_history() -> dict[str, pd.DataFrame]:
    histories: dict[str, pd.DataFrame] = {}

    for league, competition in LEAGUES.items():
        frames = []
        for season, code in SEASON_CODES.items():
            response = requests.get(
                BASE_URL.format(
                    code=code,
                    competition=competition,
                ),
                timeout=60,
            )
            response.raise_for_status()
            frame = pd.read_csv(io.BytesIO(response.content))
            if frame.empty:
                raise RuntimeError(
                    f"{league} {season}: empty Football-Data file"
                )
            frame = frame.copy()
            frame["league"] = league
            frame["season"] = season
            frame["_season_row"] = np.arange(len(frame), dtype=int)
            frames.append(frame)

        histories[league] = pd.concat(
            frames,
            ignore_index=True,
        )

    return histories


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
    return frame[list(columns)].apply(
        pd.to_numeric,
        errors="coerce",
    )


def valid_spread_mask(frame: pd.DataFrame) -> pd.Series:
    avg = numeric_triplet(frame, AVG_COLUMNS)
    maximum = numeric_triplet(frame, MAX_COLUMNS)

    valid = (
        avg.gt(1.0).all(axis=1)
        & maximum.gt(1.0).all(axis=1)
    )

    avg_values = avg.to_numpy(dtype=float)
    max_values = maximum.to_numpy(dtype=float)
    coherent = pd.Series(
        np.all(
            max_values >= avg_values,
            axis=1,
        ),
        index=frame.index,
        dtype=bool,
    )

    result_valid = frame["FTR"].astype(str).isin(["H", "D", "A"])
    return valid & coherent & result_valid


def league_availability(frame: pd.DataFrame) -> dict:
    mask = valid_spread_mask(frame)
    by_season = {}
    eligible = True

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
        "avg_columns_present": all(
            column in frame.columns
            for column in AVG_COLUMNS
        ),
        "max_columns_present": all(
            column in frame.columns
            for column in MAX_COLUMNS
        ),
        "minimum_required_coverage": MIN_SEASON_COVERAGE,
        "valid_rows_total": int(mask.sum()),
        "by_season": by_season,
        "eligible": bool(eligible),
    }


def probability_matrix(frame: pd.DataFrame) -> np.ndarray:
    odds = numeric_triplet(
        frame,
        AVG_COLUMNS,
    ).to_numpy(dtype=float)

    probabilities = np.empty(
        (len(frame), 3),
        dtype=float,
    )

    for index, row in enumerate(odds):
        probabilities[index], _ = (
            multiplicative_probabilities(row)
        )

    return probabilities


def actual_indices(frame: pd.DataFrame) -> np.ndarray:
    return (
        frame["FTR"]
        .astype(str)
        .map({"H": 0, "D": 1, "A": 2})
        .to_numpy(dtype=int)
    )


def prepare_league(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    mask = valid_spread_mask(frame)
    data = frame.loc[mask].copy().reset_index(drop=True)

    avg = numeric_triplet(
        data,
        AVG_COLUMNS,
    ).to_numpy(dtype=float)
    maximum = numeric_triplet(
        data,
        MAX_COLUMNS,
    ).to_numpy(dtype=float)

    gaps = maximum / avg - 1.0
    if (gaps < -1e-12).any():
        raise RuntimeError(
            "Max-vs-Avg gap became negative"
        )

    data["market_spread"] = np.sqrt(
        np.mean(gaps**2, axis=1)
    )

    probabilities = probability_matrix(data)
    y = actual_indices(data)
    onehot = np.eye(3)[y]

    realized_brier = np.sum(
        (probabilities - onehot) ** 2,
        axis=1,
    )
    expected_brier = (
        1.0
        - np.sum(
            probabilities**2,
            axis=1,
        )
    )

    data["market_brier"] = realized_brier
    data["expected_brier"] = expected_brier
    data["excess_brier"] = (
        realized_brier
        - expected_brier
    )
    data["favorite_probability"] = (
        probabilities.max(axis=1)
    )

    labels = pd.Series(
        pd.NA,
        index=data.index,
        dtype="string",
    )
    labels.loc[
        data["market_spread"]
        <= LOW_SPREAD_THRESHOLD
    ] = "LOW"
    labels.loc[
        data["market_spread"]
        >= HIGH_SPREAD_THRESHOLD
    ] = "HIGH"
    data["spread_group"] = labels

    return data


def matched_cells(
    combined: pd.DataFrame,
) -> tuple[pd.DataFrame, list[dict]]:
    cells: list[dict] = []
    selected_indices: list[np.ndarray] = []

    for (league, season), group in combined.groupby(
        ["league", "season"],
        sort=True,
    ):
        high = group[
            group["spread_group"].eq("HIGH")
        ]
        low = group[
            group["spread_group"].eq("LOW")
        ]

        eligible = bool(
            len(high) >= MIN_GROUP_ROWS_PER_CELL
            and len(low) >= MIN_GROUP_ROWS_PER_CELL
        )

        cells.append(
            {
                "league": str(league),
                "season": str(season),
                "high_rows": int(len(high)),
                "low_rows": int(len(low)),
                "eligible": eligible,
            }
        )

        if eligible:
            selected_indices.append(
                np.concatenate(
                    [
                        high.index.to_numpy(),
                        low.index.to_numpy(),
                    ]
                )
            )

    if not selected_indices:
        return combined.iloc[0:0].copy(), cells

    indices = np.concatenate(selected_indices)
    matched = combined.loc[
        np.unique(indices)
    ].copy()

    return matched, cells


def group_effect(
    frame: pd.DataFrame,
    value_column: str,
) -> float:
    high = frame.loc[
        frame["spread_group"].eq("HIGH"),
        value_column,
    ]
    low = frame.loc[
        frame["spread_group"].eq("LOW"),
        value_column,
    ]
    if len(high) == 0 or len(low) == 0:
        raise RuntimeError(
            "HIGH/LOW comparison has empty group"
        )
    return float(
        high.mean()
        - low.mean()
    )


def effect_breakdown(
    matched: pd.DataFrame,
    value_column: str,
) -> dict:
    by_league = {}
    negative_leagues = 0

    for league in sorted(
        matched["league"].unique()
    ):
        local = matched[
            matched["league"].eq(league)
        ]
        delta = group_effect(
            local,
            value_column,
        )
        negative_leagues += int(delta < 0.0)
        by_league[str(league)] = {
            "matches": int(len(local)),
            "high_rows": int(
                local["spread_group"].eq("HIGH").sum()
            ),
            "low_rows": int(
                local["spread_group"].eq("LOW").sum()
            ),
            "high_mean": float(
                local.loc[
                    local["spread_group"].eq("HIGH"),
                    value_column,
                ].mean()
            ),
            "low_mean": float(
                local.loc[
                    local["spread_group"].eq("LOW"),
                    value_column,
                ].mean()
            ),
            "high_minus_low": delta,
        }

    by_cell = {}
    negative_cells = 0

    for (league, season), local in matched.groupby(
        ["league", "season"],
        sort=True,
    ):
        delta = group_effect(
            local,
            value_column,
        )
        negative_cells += int(delta < 0.0)
        key = f"{league}|{season}"
        by_cell[key] = {
            "high_rows": int(
                local["spread_group"].eq("HIGH").sum()
            ),
            "low_rows": int(
                local["spread_group"].eq("LOW").sum()
            ),
            "high_minus_low": delta,
        }

    total_cells = len(by_cell)

    return {
        "pooled_high_minus_low": group_effect(
            matched,
            value_column,
        ),
        "negative_leagues": int(
            negative_leagues
        ),
        "league_count": int(
            len(by_league)
        ),
        "negative_cells": int(
            negative_cells
        ),
        "matched_cell_count": int(
            total_cells
        ),
        "negative_cell_fraction": (
            negative_cells / total_cells
            if total_cells
            else None
        ),
        "by_league": by_league,
        "by_cell": by_cell,
    }


def stratified_group_bootstrap(
    matched: pd.DataFrame,
    value_column: str,
) -> dict:
    cells = {}

    for (league, season), local in matched.groupby(
        ["league", "season"],
        sort=True,
    ):
        high = local.loc[
            local["spread_group"].eq("HIGH"),
            value_column,
        ].to_numpy(dtype=float)
        low = local.loc[
            local["spread_group"].eq("LOW"),
            value_column,
        ].to_numpy(dtype=float)

        if (
            len(high) < MIN_GROUP_ROWS_PER_CELL
            or len(low) < MIN_GROUP_ROWS_PER_CELL
        ):
            raise RuntimeError(
                f"{league} {season}: invalid matched cell"
            )

        cells[
            (str(league), str(season))
        ] = (high, low)

    total_high = sum(
        len(pair[0])
        for pair in cells.values()
    )
    total_low = sum(
        len(pair[1])
        for pair in cells.values()
    )

    observed = group_effect(
        matched,
        value_column,
    )

    rng = np.random.default_rng(
        BOOTSTRAP_SEED
    )
    draws = np.empty(
        BOOTSTRAP_SAMPLES,
        dtype=float,
    )

    for draw in range(
        BOOTSTRAP_SAMPLES
    ):
        high_sum = 0.0
        low_sum = 0.0

        for high, low in cells.values():
            high_sum += float(
                rng.choice(
                    high,
                    size=len(high),
                    replace=True,
                ).sum()
            )
            low_sum += float(
                rng.choice(
                    low,
                    size=len(low),
                    replace=True,
                ).sum()
            )

        draws[draw] = (
            high_sum / total_high
            - low_sum / total_low
        )

    return {
        "mean_high_minus_low": observed,
        "ci95_low": float(
            np.quantile(
                draws,
                0.025,
            )
        ),
        "ci95_high": float(
            np.quantile(
                draws,
                0.975,
            )
        ),
        "bootstrap_probability_negative":
            float(
                (
                    draws
                    < 0.0
                ).mean()
            ),
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
    }


def support_decision(
    breakdown: dict,
    bootstrap: dict,
) -> bool:
    return bool(
        breakdown["pooled_high_minus_low"] < 0.0
        and bootstrap["ci95_high"] < 0.0
        and breakdown["negative_leagues"]
            >= MIN_ELIGIBLE_LEAGUES
        and breakdown["negative_cell_fraction"]
            >= CELL_NEGATIVE_FRACTION_GATE
    )


def evaluate(
    histories: dict[str, pd.DataFrame],
) -> dict:
    source_availability = {
        league: league_availability(frame)
        for league, frame in histories.items()
    }

    eligible_leagues = [
        league
        for league in LEAGUES
        if source_availability[league]["eligible"]
    ]

    if len(eligible_leagues) < MIN_ELIGIBLE_LEAGUES:
        return {
            "source_availability": source_availability,
            "eligible_leagues": eligible_leagues,
            "matched_cell_count": 0,
            "raw_brier": None,
            "excess_brier": None,
            "favorite_probability_diagnostic": None,
            "signals_supported": [],
            "interpretation":
                "INSUFFICIENT_REPLICATION_COVERAGE",
        }

    prepared = []

    for league in eligible_leagues:
        data = prepare_league(
            histories[league]
        )
        prepared.append(data)

    combined = pd.concat(
        prepared,
        ignore_index=True,
    )

    matched, cell_coverage = (
        matched_cells(combined)
    )

    matched_cell_count = int(
        sum(
            row["eligible"]
            for row in cell_coverage
        )
    )

    if matched_cell_count < MIN_MATCHED_CELLS:
        return {
            "source_availability": source_availability,
            "eligible_leagues": eligible_leagues,
            "prepared_rows": int(len(combined)),
            "cell_coverage": cell_coverage,
            "matched_cell_count": matched_cell_count,
            "raw_brier": None,
            "excess_brier": None,
            "favorite_probability_diagnostic": None,
            "signals_supported": [],
            "interpretation":
                "INSUFFICIENT_MATCHED_CELL_COVERAGE",
        }

    raw_breakdown = effect_breakdown(
        matched,
        "market_brier",
    )
    raw_bootstrap = stratified_group_bootstrap(
        matched,
        "market_brier",
    )
    raw_supported = support_decision(
        raw_breakdown,
        raw_bootstrap,
    )

    excess_breakdown = effect_breakdown(
        matched,
        "excess_brier",
    )
    excess_bootstrap = stratified_group_bootstrap(
        matched,
        "excess_brier",
    )
    excess_supported = support_decision(
        excess_breakdown,
        excess_bootstrap,
    )

    favorite_breakdown = effect_breakdown(
        matched,
        "favorite_probability",
    )

    signals = []

    if raw_supported:
        signals.append(
            "RAW_INVERSE_SPREAD_REPLICATION"
        )

    if excess_supported:
        signals.append(
            "CONFIDENCE_ADJUSTED_SPREAD_REPLICATION"
        )

    if excess_supported:
        interpretation = (
            "CONFIDENCE_ADJUSTED_SPREAD_REPLICATED"
        )
    elif raw_supported:
        interpretation = (
            "RAW_ONLY_SPREAD_REPLICATION"
        )
    else:
        interpretation = (
            "NO_CROSS_LEAGUE_SPREAD_REPLICATION"
        )

    return {
        "source_availability":
            source_availability,

        "eligible_leagues":
            eligible_leagues,

        "prepared_rows":
            int(len(combined)),

        "transferred_thresholds": {
            "low_max": LOW_SPREAD_THRESHOLD,
            "high_min":
                HIGH_SPREAD_THRESHOLD,
        },

        "cell_coverage":
            cell_coverage,

        "matched_cell_count":
            matched_cell_count,

        "matched_rows":
            int(len(matched)),

        "raw_brier": {
            "breakdown": raw_breakdown,
            "bootstrap": raw_bootstrap,
            "supported": raw_supported,
        },

        "excess_brier": {
            "formula":
                "realized_brier - (1 - sum(p_i^2))",
            "breakdown": excess_breakdown,
            "bootstrap": excess_bootstrap,
            "supported": excess_supported,
        },

        "favorite_probability_diagnostic": {
            "breakdown":
                favorite_breakdown,
        },

        "signals_supported":
            signals,

        "interpretation":
            interpretation,
    }


def main() -> int:
    histories = download_history()
    result = evaluate(histories)

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class":
            "EXTERNAL_CROSS_LEAGUE_REPLICATION",
        "research_only": True,
        "production_promotion": False,
        "epl_outcomes_used_in_support_statistics":
            False,
        "paid_odds_api_calls": False,
        "supabase_reads": False,
        "supabase_writes": False,
        "candidate_artifact_saved": False,
        "source":
            "Football-Data CSV",
        "leagues":
            list(LEAGUES),
        "season_codes":
            SEASON_CODES,
        "avg_columns":
            list(AVG_COLUMNS),
        "max_columns":
            list(MAX_COLUMNS),
        "low_spread_threshold":
            LOW_SPREAD_THRESHOLD,
        "high_spread_threshold":
            HIGH_SPREAD_THRESHOLD,
        "minimum_season_coverage":
            MIN_SEASON_COVERAGE,
        "minimum_group_rows_per_cell":
            MIN_GROUP_ROWS_PER_CELL,
        "minimum_matched_cells":
            MIN_MATCHED_CELLS,
        "result":
            result,
        "package_versions": {
            "pandas":
                pd.__version__,
            "numpy":
                np.__version__,
            "requests":
                requests.__version__,
        },
    }

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT_PATH.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        )
    )

    print(
        "Research only; zero paid API calls; "
        "EPL excluded; production unchanged."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
