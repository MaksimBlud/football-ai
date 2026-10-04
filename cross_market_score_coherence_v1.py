"""CROSS_MARKET_SCORE_COHERENCE_V1.

Preregistered historical temporal-OOT diagnostic of same-bookmaker structural
coherence between Bet365 1X2, O/U 2.5 and Asian Handicap markets.

Research-only / NO_BET / no production promotion / no 2026-27 outcomes.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import scipy
from scipy.optimize import brentq, minimize_scalar
from scipy.stats import poisson, skellam, spearmanr
from sklearn.metrics import log_loss

from historical_football_signal_runner import BASE, LEAGUES


EXPERIMENT_ID = "CROSS_MARKET_SCORE_COHERENCE_V1"
LEAGUE_IDS = ("EPL", "LA_LIGA", "SERIE_A")
TRAIN_SEASONS = tuple(f"{year}-{year + 1}" for year in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
ALLOWED_SEASONS = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}

ONE_X_TWO_COLUMNS = ("B365H", "B365D", "B365A")
TOTAL_COLUMNS = ("B365>2.5", "B365<2.5")
AH_COLUMNS = ("B365AHH", "B365AHA")
AH_LINE_COLUMNS = ("AHh", "B365AH")

MU_BOUNDS = (0.05, 8.0)
HOME_SHARE_BOUNDS = (0.02, 0.98)
MIN_TAIL_ROWS_PER_LEAGUE = 15
BOOTSTRAP_SAMPLES = 10000
BOOTSTRAP_SEED = 20261002
EPS = 1e-12

RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}


def _three_way_devig(odds: np.ndarray) -> np.ndarray:
    values = np.asarray(odds, dtype=float)
    if values.shape != (3,):
        raise ValueError("1X2 odds must contain exactly three prices")
    if not np.isfinite(values).all() or (values <= 1.0).any():
        raise ValueError("1X2 decimal odds must be finite and > 1")
    inverse = 1.0 / values
    total = float(inverse.sum())
    if not np.isfinite(total) or total <= 0.0:
        raise ValueError("invalid inverse-odds total")
    probabilities = inverse / total
    if not np.isclose(probabilities.sum(), 1.0, atol=1e-12):
        raise ValueError("1X2 probabilities do not sum to one")
    return probabilities


def _binary_devig(first_odds: float, second_odds: float) -> float:
    first = float(first_odds)
    second = float(second_odds)
    if (
        not np.isfinite(first)
        or not np.isfinite(second)
        or first <= 1.0
        or second <= 1.0
    ):
        raise ValueError("two-way decimal odds must be finite and > 1")
    first_inv = 1.0 / first
    second_inv = 1.0 / second
    return float(first_inv / (first_inv + second_inv))


def _is_half_goal_line(line: float) -> bool:
    value = float(line)
    if not np.isfinite(value):
        return False
    twice = value * 2.0
    if not np.isclose(twice, round(twice), atol=1e-9):
        return False
    return not np.isclose(value, round(value), atol=1e-9)


def _first_line(row: pd.Series) -> tuple[float, str] | None:
    for column in AH_LINE_COLUMNS:
        value = pd.to_numeric(row.get(column), errors="coerce")
        if np.isfinite(value):
            return float(value), column
    return None


def _over25_probability(mu: float) -> float:
    return float(1.0 - poisson.cdf(2, float(mu)))


def _infer_total_lambda(p_over25: float) -> float:
    target = float(p_over25)
    if not 0.0 < target < 1.0:
        raise ValueError("O/U probability must lie strictly inside (0,1)")
    lo, hi = MU_BOUNDS
    p_lo = _over25_probability(lo)
    p_hi = _over25_probability(hi)
    if target < p_lo - 1e-12 or target > p_hi + 1e-12:
        raise ValueError("O/U probability outside frozen Poisson lambda bracket")
    return float(
        brentq(
            lambda mu: _over25_probability(mu) - target,
            lo,
            hi,
            xtol=1e-12,
            rtol=1e-12,
            maxiter=200,
        )
    )


def _minimum_cover_difference(line: float) -> int:
    if not _is_half_goal_line(line):
        raise ValueError("primary coherence reconstruction requires half-goal AH")
    # D + line > 0, with integer D = home goals - away goals.
    return int(math.floor(-float(line)) + 1)


def _ah_home_cover_probability(
    mu: float,
    home_share: float,
    line: float,
) -> float:
    share = float(home_share)
    if not HOME_SHARE_BOUNDS[0] <= share <= HOME_SHARE_BOUNDS[1]:
        raise ValueError("home share outside frozen bounds")
    lambda_home = float(mu) * share
    lambda_away = float(mu) * (1.0 - share)
    minimum_difference = _minimum_cover_difference(line)
    return float(
        skellam.sf(
            minimum_difference - 1,
            lambda_home,
            lambda_away,
        )
    )


def _infer_home_share(
    mu: float,
    line: float,
    p_ah_home: float,
) -> tuple[float, float, str]:
    target = float(p_ah_home)
    if not 0.0 < target < 1.0:
        raise ValueError("AH probability must lie strictly inside (0,1)")

    lo, hi = HOME_SHARE_BOUNDS

    def residual(share: float) -> float:
        return _ah_home_cover_probability(mu, share, line) - target

    f_lo = residual(lo)
    f_hi = residual(hi)
    if not np.isfinite(f_lo) or not np.isfinite(f_hi):
        raise ValueError("non-finite AH reconstruction endpoint")

    if f_lo == 0.0:
        share = lo
        method = "BOUNDARY_ROOT"
    elif f_hi == 0.0:
        share = hi
        method = "BOUNDARY_ROOT"
    elif f_lo * f_hi < 0.0:
        share = float(
            brentq(
                residual,
                lo,
                hi,
                xtol=1e-12,
                rtol=1e-12,
                maxiter=200,
            )
        )
        method = "BRENT_ROOT"
    else:
        optimized = minimize_scalar(
            lambda share_value: residual(float(share_value)) ** 2,
            bounds=(lo, hi),
            method="bounded",
            options={"xatol": 1e-12, "maxiter": 500},
        )
        if not optimized.success or not np.isfinite(optimized.x):
            raise ValueError("AH bounded reconstruction failed")
        share = float(optimized.x)
        method = "BOUNDED_MINIMUM"

    fitted = _ah_home_cover_probability(mu, share, line)
    return share, abs(float(fitted - target)), method


def _synthetic_1x2(lambda_home: float, lambda_away: float) -> np.ndarray:
    home = float(skellam.sf(0, lambda_home, lambda_away))
    draw = float(skellam.pmf(0, lambda_home, lambda_away))
    away = float(skellam.cdf(-1, lambda_home, lambda_away))
    probabilities = np.asarray([home, draw, away], dtype=float)
    if not np.isfinite(probabilities).all() or (probabilities < 0.0).any():
        raise ValueError("invalid synthetic 1X2 probabilities")
    total = float(probabilities.sum())
    if total <= 0.0:
        raise ValueError("synthetic 1X2 probabilities have zero mass")
    probabilities /= total
    return probabilities


def _reconstruct(
    p_over25: float,
    ah_line: float,
    p_ah_home: float,
) -> dict[str, object]:
    mu = _infer_total_lambda(p_over25)
    share, ah_error, method = _infer_home_share(
        mu,
        ah_line,
        p_ah_home,
    )
    lambda_home = mu * share
    lambda_away = mu * (1.0 - share)
    p_score = _synthetic_1x2(lambda_home, lambda_away)
    return {
        "lambda_total": float(mu),
        "lambda_home": float(lambda_home),
        "lambda_away": float(lambda_away),
        "home_share": float(share),
        "ah_fit_abs_error": float(ah_error),
        "ah_fit_method": method,
        "score_home_prob": float(p_score[0]),
        "score_draw_prob": float(p_score[1]),
        "score_away_prob": float(p_score[2]),
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
        raw["Date"],
        dayfirst=True,
        errors="coerce",
    )
    return raw.sort_values(
        ["match_date", "HomeTeam", "AwayTeam"],
        kind="stable",
    ).reset_index(drop=True)


def _valid_prices(row: pd.Series, columns: tuple[str, ...]) -> np.ndarray | None:
    values = np.asarray(
        [pd.to_numeric(row.get(column), errors="coerce") for column in columns],
        dtype=float,
    )
    if not np.isfinite(values).all() or (values <= 1.0).any():
        return None
    return values


def _build_league_rows(
    raw: pd.DataFrame,
    league: str,
) -> tuple[pd.DataFrame, dict[str, object]]:
    rows: list[dict[str, object]] = []
    coverage_by_season: dict[str, dict[str, int]] = {}

    for season in sorted(ALLOWED_SEASONS):
        season_frame = raw[raw["season"].astype(str) == season]
        coverage_by_season[season] = {
            "source_rows": int(len(season_frame)),
            "complete_same_book_market_rows": 0,
            "half_goal_ah_rows": 0,
            "reconstructed_rows": 0,
        }

    reconstruction_failures = Counter()
    line_distribution = Counter()
    method_distribution = Counter()

    for _, row in raw.iterrows():
        season = str(row.get("season"))
        if season not in coverage_by_season:
            continue

        one_x_two = _valid_prices(row, ONE_X_TWO_COLUMNS)
        total = _valid_prices(row, TOTAL_COLUMNS)
        ah = _valid_prices(row, AH_COLUMNS)
        line_info = _first_line(row)

        if (
            one_x_two is None
            or total is None
            or ah is None
            or line_info is None
        ):
            continue

        coverage_by_season[season]["complete_same_book_market_rows"] += 1

        ah_line, line_source = line_info
        if not _is_half_goal_line(ah_line):
            continue
        coverage_by_season[season]["half_goal_ah_rows"] += 1

        result = str(row.get("FTR") or "").upper()
        if result not in RESULT_TO_INT:
            continue

        try:
            p_market = _three_way_devig(one_x_two)
            p_over25 = _binary_devig(total[0], total[1])
            p_ah_home = _binary_devig(ah[0], ah[1])
            reconstructed = _reconstruct(
                p_over25,
                ah_line,
                p_ah_home,
            )
        except (ValueError, RuntimeError) as exc:
            reconstruction_failures[type(exc).__name__ + ":" + str(exc)] += 1
            continue

        p_score = np.asarray(
            [
                reconstructed["score_home_prob"],
                reconstructed["score_draw_prob"],
                reconstructed["score_away_prob"],
            ],
            dtype=float,
        )
        score_gap_tv = float(
            0.5 * np.abs(p_market - p_score).sum()
        )

        rows.append(
            {
                "league": league,
                "season": season,
                "match_date": row.get("match_date"),
                "home_team": str(row.get("HomeTeam")),
                "away_team": str(row.get("AwayTeam")),
                "actual_result": result,
                "actual_index": RESULT_TO_INT[result],
                "market_home_prob": float(p_market[0]),
                "market_draw_prob": float(p_market[1]),
                "market_away_prob": float(p_market[2]),
                "over25_prob": float(p_over25),
                "ah_home_prob": float(p_ah_home),
                "ah_line": float(ah_line),
                "ah_line_source": line_source,
                "score_gap_tv": score_gap_tv,
                **reconstructed,
            }
        )
        coverage_by_season[season]["reconstructed_rows"] += 1
        line_distribution[f"{ah_line:+.1f}"] += 1
        method_distribution[str(reconstructed["ah_fit_method"])] += 1

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"{league}: no cross-market coherence rows")

    coverage = {
        "source_rows": int(len(raw)),
        "coherence_rows": int(len(frame)),
        "by_season": coverage_by_season,
        "ah_line_distribution": dict(sorted(line_distribution.items())),
        "ah_fit_method_distribution": dict(sorted(method_distribution.items())),
        "reconstruction_failures": dict(reconstruction_failures),
    }
    return frame, coverage


def _multiclass_scores(
    y: np.ndarray,
    probabilities: np.ndarray,
) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = np.asarray(probabilities, dtype=float)
    if len(y) != len(p):
        raise ValueError("score length mismatch")
    onehot = np.eye(3)[y]
    clipped = np.clip(p, 1e-15, 1.0)
    return {
        "brier": float(
            np.mean(np.sum((p - onehot) ** 2, axis=1))
        ),
        "log_loss": float(
            log_loss(y, clipped, labels=[0, 1, 2])
        ),
        "accuracy": float(
            (p.argmax(axis=1) == y).mean()
        ),
    }


def _attach_outcome_errors(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    p_market = out[
        ["market_home_prob", "market_draw_prob", "market_away_prob"]
    ].to_numpy(dtype=float)
    y = out["actual_index"].to_numpy(dtype=int)
    onehot = np.eye(3)[y]
    out["market_brier"] = np.sum(
        (p_market - onehot) ** 2,
        axis=1,
    )
    out["expected_market_brier"] = (
        1.0 - np.sum(p_market**2, axis=1)
    )
    out["excess_brier"] = (
        out["market_brier"] - out["expected_market_brier"]
    )
    return out


def _training_thresholds(
    frame: pd.DataFrame,
) -> dict[str, dict[str, float | int]]:
    thresholds: dict[str, dict[str, float | int]] = {}
    for league in LEAGUE_IDS:
        train = frame[
            (frame["league"] == league)
            & frame["season"].isin(TRAIN_SEASONS)
        ]
        if len(train) < 60:
            raise RuntimeError(
                f"{league}: insufficient train coherence rows ({len(train)})"
            )
        low = float(train["score_gap_tv"].quantile(0.25))
        high = float(train["score_gap_tv"].quantile(0.75))
        if not np.isfinite(low) or not np.isfinite(high) or not low < high:
            raise RuntimeError(
                f"{league}: invalid feature-only coherence thresholds"
            )
        thresholds[league] = {
            "train_rows": int(len(train)),
            "low_q25": low,
            "high_q75": high,
        }
    return thresholds


def _assign_tail(
    frame: pd.DataFrame,
    thresholds: dict[str, dict[str, float | int]],
) -> pd.DataFrame:
    out = frame.copy()
    labels = []
    for row in out.itertuples(index=False):
        threshold = thresholds[str(row.league)]
        gap = float(row.score_gap_tv)
        if gap <= float(threshold["low_q25"]):
            labels.append("LOW")
        elif gap >= float(threshold["high_q75"]):
            labels.append("HIGH")
        else:
            labels.append("MID")
    out["coherence_tail"] = labels
    return out


def _safe_corr(
    x: pd.Series,
    y: pd.Series,
) -> dict[str, float | None]:
    if len(x) < 3:
        return {"pearson": None, "spearman": None}
    pearson = float(x.astype(float).corr(y.astype(float), method="pearson"))
    spearman = float(spearmanr(x.astype(float), y.astype(float)).statistic)
    return {
        "pearson": pearson if np.isfinite(pearson) else None,
        "spearman": spearman if np.isfinite(spearman) else None,
    }


def _split_report(
    frame: pd.DataFrame,
    season: str,
) -> dict[str, object]:
    split = frame[frame["season"] == season].copy()
    if split.empty:
        raise RuntimeError(f"{season}: empty coherence split")

    by_league: dict[str, dict[str, object]] = {}
    positive_leagues = 0
    all_high = []
    all_low = []

    for league in LEAGUE_IDS:
        local = split[split["league"] == league]
        high = local[local["coherence_tail"] == "HIGH"]
        low = local[local["coherence_tail"] == "LOW"]

        excess_delta = (
            float(high["excess_brier"].mean() - low["excess_brier"].mean())
            if len(high) and len(low)
            else None
        )
        raw_delta = (
            float(high["market_brier"].mean() - low["market_brier"].mean())
            if len(high) and len(low)
            else None
        )
        positive_leagues += int(
            excess_delta is not None and excess_delta > 0.0
        )
        all_high.append(high)
        all_low.append(low)

        by_league[league] = {
            "rows": int(len(local)),
            "high_rows": int(len(high)),
            "mid_rows": int((local["coherence_tail"] == "MID").sum()),
            "low_rows": int(len(low)),
            "high_mean_gap_tv": (
                float(high["score_gap_tv"].mean()) if len(high) else None
            ),
            "low_mean_gap_tv": (
                float(low["score_gap_tv"].mean()) if len(low) else None
            ),
            "high_mean_excess_brier": (
                float(high["excess_brier"].mean()) if len(high) else None
            ),
            "low_mean_excess_brier": (
                float(low["excess_brier"].mean()) if len(low) else None
            ),
            "excess_brier_high_minus_low": excess_delta,
            "high_mean_raw_brier": (
                float(high["market_brier"].mean()) if len(high) else None
            ),
            "low_mean_raw_brier": (
                float(low["market_brier"].mean()) if len(low) else None
            ),
            "raw_brier_high_minus_low": raw_delta,
        }

    high_all = pd.concat(all_high, ignore_index=True)
    low_all = pd.concat(all_low, ignore_index=True)
    pooled_excess_delta = float(
        high_all["excess_brier"].mean()
        - low_all["excess_brier"].mean()
    )
    pooled_raw_delta = float(
        high_all["market_brier"].mean()
        - low_all["market_brier"].mean()
    )

    y = split["actual_index"].to_numpy(dtype=int)
    market_p = split[
        ["market_home_prob", "market_draw_prob", "market_away_prob"]
    ].to_numpy(dtype=float)
    score_p = split[
        ["score_home_prob", "score_draw_prob", "score_away_prob"]
    ].to_numpy(dtype=float)

    counts_ok = all(
        by_league[league]["high_rows"] >= MIN_TAIL_ROWS_PER_LEAGUE
        and by_league[league]["low_rows"] >= MIN_TAIL_ROWS_PER_LEAGUE
        for league in LEAGUE_IDS
    )

    return {
        "season": season,
        "rows": int(len(split)),
        "tail_rows": int(len(high_all) + len(low_all)),
        "pooled_high_rows": int(len(high_all)),
        "pooled_low_rows": int(len(low_all)),
        "pooled_excess_brier_high_minus_low": pooled_excess_delta,
        "pooled_raw_brier_high_minus_low": pooled_raw_delta,
        "positive_excess_brier_leagues": int(positive_leagues),
        "league_count": len(LEAGUE_IDS),
        "minimum_tail_rows_per_league": MIN_TAIL_ROWS_PER_LEAGUE,
        "tail_counts_ok": bool(counts_ok),
        "by_league": by_league,
        "actual_1x2_market_scores": _multiclass_scores(y, market_p),
        "synthetic_score_model_1x2_scores": _multiclass_scores(y, score_p),
        "gap_vs_excess_brier_correlation": _safe_corr(
            split["score_gap_tv"],
            split["excess_brier"],
        ),
        "gap_vs_ah_fit_error_correlation": _safe_corr(
            split["score_gap_tv"],
            split["ah_fit_abs_error"],
        ),
        "ah_fit_abs_error": {
            "mean": float(split["ah_fit_abs_error"].mean()),
            "median": float(split["ah_fit_abs_error"].median()),
            "p95": float(split["ah_fit_abs_error"].quantile(0.95)),
            "max": float(split["ah_fit_abs_error"].max()),
        },
    }


def _stratified_tail_bootstrap(
    frame: pd.DataFrame,
    season: str,
) -> dict[str, float | int]:
    split = frame[frame["season"] == season].copy()
    rng = np.random.default_rng(BOOTSTRAP_SEED)

    groups: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for league in LEAGUE_IDS:
        local = split[split["league"] == league]
        high = local.loc[
            local["coherence_tail"] == "HIGH",
            "excess_brier",
        ].to_numpy(dtype=float)
        low = local.loc[
            local["coherence_tail"] == "LOW",
            "excess_brier",
        ].to_numpy(dtype=float)
        if len(high) < MIN_TAIL_ROWS_PER_LEAGUE or len(low) < MIN_TAIL_ROWS_PER_LEAGUE:
            raise RuntimeError(
                f"{league}/{season}: insufficient tail rows for frozen bootstrap"
            )
        groups[league] = (high, low)

    total_high = sum(len(pair[0]) for pair in groups.values())
    total_low = sum(len(pair[1]) for pair in groups.values())
    draws = np.empty(BOOTSTRAP_SAMPLES, dtype=float)

    for index in range(BOOTSTRAP_SAMPLES):
        high_sum = 0.0
        low_sum = 0.0
        for high, low in groups.values():
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
        draws[index] = (
            high_sum / total_high
            - low_sum / total_low
        )

    return {
        "samples": BOOTSTRAP_SAMPLES,
        "seed": BOOTSTRAP_SEED,
        "mean_delta": float(draws.mean()),
        "ci95_low": float(np.quantile(draws, 0.025)),
        "ci95_high": float(np.quantile(draws, 0.975)),
        "bootstrap_probability_positive": float(
            (draws > 0.0).mean()
        ),
    }


def evaluate() -> dict[str, object]:
    frames = []
    coverage = {}

    for league in LEAGUE_IDS:
        raw = _download_league_raw(league)
        league_frame, league_coverage = _build_league_rows(raw, league)
        frames.append(league_frame)
        coverage[league] = league_coverage

    combined = pd.concat(frames, ignore_index=True)
    combined = _attach_outcome_errors(combined)
    thresholds = _training_thresholds(combined)
    combined = _assign_tail(combined, thresholds)

    validation = _split_report(combined, VALIDATION_SEASON)
    validation_admissible = bool(
        validation["tail_counts_ok"]
        and validation["pooled_excess_brier_high_minus_low"] > 0.0
        and validation["positive_excess_brier_leagues"] >= 2
    )

    test = _split_report(combined, TEST_SEASON)
    test_bootstrap = None
    if test["tail_counts_ok"]:
        test_bootstrap = _stratified_tail_bootstrap(
            combined,
            TEST_SEASON,
        )

    test_gate = bool(
        test["tail_counts_ok"]
        and test["pooled_excess_brier_high_minus_low"] > 0.0
        and test["positive_excess_brier_leagues"] >= 2
        and test_bootstrap is not None
        and test_bootstrap["ci95_low"] > 0.0
    )

    supported = bool(validation_admissible and test_gate)

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "research_only": True,
        "betting_enabled": False,
        "production_promotion": False,
        "opened_2026_27_outcomes_used": False,
        "same_bookmaker": "BET365",
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "source_contract": {
            "one_x_two_columns": list(ONE_X_TWO_COLUMNS),
            "total_columns": list(TOTAL_COLUMNS),
            "ah_columns": list(AH_COLUMNS),
            "ah_line_columns": list(AH_LINE_COLUMNS),
            "half_goal_ah_only": True,
        },
        "reconstruction_contract": {
            "mu_bounds": list(MU_BOUNDS),
            "home_share_bounds": list(HOME_SHARE_BOUNDS),
            "primary_feature": "score_gap_tv",
            "tail_thresholds": "train-only league q25/q75",
            "primary_error_target": "excess_brier",
        },
        "coverage": coverage,
        "training_thresholds": thresholds,
        "validation": validation,
        "validation_admissible": validation_admissible,
        "test": test,
        "test_stratified_bootstrap": test_bootstrap,
        "supported": supported,
        "decision": (
            "CROSS_MARKET_COHERENCE_SUPPORTED"
            if supported
            else "NO_INDEPENDENT_CROSS_MARKET_COHERENCE_SIGNAL"
        ),
        "result": "NO_BET",
        "package_versions": {
            "pandas": pd.__version__,
            "numpy": np.__version__,
            "scipy": scipy.__version__,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path(
            "artifacts/cross_market_score_coherence_v1/report.json"
        ),
    )
    args = parser.parse_args()
    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
