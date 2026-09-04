"""Leakage-safe Schedule Load Signal Lab.

Research only. Builds pre-match rest/congestion features from prior completed match
calendar dates and evaluates a frozen schedule-only and market+schedule comparison.
No production artifacts, Supabase writes, threshold search, or live activation.
"""
from __future__ import annotations

from collections import defaultdict, deque
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
MARKET_TRIPLETS = [
    ("B365H", "B365D", "B365A"),
    ("PSH", "PSD", "PSA"),
    ("AvgH", "AvgD", "AvgA"),
]
REST_DAY_CAP = 30.0
SCHEDULE_FEATURES = [
    "home_rest_days_capped",
    "away_rest_days_capped",
    "diff_rest_days_capped",
    "home_matches_7d",
    "away_matches_7d",
    "diff_matches_7d",
    "home_matches_14d",
    "away_matches_14d",
    "diff_matches_14d",
]
MARKET_FEATURES = ["market_home", "market_draw", "market_away"]


def _market_probabilities(row: pd.Series) -> tuple[float, float, float]:
    for h, d, a in MARKET_TRIPLETS:
        if all(column in row.index for column in (h, d, a)):
            odds = pd.to_numeric(pd.Series([row[h], row[d], row[a]]), errors="coerce").to_numpy(float)
            if np.isfinite(odds).all() and (odds > 1.0).all():
                inv = 1.0 / odds
                p = inv / inv.sum()
                return float(p[0]), float(p[1]), float(p[2])
    return np.nan, np.nan, np.nan


def _team_schedule_snapshot(history: deque[pd.Timestamp], current: pd.Timestamp, prefix: str) -> dict[str, float]:
    prior = [stamp for stamp in history if stamp < current]
    rest = np.nan if not prior else float((current - prior[-1]).days)
    rest_capped = np.nan if pd.isna(rest) else float(min(max(rest, 0.0), REST_DAY_CAP))
    matches_7d = float(sum(stamp >= current - pd.Timedelta(days=7) for stamp in prior))
    matches_14d = float(sum(stamp >= current - pd.Timedelta(days=14) for stamp in prior))
    return {
        f"{prefix}_rest_days_capped": rest_capped,
        f"{prefix}_matches_7d": matches_7d,
        f"{prefix}_matches_14d": matches_14d,
    }


def build_schedule_features(matches: pd.DataFrame, league: str) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTR", "_season"}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError("Missing required schedule columns: " + ", ".join(sorted(missing)))

    frame = matches.copy()
    frame["match_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    frame = frame.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "FTR", "_season"])
    frame = frame.sort_values("match_date", kind="stable")

    histories: dict[str, deque[pd.Timestamp]] = defaultdict(lambda: deque(maxlen=60))
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        current = pd.Timestamp(row["match_date"])
        home = str(row["HomeTeam"])
        away = str(row["AwayTeam"])
        record: dict[str, object] = {
            "league": league,
            "season": str(row["_season"]),
            "match_date": current,
            "home_team": home,
            "away_team": away,
            "result": str(row["FTR"]),
        }
        record.update(_team_schedule_snapshot(histories[home], current, "home"))
        record.update(_team_schedule_snapshot(histories[away], current, "away"))
        record["diff_rest_days_capped"] = (
            record["home_rest_days_capped"] - record["away_rest_days_capped"]
            if pd.notna(record["home_rest_days_capped"]) and pd.notna(record["away_rest_days_capped"])
            else np.nan
        )
        record["diff_matches_7d"] = record["home_matches_7d"] - record["away_matches_7d"]
        record["diff_matches_14d"] = record["home_matches_14d"] - record["away_matches_14d"]
        mh, md, ma = _market_probabilities(row)
        record.update({"market_home": mh, "market_draw": md, "market_away": ma})
        rows.append(record)

        # Current match becomes history only after its pre-match snapshot is frozen.
        histories[home].append(current)
        histories[away].append(current)

    return pd.DataFrame(rows)


def _model() -> Pipeline:
    return Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000)),
        ]
    )


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_schedule_lab(frame: pd.DataFrame, min_train_seasons: int = 3) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for league, league_df in frame.groupby("league"):
        seasons = sorted(league_df["season"].dropna().unique())
        for index in range(min_train_seasons, len(seasons)):
            train = league_df[league_df["season"].isin(seasons[:index])].copy()
            test = league_df[league_df["season"] == seasons[index]].copy()
            train = train.dropna(subset=MARKET_FEATURES + ["result"])
            test = test.dropna(subset=MARKET_FEATURES + ["result"])
            if train.empty or test.empty:
                continue
            y_train = train["result"].map(RESULT_TO_INT).to_numpy()
            y_test = test["result"].map(RESULT_TO_INT).to_numpy()

            raw = test[MARKET_FEATURES].to_numpy(float)
            raw = raw / raw.sum(axis=1, keepdims=True)
            rows.append(
                {
                    "league": league,
                    "test_season": seasons[index],
                    "feature_set": "MARKET_RAW",
                    "matches": len(y_test),
                    **_score(y_test, raw),
                }
            )

            for name, columns in (
                ("SCHEDULE_ONLY", SCHEDULE_FEATURES),
                ("MARKET_MODEL", MARKET_FEATURES),
                ("MARKET_SCHEDULE", MARKET_FEATURES + SCHEDULE_FEATURES),
            ):
                model = _model()
                model.fit(train[columns], y_train)
                probabilities = model.predict_proba(test[columns])
                rows.append(
                    {
                        "league": league,
                        "test_season": seasons[index],
                        "feature_set": name,
                        "matches": len(y_test),
                        **_score(y_test, probabilities),
                    }
                )
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (league, feature_set), group in results.groupby(["league", "feature_set"]):
        weights = group["matches"].to_numpy()
        rows.append(
            {
                "league": league,
                "feature_set": feature_set,
                "matches": int(group["matches"].sum()),
                "seasons": int(len(group)),
                "accuracy": float(np.average(group["accuracy"], weights=weights)),
                "brier": float(np.average(group["brier"], weights=weights)),
                "log_loss": float(np.average(group["log_loss"], weights=weights)),
            }
        )
    return pd.DataFrame(rows).sort_values(["league", "brier"])


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    baseline = results[results["feature_set"] == "MARKET_MODEL"]
    candidate = results[results["feature_set"] == "MARKET_SCHEDULE"]
    paired = candidate.merge(
        baseline,
        on=["league", "test_season"],
        suffixes=("_candidate", "_baseline"),
        validate="one_to_one",
    )
    if len(paired) != len(candidate):
        raise ValueError("Incomplete paired schedule coverage")
    out = pd.DataFrame(
        {
            "league": paired["league"],
            "test_season": paired["test_season"],
            "matches": paired["matches_candidate"].astype(int),
            "delta_accuracy": paired["accuracy_candidate"] - paired["accuracy_baseline"],
            "delta_brier": paired["brier_candidate"] - paired["brier_baseline"],
            "delta_log_loss": paired["log_loss_candidate"] - paired["log_loss_baseline"],
        }
    )
    out["brier_win"] = out["delta_brier"] < 0
    out["log_loss_win"] = out["delta_log_loss"] < 0
    return out.sort_values(["league", "test_season"])


def summarize_incremental(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league, group in paired.groupby("league"):
        weights = group["matches"].to_numpy()
        rows.append(
            {
                "league": league,
                "matches": int(group["matches"].sum()),
                "seasons": int(len(group)),
                "mean_delta_accuracy": float(np.average(group["delta_accuracy"], weights=weights)),
                "mean_delta_brier": float(np.average(group["delta_brier"], weights=weights)),
                "mean_delta_log_loss": float(np.average(group["delta_log_loss"], weights=weights)),
                "brier_wins": int(group["brier_win"].sum()),
                "log_loss_wins": int(group["log_loss_win"].sum()),
                "brier_win_rate": float(group["brier_win"].mean()),
                "log_loss_win_rate": float(group["log_loss_win"].mean()),
            }
        )
    return pd.DataFrame(rows).sort_values("league")


def write_reports(frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_schedule_lab(frame)
    summary = summarize(detail)
    paired = paired_incremental(detail)
    paired_summary = summarize_incremental(paired)
    detail.to_csv(output_dir / "schedule_load_detail.csv", index=False)
    summary.to_csv(output_dir / "schedule_load_summary.csv", index=False)
    paired.to_csv(output_dir / "schedule_load_paired.csv", index=False)
    paired_summary.to_csv(output_dir / "schedule_load_paired_summary.csv", index=False)
    return summary, paired_summary
