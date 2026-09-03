"""Pre-registered prospective MARKET_MODEL vs MARKET_AVAILABILITY evaluator.

This module must not be used for scoring until readiness passes for all three
leagues. Its model family mirrors the closed historical market-incremental lab.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from prospective_availability_features import FEATURE_COLUMNS, build_availability_features

MARKET_COLUMNS = (
    "market_home_probability",
    "market_draw_probability",
    "market_away_probability",
)
RESEARCH_LEAGUES = ("EPL", "LA_LIGA", "SERIE_A")
RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
CUTOFF_HOURS_BEFORE_KICKOFF = 6
MIN_TRAIN_MATCHES_PER_LEAGUE = 60
MIN_TEST_MATCHES_PER_BLOCK = 20
MIN_EVALUATION_BLOCKS_PER_LEAGUE = 2
MIN_CALENDAR_MONTHS_PER_LEAGUE = 4
MIN_PAIRED_MATCHES_PER_LEAGUE = 100


def select_frozen_market_rows(market_snapshots: pd.DataFrame) -> pd.DataFrame:
    required = {
        "league", "home_team", "away_team", "commence_time_utc", "snapshot_time_utc", *MARKET_COLUMNS
    }
    missing = required.difference(market_snapshots.columns)
    if missing:
        raise ValueError(f"Market snapshots missing columns: {sorted(missing)}")
    frame = market_snapshots.copy()
    frame["commence_time_utc"] = pd.to_datetime(frame["commence_time_utc"], utc=True, errors="coerce")
    frame["snapshot_time_utc"] = pd.to_datetime(frame["snapshot_time_utc"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["commence_time_utc", "snapshot_time_utc", *MARKET_COLUMNS])
    ceiling = frame["commence_time_utc"] - pd.Timedelta(hours=CUTOFF_HOURS_BEFORE_KICKOFF)
    frame = frame.loc[frame["snapshot_time_utc"] <= ceiling].copy()
    identity = ["league", "home_team", "away_team", "commence_time_utc"]
    frame = frame.sort_values("snapshot_time_utc").drop_duplicates(identity, keep="last")
    probabilities = frame[list(MARKET_COLUMNS)].apply(pd.to_numeric, errors="coerce")
    frame = frame.loc[~probabilities.isna().any(axis=1)].copy()
    probabilities = frame[list(MARKET_COLUMNS)].astype(float)
    sums = probabilities.sum(axis=1)
    if (sums <= 0).any():
        raise ValueError("Market probabilities must have positive row sums")
    frame.loc[:, list(MARKET_COLUMNS)] = probabilities.div(sums, axis=0)
    return frame.reset_index(drop=True)


def build_paired_research_frame(
    market_snapshots: pd.DataFrame,
    polls: pd.DataFrame,
    observations: pd.DataFrame,
) -> pd.DataFrame:
    selected = select_frozen_market_rows(market_snapshots)
    featured = build_availability_features(selected, polls, observations)
    return featured.loc[featured["availability_covered"].astype(bool)].reset_index(drop=True)


def readiness(frame: pd.DataFrame) -> pd.DataFrame:
    required = {"league", "commence_time_utc", "result", "availability_covered"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Readiness frame missing columns: {sorted(missing)}")
    work = frame.loc[
        frame["availability_covered"].astype(bool)
        & frame["result"].isin(RESULT_TO_INT)
    ].copy()
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work = work.dropna(subset=["commence_time_utc"])
    work["calendar_month"] = work["commence_time_utc"].dt.to_period("M").astype(str)
    rows = []
    for league in RESEARCH_LEAGUES:
        group = work.loc[work["league"].astype(str) == league].copy()
        month_counts = group.groupby("calendar_month").size().sort_index()
        eligible_blocks = 0
        cumulative = 0
        for count in month_counts.tolist():
            if cumulative >= MIN_TRAIN_MATCHES_PER_LEAGUE and count >= MIN_TEST_MATCHES_PER_BLOCK:
                eligible_blocks += 1
            cumulative += int(count)
        matches = len(group)
        months = int(group["calendar_month"].nunique())
        ready = (
            matches >= MIN_PAIRED_MATCHES_PER_LEAGUE
            and months >= MIN_CALENDAR_MONTHS_PER_LEAGUE
            and eligible_blocks >= MIN_EVALUATION_BLOCKS_PER_LEAGUE
        )
        rows.append(
            {
                "league": league,
                "paired_finished_matches": matches,
                "calendar_months": months,
                "eligible_evaluation_blocks": eligible_blocks,
                "ready": bool(ready),
            }
        )
    return pd.DataFrame(rows)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )


def _score(y: np.ndarray, probabilities: np.ndarray) -> dict:
    one_hot = np.eye(3)[y]
    return {
        "accuracy": float((probabilities.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((probabilities - one_hot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, probabilities, labels=[0, 1, 2])),
    }


def run_preregistered_evaluation(frame: pd.DataFrame) -> pd.DataFrame:
    state = readiness(frame)
    if not bool(state["ready"].all()):
        detail = state.to_dict(orient="records")
        raise RuntimeError(f"PROSPECTIVE_SAMPLE_NOT_READY: {detail}")
    work = frame.copy()
    work["commence_time_utc"] = pd.to_datetime(work["commence_time_utc"], utc=True, errors="coerce")
    work["calendar_month"] = work["commence_time_utc"].dt.to_period("M").astype(str)
    rows = []
    for league in RESEARCH_LEAGUES:
        group = work.loc[
            (work["league"].astype(str) == league)
            & work["availability_covered"].astype(bool)
            & work["result"].isin(RESULT_TO_INT)
        ].sort_values("commence_time_utc")
        months = sorted(group["calendar_month"].unique())
        for test_month in months:
            test = group.loc[group["calendar_month"] == test_month]
            train = group.loc[group["calendar_month"] < test_month]
            if len(train) < MIN_TRAIN_MATCHES_PER_LEAGUE or len(test) < MIN_TEST_MATCHES_PER_BLOCK:
                continue
            y_train = train["result"].map(RESULT_TO_INT).to_numpy()
            y_test = test["result"].map(RESULT_TO_INT).to_numpy()
            if len(set(y_train.tolist())) < 3:
                raise RuntimeError(f"Training block lacks all three 1X2 classes for {league}/{test_month}")
            for name, columns in (
                ("MARKET_MODEL", list(MARKET_COLUMNS)),
                ("MARKET_AVAILABILITY", list(MARKET_COLUMNS) + list(FEATURE_COLUMNS)),
            ):
                model = _model()
                model.fit(train[columns], y_train)
                probabilities = model.predict_proba(test[columns])
                rows.append(
                    {
                        "league": league,
                        "test_month": test_month,
                        "feature_set": name,
                        "matches": len(test),
                        **_score(y_test, probabilities),
                    }
                )
    return pd.DataFrame(rows)


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    baseline = results.loc[results["feature_set"] == "MARKET_MODEL"]
    candidate = results.loc[results["feature_set"] == "MARKET_AVAILABILITY"]
    merged = candidate.merge(
        baseline,
        on=["league", "test_month"],
        suffixes=("_candidate", "_baseline"),
        validate="one_to_one",
    )
    if len(merged) != len(candidate) or len(merged) != len(baseline):
        raise ValueError("Incomplete paired prospective evaluation coverage")
    return pd.DataFrame(
        {
            "league": merged["league"],
            "test_month": merged["test_month"],
            "matches": merged["matches_candidate"].astype(int),
            "delta_accuracy": merged["accuracy_candidate"] - merged["accuracy_baseline"],
            "delta_brier": merged["brier_candidate"] - merged["brier_baseline"],
            "delta_log_loss": merged["log_loss_candidate"] - merged["log_loss_baseline"],
        }
    ).sort_values(["league", "test_month"])
