"""Leakage-safe SHOTS10 Signal Lab.

Research only. Builds 10-match rolling shot-volume and shots-on-target state from
prior completed matches and evaluates schedule-independent incremental value over market.
"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

RESULT_TO_INT = {"H": 0, "D": 1, "A": 2}
MARKET_TRIPLETS = [("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA"), ("AvgH", "AvgD", "AvgA")]
MARKET_FEATURES = ["market_home", "market_draw", "market_away"]
SHOTS_FEATURES = [
    "diff_shots_for_10",
    "diff_shots_against_10",
    "diff_sot_for_10",
    "diff_sot_against_10",
]


@dataclass(frozen=True)
class ShotMatch:
    shots_for: float
    shots_against: float
    sot_for: float
    sot_against: float


def _market_probabilities(row: pd.Series) -> tuple[float, float, float]:
    for h, d, a in MARKET_TRIPLETS:
        if all(column in row.index for column in (h, d, a)):
            odds = pd.to_numeric(pd.Series([row[h], row[d], row[a]]), errors="coerce").to_numpy(float)
            if np.isfinite(odds).all() and (odds > 1.0).all():
                inv = 1.0 / odds
                p = inv / inv.sum()
                return float(p[0]), float(p[1]), float(p[2])
    return np.nan, np.nan, np.nan


def _mean(history: deque[ShotMatch], attr: str) -> float:
    values = [getattr(item, attr) for item in list(history)[-10:] if pd.notna(getattr(item, attr))]
    return float(np.mean(values)) if values else np.nan


def _snapshot(history: deque[ShotMatch], prefix: str) -> dict[str, float]:
    return {
        f"{prefix}_shots_for_10": _mean(history, "shots_for"),
        f"{prefix}_shots_against_10": _mean(history, "shots_against"),
        f"{prefix}_sot_for_10": _mean(history, "sot_for"),
        f"{prefix}_sot_against_10": _mean(history, "sot_against"),
    }


def build_shots10_features(matches: pd.DataFrame, league: str) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTR", "_season", "HS", "AS", "HST", "AST"}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError("Missing required SHOTS10 columns: " + ", ".join(sorted(missing)))

    frame = matches.copy()
    frame["match_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    frame = frame.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "FTR", "_season"])
    frame = frame.sort_values("match_date", kind="stable")

    histories: dict[str, deque[ShotMatch]] = defaultdict(lambda: deque(maxlen=30))
    rows: list[dict[str, object]] = []
    for _, row in frame.iterrows():
        home = str(row["HomeTeam"])
        away = str(row["AwayTeam"])
        record: dict[str, object] = {
            "league": league,
            "season": str(row["_season"]),
            "match_date": pd.Timestamp(row["match_date"]),
            "home_team": home,
            "away_team": away,
            "result": str(row["FTR"]),
        }
        record.update(_snapshot(histories[home], "home"))
        record.update(_snapshot(histories[away], "away"))
        for suffix in ("shots_for_10", "shots_against_10", "sot_for_10", "sot_against_10"):
            record[f"diff_{suffix}"] = record[f"home_{suffix}"] - record[f"away_{suffix}"]
        mh, md, ma = _market_probabilities(row)
        record.update({"market_home": mh, "market_draw": md, "market_away": ma})
        rows.append(record)

        hs = pd.to_numeric(row.get("HS"), errors="coerce")
        ass = pd.to_numeric(row.get("AS"), errors="coerce")
        hst = pd.to_numeric(row.get("HST"), errors="coerce")
        ast = pd.to_numeric(row.get("AST"), errors="coerce")
        histories[home].append(ShotMatch(hs, ass, hst, ast))
        histories[away].append(ShotMatch(ass, hs, ast, hst))

    return pd.DataFrame(rows)


def _model() -> Pipeline:
    return Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
        ("model", LogisticRegression(max_iter=1000)),
    ])


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_shots10_lab(frame: pd.DataFrame, min_train_seasons: int = 3) -> pd.DataFrame:
    rows = []
    for league, group in frame.groupby("league"):
        seasons = sorted(group["season"].dropna().unique())
        for index in range(min_train_seasons, len(seasons)):
            train = group[group["season"].isin(seasons[:index])].dropna(subset=MARKET_FEATURES + ["result"]).copy()
            test = group[group["season"] == seasons[index]].dropna(subset=MARKET_FEATURES + ["result"]).copy()
            if train.empty or test.empty:
                continue
            y_train = train["result"].map(RESULT_TO_INT).to_numpy()
            y_test = test["result"].map(RESULT_TO_INT).to_numpy()

            raw = test[MARKET_FEATURES].to_numpy(float)
            raw = raw / raw.sum(axis=1, keepdims=True)
            rows.append({"league": league, "test_season": seasons[index], "feature_set": "MARKET_RAW", "matches": len(y_test), **_score(y_test, raw)})

            for name, columns in (
                ("SHOTS10_ONLY", SHOTS_FEATURES),
                ("MARKET_MODEL", MARKET_FEATURES),
                ("MARKET_SHOTS10", MARKET_FEATURES + SHOTS_FEATURES),
            ):
                model = _model()
                model.fit(train[columns], y_train)
                p = model.predict_proba(test[columns])
                rows.append({"league": league, "test_season": seasons[index], "feature_set": name, "matches": len(y_test), **_score(y_test, p)})
    return pd.DataFrame(rows)


def summarize(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (league, feature_set), group in results.groupby(["league", "feature_set"]):
        weights = group["matches"].to_numpy()
        rows.append({
            "league": league,
            "feature_set": feature_set,
            "matches": int(group["matches"].sum()),
            "seasons": int(len(group)),
            "accuracy": float(np.average(group["accuracy"], weights=weights)),
            "brier": float(np.average(group["brier"], weights=weights)),
            "log_loss": float(np.average(group["log_loss"], weights=weights)),
        })
    return pd.DataFrame(rows).sort_values(["league", "brier"])


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    baseline = results[results["feature_set"] == "MARKET_MODEL"]
    candidate = results[results["feature_set"] == "MARKET_SHOTS10"]
    paired = candidate.merge(baseline, on=["league", "test_season"], suffixes=("_candidate", "_baseline"), validate="one_to_one")
    if len(paired) != len(candidate):
        raise ValueError("Incomplete paired SHOTS10 coverage")
    out = pd.DataFrame({
        "league": paired["league"],
        "test_season": paired["test_season"],
        "matches": paired["matches_candidate"].astype(int),
        "delta_accuracy": paired["accuracy_candidate"] - paired["accuracy_baseline"],
        "delta_brier": paired["brier_candidate"] - paired["brier_baseline"],
        "delta_log_loss": paired["log_loss_candidate"] - paired["log_loss_baseline"],
    })
    out["brier_win"] = out["delta_brier"] < 0
    out["log_loss_win"] = out["delta_log_loss"] < 0
    return out.sort_values(["league", "test_season"])


def summarize_incremental(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for league, group in paired.groupby("league"):
        weights = group["matches"].to_numpy()
        rows.append({
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
        })
    return pd.DataFrame(rows).sort_values("league")


def write_reports(frame: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_shots10_lab(frame)
    summary = summarize(detail)
    paired = paired_incremental(detail)
    paired_summary = summarize_incremental(paired)
    detail.to_csv(output_dir / "shots10_detail.csv", index=False)
    summary.to_csv(output_dir / "shots10_summary.csv", index=False)
    paired.to_csv(output_dir / "shots10_paired.csv", index=False)
    paired_summary.to_csv(output_dir / "shots10_paired_summary.csv", index=False)
    return summary, paired_summary
