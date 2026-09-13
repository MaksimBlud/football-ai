"""Leakage-safe historical shot-quality proxy research.

Research only. Uses Football-Data shots and shots-on-target as a fixed proxy profile.
It does not label these statistics as xG and fails closed when shot columns are absent.
True xG remains a separate data-source capability gate.
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

from historical_football_signal_lab import RESULT_TO_INT, add_difference_features
from historical_football_market_incremental import CORNERS10, MARKET

SHOT_COLUMNS = ("HS", "AS", "HST", "AST")
XG_COLUMN_PAIRS = (
    ("HxG", "AxG"),
    ("HomeXG", "AwayXG"),
    ("home_xg", "away_xg"),
    ("xG_Home", "xG_Away"),
)
SHOT_QUALITY10 = [
    "diff_shots_for_10",
    "diff_shots_against_10",
    "diff_sot_for_10",
    "diff_sot_against_10",
    "diff_sot_rate_for_10",
    "diff_sot_rate_against_10",
]
FEATURE_SETS = {
    "CORNERS10": CORNERS10,
    "CORNERS10_SHOT_QUALITY": CORNERS10 + SHOT_QUALITY10,
    "MARKET_MODEL": MARKET,
    "MARKET_SHOT_QUALITY": MARKET + SHOT_QUALITY10,
}
PAIRS = (
    ("CORNERS10", "CORNERS10_SHOT_QUALITY"),
    ("MARKET_MODEL", "MARKET_SHOT_QUALITY"),
)
EVIDENCE_TIER = {
    "EPL": "PRIMARY",
    "LA_LIGA": "PRIMARY",
    "SERIE_A": "SOURCE_CAVEAT_SENSITIVITY",
}


@dataclass(frozen=True)
class TeamShotMatch:
    shots_for: float
    shots_against: float
    sot_for: float
    sot_against: float


def source_capability(frame: pd.DataFrame) -> dict[str, object]:
    """Report shot availability and detect, but never synthesize, true-xG columns."""
    missing_shots = [column for column in SHOT_COLUMNS if column not in frame.columns]
    xg_pair = next(
        (pair for pair in XG_COLUMN_PAIRS if pair[0] in frame.columns and pair[1] in frame.columns),
        None,
    )
    return {
        "shots_complete": not missing_shots,
        "missing_shot_columns": tuple(missing_shots),
        "true_xg_pair_detected": xg_pair is not None,
        "true_xg_columns": xg_pair,
    }


def _mean(history: deque[TeamShotMatch], attr: str, n: int = 10) -> float:
    values = [getattr(item, attr) for item in list(history)[-n:]]
    values = [value for value in values if pd.notna(value)]
    return float(np.mean(values)) if values else np.nan


def _rate(
    history: deque[TeamShotMatch],
    numerator: str,
    denominator: str,
    n: int = 10,
) -> float:
    items = list(history)[-n:]
    pairs = [
        (getattr(item, numerator), getattr(item, denominator))
        for item in items
        if pd.notna(getattr(item, numerator)) and pd.notna(getattr(item, denominator))
    ]
    if not pairs:
        return np.nan
    num = float(sum(pair[0] for pair in pairs))
    den = float(sum(pair[1] for pair in pairs))
    return num / den if den > 0 else np.nan


def build_point_in_time_shot_quality(matches: pd.DataFrame, league: str) -> pd.DataFrame:
    """Build fixed rolling-10 shot/SOT profiles using only prior fixtures."""
    required = {"Date", "HomeTeam", "AwayTeam", *SHOT_COLUMNS}
    missing = required - set(matches.columns)
    if missing:
        raise ValueError("Missing required shot-quality columns: " + ", ".join(sorted(missing)))

    frame = matches.copy()
    frame["match_date"] = pd.to_datetime(frame["Date"], dayfirst=True, errors="coerce")
    frame = frame.dropna(subset=["match_date", "HomeTeam", "AwayTeam"]).sort_values(
        ["match_date", "HomeTeam", "AwayTeam"], kind="stable"
    )
    histories: dict[str, deque[TeamShotMatch]] = defaultdict(lambda: deque(maxlen=30))
    rows: list[dict[str, object]] = []

    for _, row in frame.iterrows():
        home, away = str(row.HomeTeam), str(row.AwayTeam)
        record: dict[str, object] = {
            "league": league,
            "match_date": row.match_date,
            "home_team": home,
            "away_team": away,
        }
        for team, prefix in ((home, "home"), (away, "away")):
            history = histories[team]
            record[f"{prefix}_shots_for_10"] = _mean(history, "shots_for")
            record[f"{prefix}_shots_against_10"] = _mean(history, "shots_against")
            record[f"{prefix}_sot_for_10"] = _mean(history, "sot_for")
            record[f"{prefix}_sot_against_10"] = _mean(history, "sot_against")
            record[f"{prefix}_sot_rate_for_10"] = _rate(history, "sot_for", "shots_for")
            record[f"{prefix}_sot_rate_against_10"] = _rate(
                history, "sot_against", "shots_against"
            )
        rows.append(record)

        hs, ass, hst, ast = (
            pd.to_numeric(row.HS, errors="coerce"),
            pd.to_numeric(row.AS, errors="coerce"),
            pd.to_numeric(row.HST, errors="coerce"),
            pd.to_numeric(row.AST, errors="coerce"),
        )
        histories[home].append(TeamShotMatch(hs, ass, hst, ast))
        histories[away].append(TeamShotMatch(ass, hs, ast, hst))

    out = pd.DataFrame(rows)
    for suffix in (
        "shots_for_10",
        "shots_against_10",
        "sot_for_10",
        "sot_against_10",
        "sot_rate_for_10",
        "sot_rate_against_10",
    ):
        out[f"diff_{suffix}"] = out[f"home_{suffix}"] - out[f"away_{suffix}"]
    return out


def _score(y: np.ndarray, p: np.ndarray) -> dict[str, float]:
    onehot = np.eye(3)[y]
    return {
        "accuracy": float((p.argmax(axis=1) == y).mean()),
        "brier": float(np.mean(np.sum((p - onehot) ** 2, axis=1))),
        "log_loss": float(log_loss(y, p, labels=[0, 1, 2])),
    }


def run_shot_quality_ablation(
    frame: pd.DataFrame,
    min_train_seasons: int = 3,
) -> pd.DataFrame:
    enriched = add_difference_features(frame)
    rows = []
    for league, league_df in enriched.groupby("league"):
        seasons = sorted(league_df.season.unique())
        for i in range(min_train_seasons, len(seasons)):
            train = league_df[league_df.season.isin(seasons[:i])]
            test = league_df[league_df.season == seasons[i]]
            for name, columns in FEATURE_SETS.items():
                market_based = name.startswith("MARKET")
                usable_train = (
                    train.dropna(subset=MARKET + ["result"])
                    if market_based
                    else train.dropna(subset=["result"])
                )
                usable_test = (
                    test.dropna(subset=MARKET + ["result"])
                    if market_based
                    else test.dropna(subset=["result"])
                )
                if usable_train.empty or usable_test.empty:
                    continue
                model = Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scale", StandardScaler()),
                        ("model", LogisticRegression(max_iter=1000)),
                    ]
                )
                y_train = usable_train.result.map(RESULT_TO_INT).to_numpy()
                y = usable_test.result.map(RESULT_TO_INT).to_numpy()
                model.fit(usable_train[columns], y_train)
                p = model.predict_proba(usable_test[columns])
                rows.append(
                    {
                        "league": league,
                        "evidence_tier": EVIDENCE_TIER.get(league, "UNCLASSIFIED"),
                        "test_season": seasons[i],
                        "feature_set": name,
                        "matches": len(y),
                        **_score(y, p),
                    }
                )
    return pd.DataFrame(rows)


def paired_incremental(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for baseline, candidate in PAIRS:
        base = results[results.feature_set == baseline]
        cand = results[results.feature_set == candidate]
        merged = cand.merge(
            base,
            on=["league", "evidence_tier", "test_season"],
            suffixes=("_candidate", "_baseline"),
            validate="one_to_one",
        )
        if len(merged) != len(cand):
            raise ValueError(f"incomplete paired coverage for {candidate}")
        for _, row in merged.iterrows():
            rows.append(
                {
                    "league": row.league,
                    "evidence_tier": row.evidence_tier,
                    "test_season": row.test_season,
                    "baseline": baseline,
                    "candidate": candidate,
                    "matches": int(row.matches_candidate),
                    "delta_accuracy": float(row.accuracy_candidate-row.accuracy_baseline),
                    "delta_brier": float(row.brier_candidate-row.brier_baseline),
                    "delta_log_loss": float(row.log_loss_candidate-row.log_loss_baseline),
                }
            )
    return pd.DataFrame(rows).sort_values(["baseline", "league", "test_season"])


def summarize_paired(paired: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (league, tier, baseline, candidate), group in paired.groupby(
        ["league", "evidence_tier", "baseline", "candidate"]
    ):
        weights = group.matches.to_numpy()
        rows.append(
            {
                "league": league,
                "evidence_tier": tier,
                "baseline": baseline,
                "candidate": candidate,
                "matches": int(group.matches.sum()),
                "seasons": len(group),
                "mean_delta_accuracy": float(np.average(group.delta_accuracy, weights=weights)),
                "mean_delta_brier": float(np.average(group.delta_brier, weights=weights)),
                "mean_delta_log_loss": float(np.average(group.delta_log_loss, weights=weights)),
                "brier_wins": int((group.delta_brier < 0).sum()),
                "log_loss_wins": int((group.delta_log_loss < 0).sum()),
            }
        )
    return pd.DataFrame(rows).sort_values(["baseline", "league"])


def write_shot_quality_reports(frame: pd.DataFrame, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    detail = run_shot_quality_ablation(frame)
    paired = paired_incremental(detail)
    summary = summarize_paired(paired)
    detail.to_csv(output_dir / "shot_quality_proxy_ablation.csv", index=False)
    paired.to_csv(output_dir / "shot_quality_proxy_paired.csv", index=False)
    summary.to_csv(output_dir / "shot_quality_proxy_summary.csv", index=False)
    return summary
