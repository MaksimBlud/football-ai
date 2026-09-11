"""Frozen Eredivisie nested historical development protocol V1.

Research only. All admitted completed historical seasons are development evidence.
The structurally incomplete 2019-2020 season is excluded before any model result.
The current 2026-2027 source is never downloaded or inspected. No live database,
paid odds-provider access, model artifact creation, or production promotion occurs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
from feature_engineering import build_features
from league_model_sweep import (
    FEATURE_SETS,
    MODEL_VARIANTS,
    TARGET_MAP,
    make_model,
    market_probabilities,
    metrics,
)
from league_offline_history import parse_football_data_date, validate_complete_double_round_robin

PROTOCOL_VERSION = "eredivisie_nested_development_v1"
LEAGUE = "EREDIVISIE"
MAX_ALLOWED_SEASON = "2025-2026"
CURRENT_FORBIDDEN_SEASON = "2026-2027"
CONFIGURED_HISTORICAL_SEASONS = (
    "2016-2017",
    "2017-2018",
    "2018-2019",
    "2019-2020",
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
    "2026-2027",
)
STRUCTURALLY_EXCLUDED_SEASONS = ("2019-2020",)
ADMITTED_HISTORICAL_SEASONS = tuple(
    season
    for season in CONFIGURED_HISTORICAL_SEASONS
    if season not in STRUCTURALLY_EXCLUDED_SEASONS
    and season != CURRENT_FORBIDDEN_SEASON
)
DEVELOPMENT_OOS_SEASONS = (
    "2020-2021",
    "2021-2022",
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
)
OUTER_TEST_SEASONS = (
    "2022-2023",
    "2023-2024",
    "2024-2025",
    "2025-2026",
)
FEATURE_SET_ORDER = ("core", "core_elo", "full_no_odds")
MODEL_ORDER = ("logistic_l2", "xgb_shallow", "xgb_base", "xgb_regularized")
ALPHAS = tuple(round(float(value), 2) for value in np.arange(0.05, 0.51, 0.05))
REQUIRED_OUTER_SEASON_WINS = 3
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/{competition}.csv"

PRODUCTION_ARTIFACTS = (
    "football_model_xgboost_elo.pkl",
    "football_model_no_odds.pkl",
    "1x2_calibrator.pkl",
    "home_goals_model_no_odds.pkl",
    "away_goals_model_no_odds.pkl",
    "over_2_5_calibrator.pkl",
    "btts_calibrator.pkl",
)

REQUIRED_SOURCE_COLUMNS = {
    "Date",
    "HomeTeam",
    "AwayTeam",
    "FTHG",
    "FTAG",
    "FTR",
    "B365H",
    "B365D",
    "B365A",
}

COLUMN_MAP = {
    "Date": "match_date",
    "Time": "match_time",
    "HomeTeam": "home_team",
    "AwayTeam": "away_team",
    "FTHG": "home_goals",
    "FTAG": "away_goals",
    "FTR": "result",
    "HS": "home_shots",
    "AS": "away_shots",
    "HST": "home_shots_target",
    "AST": "away_shots_target",
    "HC": "home_corners",
    "AC": "away_corners",
    "HY": "home_yellow",
    "AY": "away_yellow",
    "HR": "home_red",
    "AR": "away_red",
    "B365H": "home_odds",
    "B365D": "draw_odds",
    "B365A": "away_odds",
}


def sha256(path: Path) -> str | None:
    if not path.exists():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def production_state(root: Path) -> dict[str, str | None]:
    return {name: sha256(root / name) for name in PRODUCTION_ARTIFACTS}


def assert_frozen_family() -> None:
    if tuple(name for name in FEATURE_SET_ORDER if name in FEATURE_SETS) != FEATURE_SET_ORDER:
        raise RuntimeError("Frozen feature family is no longer available")
    if tuple(name for name in MODEL_ORDER if name in MODEL_VARIANTS) != MODEL_ORDER:
        raise RuntimeError("Frozen model family is no longer available")
    if set(FEATURE_SETS) & set(FEATURE_SET_ORDER) != set(FEATURE_SET_ORDER):
        raise RuntimeError("Frozen feature family mismatch")
    if set(MODEL_VARIANTS) & set(MODEL_ORDER) != set(MODEL_ORDER):
        raise RuntimeError("Frozen model family mismatch")


def assert_historical_boundary(frame: pd.DataFrame) -> None:
    if frame.empty:
        raise ValueError("Eredivisie historical frame is empty")
    leagues = set(frame["league"].dropna().astype(str).unique())
    if leagues != {LEAGUE}:
        raise ValueError(f"Historical frame must be pure {LEAGUE}, got {sorted(leagues)}")
    seasons = sorted(frame["season"].dropna().astype(str).unique())
    if not seasons:
        raise ValueError("Historical frame has no seasons")
    if CURRENT_FORBIDDEN_SEASON in seasons or any(season > MAX_ALLOWED_SEASON for season in seasons):
        raise ValueError("Historical boundary violation: current/later-than-2025-2026 data is forbidden")
    excluded_present = [season for season in STRUCTURALLY_EXCLUDED_SEASONS if season in seasons]
    if excluded_present:
        raise ValueError(f"Structurally excluded Eredivisie seasons are forbidden: {excluded_present}")
    unexpected = [season for season in seasons if season not in ADMITTED_HISTORICAL_SEASONS]
    if unexpected:
        raise ValueError(f"Unexpected historical seasons outside frozen contract: {unexpected}")
    missing = [season for season in ADMITTED_HISTORICAL_SEASONS if season not in seasons]
    if missing:
        raise ValueError(f"Missing required admitted historical seasons: {missing}")
    missing_oos = [season for season in DEVELOPMENT_OOS_SEASONS if season not in seasons]
    if missing_oos:
        raise ValueError(f"Missing required development OOS seasons: {missing_oos}")


def download_source(url: str, path: Path) -> None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0 football-ai-research"})
    with urlopen(request, timeout=60) as response:
        content = response.read()
    if len(content) < 1000:
        raise RuntimeError(f"Downloaded file suspiciously small: {url} ({len(content)} bytes)")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _validate_required_source_columns(source: pd.DataFrame, *, season: str) -> None:
    missing = REQUIRED_SOURCE_COLUMNS - set(source.columns)
    if missing:
        raise ValueError(f"Eredivisie {season}: missing source columns {sorted(missing)}")


def validate_structurally_excluded_source(source: pd.DataFrame, *, season: str) -> None:
    if season not in STRUCTURALLY_EXCLUDED_SEASONS:
        raise ValueError(f"Season {season} is not frozen as structurally excluded")
    _validate_required_source_columns(source, season=season)
    teams = sorted(
        set(source["HomeTeam"].astype(str).str.strip())
        | set(source["AwayTeam"].astype(str).str.strip())
    )
    if season == "2019-2020":
        if len(teams) != 18:
            raise ValueError(f"Eredivisie {season}: expected 18 teams in terminated source")
        complete_matches = len(teams) * (len(teams) - 1)
        if not (0 < len(source) < complete_matches):
            raise ValueError(
                f"Eredivisie {season}: terminated source must contain fewer than {complete_matches} matches"
            )
    pairs = source[["HomeTeam", "AwayTeam"]].astype(str).apply(lambda col: col.str.strip())
    if (pairs["HomeTeam"] == pairs["AwayTeam"]).any():
        raise ValueError(f"Eredivisie {season}: team cannot play itself")
    if pairs.duplicated().any():
        raise ValueError(f"Eredivisie {season}: duplicate home/away pairing in terminated source")
    if not set(source["FTR"].astype(str)).issubset({"H", "D", "A"}):
        raise ValueError(f"Eredivisie {season}: unexpected result code")
    try:
        validate_complete_double_round_robin(source, season=season)
    except ValueError:
        return
    raise ValueError(f"Eredivisie {season}: excluded season unexpectedly became structurally complete")


def normalize_source(source: pd.DataFrame, *, season: str) -> pd.DataFrame:
    _validate_required_source_columns(source, season=season)
    validate_complete_double_round_robin(source, season=season)

    frame = pd.DataFrame()
    for source_column, target_column in COLUMN_MAP.items():
        frame[target_column] = source[source_column] if source_column in source.columns else pd.NA

    frame["match_date"] = parse_football_data_date(frame["match_date"])
    frame["match_time"] = frame["match_time"].fillna("00:00").astype(str)
    frame["home_team"] = frame["home_team"].astype(str).str.strip().replace(EREDIVISIE_RUNTIME_CONFIG.aliases)
    frame["away_team"] = frame["away_team"].astype(str).str.strip().replace(EREDIVISIE_RUNTIME_CONFIG.aliases)

    numeric = [
        "home_goals", "away_goals", "home_shots", "away_shots",
        "home_shots_target", "away_shots_target", "home_corners", "away_corners",
        "home_yellow", "away_yellow", "home_red", "away_red",
        "home_odds", "draw_odds", "away_odds",
    ]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    for column in (
        "home_shots", "away_shots", "home_shots_target", "away_shots_target",
        "home_corners", "away_corners", "home_yellow", "away_yellow", "home_red", "away_red",
    ):
        frame[column] = frame[column].fillna(0.0)

    frame["season"] = season
    frame["league"] = LEAGUE
    if not set(frame["result"].astype(str)).issubset({"H", "D", "A"}):
        raise ValueError(f"Eredivisie {season}: unexpected result code")
    if (frame[["home_odds", "draw_odds", "away_odds"]] <= 1.0).any().any():
        raise ValueError(f"Eredivisie {season}: invalid B365 1X2 odds")
    if frame.duplicated(subset=["season", "match_date", "home_team", "away_team"]).any():
        raise ValueError(f"Eredivisie {season}: duplicate canonical fixture after aliases")
    return frame


def build_historical_frame(work_dir: Path) -> tuple[pd.DataFrame, dict[str, int]]:
    config = EREDIVISIE_RUNTIME_CONFIG
    configured = tuple(config.historical_source.season_codes.values())
    if configured != CONFIGURED_HISTORICAL_SEASONS:
        raise RuntimeError(f"Configured Eredivisie history changed from frozen contract: {configured}")

    frames: list[pd.DataFrame] = []
    excluded_rows: dict[str, int] = {}
    competition = config.historical_source.competition_code
    for code, season in config.historical_source.season_codes.items():
        if season == CURRENT_FORBIDDEN_SEASON:
            continue
        if season > MAX_ALLOWED_SEASON:
            raise RuntimeError("Configured Eredivisie history crosses frozen development boundary")
        path = work_dir / "raw" / f"{competition}_{code}.csv"
        if not path.exists():
            url = BASE_URL.format(code=code, competition=competition)
            download_source(url, path)
        source = pd.read_csv(path, encoding_errors="replace")
        if season in STRUCTURALLY_EXCLUDED_SEASONS:
            validate_structurally_excluded_source(source, season=season)
            excluded_rows[season] = int(len(source))
            continue
        frames.append(normalize_source(source, season=season))

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["match_date", "match_time", "home_team", "away_team"], kind="stable"
    ).reset_index(drop=True)
    assert_historical_boundary(combined)
    if set(excluded_rows) != set(STRUCTURALLY_EXCLUDED_SEASONS):
        raise RuntimeError("Frozen structurally excluded Eredivisie season was not verified")
    return combined, excluded_rows


def add_warmup_and_elo(history: pd.DataFrame) -> pd.DataFrame:
    ordered = history.sort_values(
        ["match_date", "match_time", "home_team", "away_team"], kind="stable"
    ).reset_index(drop=True)
    counts: dict[str, int] = {}
    ratings: dict[str, float] = {}
    home_prior: list[int] = []
    away_prior: list[int] = []
    home_elos: list[float] = []
    away_elos: list[float] = []
    initial = float(EREDIVISIE_RUNTIME_CONFIG.elo.initial_rating)
    k_factor = float(EREDIVISIE_RUNTIME_CONFIG.elo.k_factor)
    home_advantage = float(EREDIVISIE_RUNTIME_CONFIG.elo.home_advantage)

    for row in ordered.itertuples(index=False):
        home = str(row.home_team)
        away = str(row.away_team)
        home_prior.append(counts.get(home, 0))
        away_prior.append(counts.get(away, 0))
        h_rating = ratings.get(home, initial)
        a_rating = ratings.get(away, initial)
        home_elos.append(h_rating)
        away_elos.append(a_rating)
        expected_home = 1.0 / (1.0 + 10.0 ** ((a_rating - (h_rating + home_advantage)) / 400.0))
        actual_home = 1.0 if str(row.result) == "H" else (0.0 if str(row.result) == "A" else 0.5)
        change = k_factor * (actual_home - expected_home)
        ratings[home] = h_rating + change
        ratings[away] = a_rating - change
        counts[home] = counts.get(home, 0) + 1
        counts[away] = counts.get(away, 0) + 1

    features = build_features(ordered.copy())
    features.insert(0, "league", LEAGUE)
    features["home_prior_matches"] = home_prior
    features["away_prior_matches"] = away_prior
    features["warmup_ok"] = (
        (features["home_prior_matches"] >= int(EREDIVISIE_RUNTIME_CONFIG.temporal.min_prior_matches))
        & (features["away_prior_matches"] >= int(EREDIVISIE_RUNTIME_CONFIG.temporal.min_prior_matches))
    )
    features["home_elo"] = home_elos
    features["away_elo"] = away_elos
    features["elo_difference"] = features["home_elo"] - features["away_elo"]
    features["target"] = features["result"].map(TARGET_MAP)
    features = features[features["warmup_ok"]].copy().reset_index(drop=True)
    assert_historical_boundary(features)
    return features


def candidate_key(feature_set: str, model_name: str) -> str:
    return f"{feature_set}::{model_name}"


def _renormalize(probabilities: np.ndarray) -> np.ndarray:
    p = np.asarray(probabilities, dtype=float)
    if p.ndim != 2 or p.shape[1] != 3:
        raise ValueError("probability matrix must have shape (n, 3)")
    if not np.isfinite(p).all() or (p < 0.0).any():
        raise ValueError("probability matrix contains invalid values")
    totals = p.sum(axis=1, keepdims=True)
    if (totals <= 0.0).any():
        raise ValueError("probability row has non-positive sum")
    return p / totals


def generate_oos_predictions(frame: pd.DataFrame) -> pd.DataFrame:
    assert_frozen_family()
    assert_historical_boundary(frame)
    rows: list[dict] = []
    for feature_set in FEATURE_SET_ORDER:
        feature_names = FEATURE_SETS[feature_set]
        for model_name in MODEL_ORDER:
            key = candidate_key(feature_set, model_name)
            for season in DEVELOPMENT_OOS_SEASONS:
                train = frame[frame["season"].astype(str) < season].copy()
                test = frame[frame["season"].astype(str) == season].copy()
                required = feature_names + ["target", "home_odds", "draw_odds", "away_odds"]
                train = train.dropna(subset=required)
                test = test.dropna(subset=required)
                if train.empty or test.empty:
                    raise RuntimeError(f"{key} {season}: empty chronological train/test fold")
                if train["season"].astype(str).max() >= season:
                    raise RuntimeError(f"{key} {season}: chronological leakage")
                if (train["season"].astype(str) == "2019-2020").any():
                    raise RuntimeError(f"{key} {season}: structurally excluded season leaked into training")
                model = make_model(model_name)
                model.fit(train[feature_names], train["target"].astype(int))
                ai = _renormalize(model.predict_proba(test[feature_names]))
                market = _renormalize(market_probabilities(test))
                y = test["target"].astype(int).to_numpy()
                for index, actual in enumerate(y):
                    rows.append({
                        "candidate": key,
                        "feature_set": feature_set,
                        "model": model_name,
                        "season": season,
                        "target": int(actual),
                        "ai_home": float(ai[index, 0]),
                        "ai_draw": float(ai[index, 1]),
                        "ai_away": float(ai[index, 2]),
                        "market_home": float(market[index, 0]),
                        "market_draw": float(market[index, 1]),
                        "market_away": float(market[index, 2]),
                    })
    return pd.DataFrame(rows)


def _arrays(predictions: pd.DataFrame, prefix: str) -> tuple[np.ndarray, np.ndarray]:
    y = predictions["target"].astype(int).to_numpy()
    p = predictions[[f"{prefix}_home", f"{prefix}_draw", f"{prefix}_away"]].astype(float).to_numpy()
    return y, _renormalize(p)


def metric_block(predictions: pd.DataFrame, prefix: str) -> dict[str, float]:
    y, p = _arrays(predictions, prefix)
    return metrics(y, p)


def hybrid_metrics(predictions: pd.DataFrame, alpha: float) -> dict[str, float]:
    y, ai = _arrays(predictions, "ai")
    _, market = _arrays(predictions, "market")
    hybrid = _renormalize(alpha * ai + (1.0 - alpha) * market)
    return metrics(y, hybrid)


def select_candidate(predictions: pd.DataFrame) -> tuple[str, dict[str, float]]:
    if predictions.empty:
        raise ValueError("No inner OOS predictions available for candidate selection")
    ranked = []
    for feature_index, feature_set in enumerate(FEATURE_SET_ORDER):
        for model_index, model_name in enumerate(MODEL_ORDER):
            key = candidate_key(feature_set, model_name)
            subset = predictions[predictions["candidate"] == key]
            if subset.empty:
                raise ValueError(f"Missing candidate predictions: {key}")
            score = metric_block(subset, "ai")
            ranked.append(
                (score["logloss"], score["brier"], -score["accuracy"], feature_index, model_index, key, score)
            )
    winner = min(ranked)
    return winner[5], winner[6]


def select_alpha(predictions: pd.DataFrame) -> tuple[float, dict[str, float]]:
    if predictions.empty:
        raise ValueError("No inner OOS predictions available for alpha selection")
    ranked = []
    for alpha in ALPHAS:
        score = hybrid_metrics(predictions, alpha)
        ranked.append((score["logloss"], score["brier"], -score["accuracy"], alpha, score))
    winner = min(ranked)
    return float(winner[3]), winner[4]


def beats_market(hybrid: dict[str, float], market: dict[str, float]) -> dict[str, bool]:
    return {
        "accuracy": hybrid["accuracy"] > market["accuracy"],
        "logloss": hybrid["logloss"] < market["logloss"],
        "brier": hybrid["brier"] < market["brier"],
    }


def evaluate_nested(predictions: pd.DataFrame) -> dict:
    outer_rows: list[dict] = []
    outer_selected_parts: list[pd.DataFrame] = []
    for test_season in OUTER_TEST_SEASONS:
        inner = predictions[predictions["season"].astype(str) < test_season].copy()
        allowed_inner = tuple(season for season in DEVELOPMENT_OOS_SEASONS if season < test_season)
        if tuple(sorted(inner["season"].unique())) != allowed_inner:
            raise RuntimeError(f"{test_season}: inner season boundary mismatch")
        winner, candidate_selection_metrics = select_candidate(inner)
        winner_inner = inner[inner["candidate"] == winner].copy()
        alpha, alpha_selection_metrics = select_alpha(winner_inner)
        test = predictions[
            (predictions["season"] == test_season) & (predictions["candidate"] == winner)
        ].copy()
        if test.empty:
            raise RuntimeError(f"{test_season}: selected candidate has no outer predictions")
        hybrid = hybrid_metrics(test, alpha)
        market = metric_block(test, "market")
        wins = beats_market(hybrid, market)
        outer_rows.append({
            "test_season": test_season,
            "selected_candidate": winner,
            "selected_alpha": alpha,
            "inner_oos_seasons": list(allowed_inner),
            "candidate_selection_metrics": candidate_selection_metrics,
            "alpha_selection_metrics": alpha_selection_metrics,
            "hybrid_metrics": hybrid,
            "market_metrics": market,
            "wins": wins,
            "all_three_win": all(wins.values()),
            "matches": int(len(test)),
        })
        selected = test.copy()
        selected["selected_alpha"] = alpha
        outer_selected_parts.append(selected)

    all_targets: list[np.ndarray] = []
    all_market_probabilities: list[np.ndarray] = []
    all_hybrid_probabilities: list[np.ndarray] = []
    for part in outer_selected_parts:
        alpha = float(part["selected_alpha"].iloc[0])
        y, ai = _arrays(part, "ai")
        _, market = _arrays(part, "market")
        all_targets.append(y)
        all_market_probabilities.append(market)
        all_hybrid_probabilities.append(_renormalize(alpha * ai + (1.0 - alpha) * market))
    y_outer = np.concatenate(all_targets)
    p_outer_market = _renormalize(np.vstack(all_market_probabilities))
    p_outer_hybrid = _renormalize(np.vstack(all_hybrid_probabilities))
    outer_hybrid = metrics(y_outer, p_outer_hybrid)
    outer_market = metrics(y_outer, p_outer_market)
    outer_aggregate_wins = beats_market(outer_hybrid, outer_market)

    win_counts = {
        metric_name: sum(1 for row in outer_rows if row["wins"][metric_name])
        for metric_name in ("accuracy", "logloss", "brier")
    }
    all_three_count = sum(1 for row in outer_rows if row["all_three_win"])

    final_candidate, final_candidate_selection_metrics = select_candidate(predictions)
    final_candidate_predictions = predictions[predictions["candidate"] == final_candidate].copy()
    final_alpha, final_alpha_selection_metrics = select_alpha(final_candidate_predictions)
    final_hybrid = hybrid_metrics(final_candidate_predictions, final_alpha)
    final_market = metric_block(final_candidate_predictions, "market")
    final_wins = beats_market(final_hybrid, final_market)

    gate = {
        "outer_aggregate_all_three": all(outer_aggregate_wins.values()),
        "outer_accuracy_wins_at_least_3_of_4": win_counts["accuracy"] >= REQUIRED_OUTER_SEASON_WINS,
        "outer_logloss_wins_at_least_3_of_4": win_counts["logloss"] >= REQUIRED_OUTER_SEASON_WINS,
        "outer_brier_wins_at_least_3_of_4": win_counts["brier"] >= REQUIRED_OUTER_SEASON_WINS,
        "outer_all_three_wins_at_least_3_of_4": all_three_count >= REQUIRED_OUTER_SEASON_WINS,
        "final_development_recipe_all_three": all(final_wins.values()),
    }
    passed = all(gate.values())
    return {
        "status": "ELIGIBLE_FOR_FUTURE_PROTOCOL_FREEZE" if passed else "REJECTED_NO_FREEZE_RECOMMENDATION",
        "protocol": PROTOCOL_VERSION,
        "league": LEAGUE,
        "all_admitted_historical_data_is_development_only": True,
        "untouched_holdout_claimed": False,
        "prospective_ai_ready": False,
        "model_ready": False,
        "artifact_created": False,
        "development_oos_seasons": list(DEVELOPMENT_OOS_SEASONS),
        "outer_test_seasons": list(OUTER_TEST_SEASONS),
        "outer_folds": outer_rows,
        "outer_aggregate": {
            "hybrid": outer_hybrid,
            "market": outer_market,
            "wins": outer_aggregate_wins,
            "metric_win_counts": win_counts,
            "all_three_win_count": all_three_count,
        },
        "final_development_recipe": {
            "candidate": final_candidate,
            "alpha": final_alpha,
            "candidate_selection_metrics": final_candidate_selection_metrics,
            "alpha_selection_metrics": final_alpha_selection_metrics,
            "hybrid_metrics": final_hybrid,
            "market_metrics": final_market,
            "wins": final_wins,
        },
        "gate": gate,
    }


def run(root: Path, work_dir: Path, output_path: Path) -> dict:
    before = production_state(root)
    history, excluded_rows = build_historical_frame(work_dir)
    features = add_warmup_and_elo(history)
    predictions = generate_oos_predictions(features)
    report = evaluate_nested(predictions)
    report["configured_historical_seasons"] = list(CONFIGURED_HISTORICAL_SEASONS)
    report["historical_seasons"] = sorted(history["season"].unique().tolist())
    report["structurally_excluded_seasons"] = list(STRUCTURALLY_EXCLUDED_SEASONS)
    report["structurally_excluded_source_rows"] = excluded_rows
    report["current_forbidden_season"] = CURRENT_FORBIDDEN_SEASON
    report["historical_rows"] = int(len(history))
    report["trainable_rows"] = int(len(features))
    report["candidate_count"] = len(FEATURE_SET_ORDER) * len(MODEL_ORDER)
    report["alpha_grid"] = list(ALPHAS)
    after = production_state(root)
    report["production_before"] = before
    report["production_after"] = after
    report["production_unchanged"] = before == after
    if before != after:
        raise RuntimeError("Production artifact state changed during Eredivisie research")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--work-dir", type=Path, default=Path("artifacts/eredivisie_nested_development_v1")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("experiments/eredivisie_nested_development_v1/latest.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    report = run(root, args.work_dir, args.output)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
