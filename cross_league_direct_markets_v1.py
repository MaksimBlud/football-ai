"""Frozen cross-league direct-market V1 historical temporal-OOT research.

Direct targets:
- full-time Over/Under 2.5;
- full-time Asian Handicap home cover on integer/half-goal lines.

Research only. No production promotion, Supabase writes, paid provider calls, or
2026-27 outcomes.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import requests
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from historical_football_signal_lab import (
    add_difference_features,
    build_point_in_time_features,
)
from historical_football_signal_runner import BASE, LEAGUES

EXPERIMENT_ID = "CROSS_LEAGUE_DIRECT_MARKETS_V1"
LEAGUE_IDS = ("EPL", "LA_LIGA", "SERIE_A")
TRAIN_SEASONS = tuple(f"{y}-{y + 1}" for y in range(2016, 2024))
VALIDATION_SEASON = "2024-2025"
TEST_SEASON = "2025-2026"
ALLOWED_SEASONS = set(TRAIN_SEASONS) | {VALIDATION_SEASON, TEST_SEASON}

TOTAL_PAIRS = (
    ("B365>2.5", "B365<2.5"),
    ("P>2.5", "P<2.5"),
    ("Avg>2.5", "Avg<2.5"),
)
AH_PAIRS = (
    ("B365AHH", "B365AHA"),
    ("PAHH", "PAHA"),
    ("AvgAHH", "AvgAHA"),
)
AH_LINE_COLUMNS = ("AHh", "B365AH")

OU_FEATURES = [
    "market_logit",
    "home_goals_for_10",
    "home_goals_against_10",
    "away_goals_for_10",
    "away_goals_against_10",
    "home_corners_for_10",
    "home_corners_against_10",
    "away_corners_for_10",
    "away_corners_against_10",
    "home_goals_for_venue5",
    "home_goals_against_venue5",
    "away_goals_for_venue5",
    "away_goals_against_venue5",
    "home_corners_for_venue5",
    "home_corners_against_venue5",
    "away_corners_for_venue5",
    "away_corners_against_venue5",
]

AH_FEATURES = [
    "market_logit",
    "ah_line",
    "diff_points_10",
    "diff_goals_for_10",
    "diff_goals_against_10",
    "diff_corners_for_10",
    "diff_corners_against_10",
    "diff_points_venue5",
    "diff_goals_for_venue5",
    "diff_goals_against_venue5",
    "diff_corners_for_venue5",
    "diff_corners_against_venue5",
]


def _first_pair(row: pd.Series, pairs: tuple[tuple[str, str], ...]):
    for first, second in pairs:
        a = pd.to_numeric(row.get(first), errors="coerce")
        b = pd.to_numeric(row.get(second), errors="coerce")
        if np.isfinite(a) and np.isfinite(b) and a > 1.0 and b > 1.0:
            return float(a), float(b), f"{first}/{second}"
    return None


def _first_line(row: pd.Series) -> tuple[float, str] | None:
    for column in AH_LINE_COLUMNS:
        value = pd.to_numeric(row.get(column), errors="coerce")
        if np.isfinite(value):
            return float(value), column
    return None


def _binary_devig(first_odds: float, second_odds: float) -> float:
    inv_first = 1.0 / first_odds
    inv_second = 1.0 / second_odds
    return float(inv_first / (inv_first + inv_second))


def _logit(probability: float) -> float:
    p = float(np.clip(probability, 1e-6, 1.0 - 1e-6))
    return float(np.log(p / (1.0 - p)))


def _is_half_step_line(line: float) -> bool:
    return bool(np.isclose(line * 2.0, round(line * 2.0), atol=1e-9))


def _settle_ah_home(home_goals: float, away_goals: float, line: float) -> int | None:
    margin = float(home_goals + line - away_goals)
    if np.isclose(margin, 0.0, atol=1e-9):
        return None
    return int(margin > 0.0)


def _binary_scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    y = np.asarray(y, dtype=int)
    p = np.clip(np.asarray(p, dtype=float), 1e-12, 1.0 - 1e-12)
    return {
        "accuracy": float(((p >= 0.5).astype(int) == y).mean()),
        "brier": float(np.mean((p - y) ** 2)),
        "log_loss": float(log_loss(y, np.column_stack([1.0 - p, p]), labels=[0, 1])),
    }


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(C=0.1, max_iter=2000)),
        ]
    )


def _download_league_raw(league: str) -> pd.DataFrame:
    config = LEAGUES[league]
    frames: list[pd.DataFrame] = []
    for code, season in config.historical_source.season_codes.items():
        if season not in ALLOWED_SEASONS:
            continue
        response = requests.get(
            BASE.format(code=code, comp=config.historical_source.competition_code),
            timeout=60,
        )
        response.raise_for_status()
        frame = pd.read_csv(pd.io.common.BytesIO(response.content))
        frame["_season"] = season
        frames.append(frame)
    if not frames:
        raise RuntimeError(f"{league}: no historical frames")
    raw = pd.concat(frames, ignore_index=True)
    raw["match_date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
    return raw.sort_values("match_date", kind="stable").reset_index(drop=True)


def _point_in_time_state(raw: pd.DataFrame, league: str) -> pd.DataFrame:
    features = build_point_in_time_features(raw, league, "MULTI_SEASON")
    features = add_difference_features(features)
    keys = raw[["match_date", "HomeTeam", "AwayTeam", "_season"]].copy()
    keys = keys.rename(
        columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "_season": "season"}
    )
    keys = keys.drop_duplicates(
        subset=["match_date", "home_team", "away_team"], keep="last"
    )
    features = features.drop(columns=["season"]).merge(
        keys,
        on=["match_date", "home_team", "away_team"],
        how="left",
        validate="one_to_one",
    )
    if features["season"].isna().any():
        raise RuntimeError(f"{league}: failed to restore season labels")
    return features


def _market_targets(raw: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for _, row in raw.iterrows():
        date = row.get("match_date")
        home = row.get("HomeTeam")
        away = row.get("AwayTeam")
        season = row.get("_season")
        hg = pd.to_numeric(row.get("FTHG"), errors="coerce")
        ag = pd.to_numeric(row.get("FTAG"), errors="coerce")
        if pd.isna(date) or pd.isna(home) or pd.isna(away) or not np.isfinite(hg) or not np.isfinite(ag):
            continue

        total = _first_pair(row, TOTAL_PAIRS)
        if total is not None:
            over_odds, under_odds, source = total
            probability = _binary_devig(over_odds, under_odds)
            rows.append(
                {
                    "match_date": date,
                    "home_team": str(home),
                    "away_team": str(away),
                    "season": season,
                    "market": "OU25",
                    "market_probability": probability,
                    "market_logit": _logit(probability),
                    "target": int(float(hg) + float(ag) > 2.5),
                    "ah_line": np.nan,
                    "price_source": source,
                    "line_source": None,
                }
            )

        ah_pair = _first_pair(row, AH_PAIRS)
        ah_line = _first_line(row)
        if ah_pair is not None and ah_line is not None:
            home_odds, away_odds, price_source = ah_pair
            line, line_source = ah_line
            if _is_half_step_line(line):
                target = _settle_ah_home(float(hg), float(ag), line)
                if target is not None:
                    probability = _binary_devig(home_odds, away_odds)
                    rows.append(
                        {
                            "match_date": date,
                            "home_team": str(home),
                            "away_team": str(away),
                            "season": season,
                            "market": "AH",
                            "market_probability": probability,
                            "market_logit": _logit(probability),
                            "target": target,
                            "ah_line": line,
                            "price_source": price_source,
                            "line_source": line_source,
                        }
                    )
    return pd.DataFrame(rows)


def load_league_frame(league: str) -> pd.DataFrame:
    raw = _download_league_raw(league)
    state = _point_in_time_state(raw, league)
    targets = _market_targets(raw)
    if targets.empty:
        raise RuntimeError(f"{league}: no direct-market target rows")
    merged = targets.merge(
        state,
        on=["match_date", "home_team", "away_team", "season"],
        how="left",
        validate="many_to_one",
    )
    return merged.sort_values(["match_date", "home_team", "away_team", "market"]).reset_index(drop=True)


def _evaluate_market(frame: pd.DataFrame, league: str, market: str) -> tuple[dict, dict]:
    subset = frame[frame["market"] == market].copy()
    features = OU_FEATURES if market == "OU25" else AH_FEATURES
    train = subset[subset["season"].isin(TRAIN_SEASONS)].copy()
    validation = subset[subset["season"] == VALIDATION_SEASON].copy()
    test = subset[subset["season"] == TEST_SEASON].copy()
    if train.empty or validation.empty or test.empty:
        raise RuntimeError(
            f"{league}/{market}: empty split train={len(train)} validation={len(validation)} test={len(test)}"
        )

    estimator = _model()
    estimator.fit(train[features], train["target"].astype(int).to_numpy())

    y_validation = validation["target"].astype(int).to_numpy()
    p_market_validation = validation["market_probability"].to_numpy(float)
    p_candidate_validation = estimator.predict_proba(validation[features])[:, 1]
    validation_market = _binary_scores(y_validation, p_market_validation)
    validation_candidate = _binary_scores(y_validation, p_candidate_validation)
    validation_admissible = (
        validation_candidate["brier"] < validation_market["brier"]
        and validation_candidate["log_loss"] < validation_market["log_loss"]
    )

    y_test = test["target"].astype(int).to_numpy()
    p_market_test = test["market_probability"].to_numpy(float)
    p_raw_candidate_test = estimator.predict_proba(test[features])[:, 1]
    p_selected_test = p_raw_candidate_test if validation_admissible else p_market_test.copy()

    test_market = _binary_scores(y_test, p_market_test)
    test_raw_candidate = _binary_scores(y_test, p_raw_candidate_test)
    test_selected = _binary_scores(y_test, p_selected_test)
    passed = bool(
        validation_admissible
        and test_raw_candidate["brier"] < test_market["brier"]
        and test_raw_candidate["log_loss"] < test_market["log_loss"]
    )

    coverage = {
        "train": int(len(train)),
        "validation": int(len(validation)),
        "test": int(len(test)),
        "price_sources": dict(Counter(subset["price_source"].dropna().astype(str))),
    }
    if market == "AH":
        coverage["line_sources"] = dict(Counter(subset["line_source"].dropna().astype(str)))

    report = {
        "league": league,
        "market": market,
        "features": features,
        "coverage": coverage,
        "validation_market": validation_market,
        "validation_candidate": validation_candidate,
        "validation_delta_brier": validation_candidate["brier"] - validation_market["brier"],
        "validation_delta_log_loss": validation_candidate["log_loss"] - validation_market["log_loss"],
        "validation_admissible": bool(validation_admissible),
        "test_market": test_market,
        "test_raw_candidate": test_raw_candidate,
        "test_selected": test_selected,
        "test_delta_brier": test_raw_candidate["brier"] - test_market["brier"],
        "test_delta_log_loss": test_raw_candidate["log_loss"] - test_market["log_loss"],
        "replication_status": "PASS" if passed else "FAIL",
        "final_active_mode": "CANDIDATE" if passed else "MARKET_FALLBACK",
    }
    pooled = {
        "y": y_test,
        "market": p_market_test,
        "selected": p_selected_test,
        "passed": passed,
    }
    return report, pooled


def evaluate() -> dict:
    league_reports: list[dict] = []
    pooled_parts: dict[str, list[dict]] = {"OU25": [], "AH": []}

    for league in LEAGUE_IDS:
        frame = load_league_frame(league)
        for market in ("OU25", "AH"):
            report, pooled = _evaluate_market(frame, league, market)
            league_reports.append(report)
            pooled_parts[market].append(pooled)

    market_decisions = {}
    for market, parts in pooled_parts.items():
        y = np.concatenate([part["y"] for part in parts])
        p_market = np.concatenate([part["market"] for part in parts])
        p_selected = np.concatenate([part["selected"] for part in parts])
        market_scores = _binary_scores(y, p_market)
        selected_scores = _binary_scores(y, p_selected)
        pass_count = sum(bool(part["passed"]) for part in parts)
        pooled_better = (
            selected_scores["brier"] < market_scores["brier"]
            and selected_scores["log_loss"] < market_scores["log_loss"]
        )
        decision = "PILOT" if pass_count >= 2 and pooled_better else "SKIP"
        market_decisions[market] = {
            "league_pass_count": int(pass_count),
            "league_count": len(parts),
            "pooled_n": int(len(y)),
            "pooled_market": market_scores,
            "pooled_validation_selected": selected_scores,
            "pooled_delta_brier": selected_scores["brier"] - market_scores["brier"],
            "pooled_delta_log_loss": selected_scores["log_loss"] - market_scores["log_loss"],
            "pooled_better_both": bool(pooled_better),
            "decision": decision,
        }

    return {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": "HISTORICAL_TEMPORAL_OOT",
        "research_only": True,
        "production_promotion": False,
        "betting_enabled": False,
        "result": "NO_BET",
        "opened_2026_27_outcomes_used": False,
        "train_seasons": list(TRAIN_SEASONS),
        "validation_season": VALIDATION_SEASON,
        "test_season": TEST_SEASON,
        "league_reports": league_reports,
        "market_decisions": market_decisions,
        "bookmaker_corners": {
            "status": "DATA_UNAVAILABLE",
            "decision": "COLLECT",
            "bookmaker_line_price_evaluated": False,
            "post_match_corner_counts_substituted_for_prices": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/cross_league_direct_markets_v1/report.json"),
    )
    args = parser.parse_args()
    report = evaluate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
