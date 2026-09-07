"""Leakage-safe Historical Football Signal Lab.

Research only. Builds pre-match rolling football-state features from Football-Data
match rows and evaluates fixed feature ablations with expanding-season walk-forward.
No production artifacts, Supabase writes, Structural activation, or threshold search.
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
STAT_COLUMNS = {
    "goals": ("FTHG", "FTAG"),
    "corners": ("HC", "AC"),
    "yellow": ("HY", "AY"),
    "red": ("HR", "AR"),
}
MARKET_TRIPLETS = [("B365H", "B365D", "B365A"), ("PSH", "PSD", "PSA"), ("AvgH", "AvgD", "AvgA")]

@dataclass(frozen=True)
class TeamMatch:
    points: float
    goals_for: float
    goals_against: float
    corners_for: float
    corners_against: float
    yellow: float
    red: float
    venue_home: bool


def _mean(history, attr: str, n: int) -> float:
    values = [getattr(x, attr) for x in list(history)[-n:] if pd.notna(getattr(x, attr))]
    return float(np.mean(values)) if values else np.nan


def _venue_mean(history, attr: str, n: int, home: bool) -> float:
    values = [getattr(x, attr) for x in history if x.venue_home == home and pd.notna(getattr(x, attr))]
    values = values[-n:]
    return float(np.mean(values)) if values else np.nan


def _snapshot(history, prefix: str) -> dict[str, float]:
    out = {f"{prefix}_prior_matches": float(len(history))}
    for n in (5, 10):
        for attr in ("points", "goals_for", "goals_against", "corners_for", "corners_against", "yellow", "red"):
            out[f"{prefix}_{attr}_{n}"] = _mean(history, attr, n)
    venue_home = prefix == "home"
    for attr in ("points", "goals_for", "goals_against", "corners_for", "corners_against"):
        out[f"{prefix}_{attr}_venue5"] = _venue_mean(history, attr, 5, venue_home)
    return out


def _market_probabilities(row: pd.Series) -> tuple[float, float, float]:
    for h, d, a in MARKET_TRIPLETS:
        if all(c in row.index for c in (h, d, a)):
            odds = pd.to_numeric(pd.Series([row[h], row[d], row[a]]), errors="coerce").to_numpy(float)
            if np.isfinite(odds).all() and (odds > 1.0).all():
                inv = 1.0 / odds
                p = inv / inv.sum()
                return float(p[0]), float(p[1]), float(p[2])
    return np.nan, np.nan, np.nan


def build_point_in_time_features(matches: pd.DataFrame, league: str, season: str) -> pd.DataFrame:
    required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError("Missing required historical columns: " + ", ".join(sorted(missing)))
    frame = matches.copy()
    frame["match_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    frame = frame.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "FTR"]).sort_values("match_date", kind="stable")
    histories: dict[str, deque] = defaultdict(lambda: deque(maxlen=30))
    rows = []
    for _, row in frame.iterrows():
        home, away = str(row.HomeTeam), str(row.AwayTeam)
        record = {"league": league, "season": season, "match_date": row.match_date, "home_team": home, "away_team": away, "result": row.FTR}
        record.update(_snapshot(histories[home], "home"))
        record.update(_snapshot(histories[away], "away"))
        mh, md, ma = _market_probabilities(row)
        record.update({"market_home": mh, "market_draw": md, "market_away": ma})
        rows.append(record)

        hg, ag = float(row.FTHG), float(row.FTAG)
        hp, ap = (3.0, 0.0) if hg > ag else ((0.0, 3.0) if hg < ag else (1.0, 1.0))
        vals = {}
        for name, (hc, ac) in STAT_COLUMNS.items():
            vals[name] = (pd.to_numeric(row.get(hc), errors="coerce"), pd.to_numeric(row.get(ac), errors="coerce"))
        histories[home].append(TeamMatch(hp, hg, ag, vals["corners"][0], vals["corners"][1], vals["yellow"][0], vals["red"][0], True))
        histories[away].append(TeamMatch(ap, ag, hg, vals["corners"][1], vals["corners"][0], vals["yellow"][1], vals["red"][1], False))
    return pd.DataFrame(rows)


def add_difference_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for suffix in ("points_5", "points_10", "goals_for_5", "goals_for_10", "goals_against_5", "goals_against_10", "corners_for_5", "corners_for_10", "corners_against_5", "corners_against_10", "yellow_5", "yellow_10", "red_5", "red_10", "points_venue5", "goals_for_venue5", "goals_against_venue5", "corners_for_venue5", "corners_against_venue5"):
        out[f"diff_{suffix}"] = out[f"home_{suffix}"] - out[f"away_{suffix}"]
    return out

FEATURE_SETS = {
    "FORM": ["diff_points_5", "diff_points_10", "diff_points_venue5"],
    "FORM_GOALS": ["diff_points_5", "diff_points_10", "diff_points_venue5", "diff_goals_for_5", "diff_goals_for_10", "diff_goals_against_5", "diff_goals_against_10", "diff_goals_for_venue5", "diff_goals_against_venue5"],
    "FORM_GOALS_CORNERS": ["diff_points_5", "diff_points_10", "diff_points_venue5", "diff_goals_for_5", "diff_goals_for_10", "diff_goals_against_5", "diff_goals_against_10", "diff_corners_for_5", "diff_corners_for_10", "diff_corners_against_5", "diff_corners_against_10", "diff_corners_for_venue5", "diff_corners_against_venue5"],
    "ALL_FOOTBALL": ["diff_points_5", "diff_points_10", "diff_points_venue5", "diff_goals_for_5", "diff_goals_for_10", "diff_goals_against_5", "diff_goals_against_10", "diff_corners_for_5", "diff_corners_for_10", "diff_corners_against_5", "diff_corners_against_10", "diff_yellow_5", "diff_yellow_10", "diff_red_5", "diff_red_10", "diff_goals_for_venue5", "diff_goals_against_venue5", "diff_corners_for_venue5", "diff_corners_against_venue5"],
}
FEATURE_SETS["MARKET"] = ["market_home", "market_draw", "market_away"]
FEATURE_SETS["MARKET_ALL_FOOTBALL"] = FEATURE_SETS["MARKET"] + FEATURE_SETS["ALL_FOOTBALL"]


def _scores(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {"accuracy": float((p.argmax(axis=1) == y).mean()), "brier": float(np.mean(np.sum((p-onehot)**2, axis=1))), "log_loss": float(log_loss(y, p, labels=[0,1,2]))}


def walk_forward_ablation(frame: pd.DataFrame, min_train_seasons: int = 3) -> pd.DataFrame:
    frame = add_difference_features(frame)
    rows = []
    for league, league_df in frame.groupby("league"):
        seasons = sorted(league_df["season"].unique())
        for i in range(min_train_seasons, len(seasons)):
            train_seasons, test_season = seasons[:i], seasons[i]
            train = league_df[league_df.season.isin(train_seasons)].copy()
            test = league_df[league_df.season == test_season].copy()
            for name, features in FEATURE_SETS.items():
                usable_train = train.dropna(subset=["result"])
                usable_test = test.dropna(subset=["result"])
                if name == "MARKET":
                    usable_test = usable_test.dropna(subset=features)
                    p = usable_test[features].to_numpy(float)
                    p = p / p.sum(axis=1, keepdims=True)
                else:
                    model = Pipeline([("imputer", SimpleImputer(strategy="median")), ("scale", StandardScaler()), ("model", LogisticRegression(max_iter=1000, multi_class="auto"))])
                    y_train = usable_train.result.map(RESULT_TO_INT).to_numpy()
                    model.fit(usable_train[features], y_train)
                    p = model.predict_proba(usable_test[features])
                y = usable_test.result.map(RESULT_TO_INT).to_numpy()
                metrics = _scores(y, p)
                rows.append({"league": league, "test_season": test_season, "feature_set": name, "matches": len(y), **metrics})
    return pd.DataFrame(rows)


def summarize_walk_forward(results: pd.DataFrame) -> pd.DataFrame:
    weighted = []
    for (league, feature_set), group in results.groupby(["league", "feature_set"]):
        n = int(group.matches.sum())
        weighted.append({"league": league, "feature_set": feature_set, "matches": n, "seasons": len(group), **{m: float(np.average(group[m], weights=group.matches)) for m in ("accuracy", "brier", "log_loss")}})
    return pd.DataFrame(weighted).sort_values(["league", "brier"])


def write_reports(features: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    wf = walk_forward_ablation(features)
    summary = summarize_walk_forward(wf)
    paths = {"features": output_dir/"point_in_time_features.csv", "walk_forward": output_dir/"walk_forward_ablation.csv", "summary": output_dir/"ablation_summary.csv"}
    features.to_csv(paths["features"], index=False); wf.to_csv(paths["walk_forward"], index=False); summary.to_csv(paths["summary"], index=False)
    return paths
