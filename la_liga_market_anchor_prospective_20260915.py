"""Freeze and generate pre-match La Liga Market Anchor shadow predictions for 2026-09-15.

Research-only prospective diagnostic. This script deliberately contains no outcome fields and
fails closed if executed at or after the first target kickoff. It reuses the exact historical
feature/model primitives from the frozen Market Anchor V2 source commit but defines a new,
predeclared La Liga analogue: ALL_FOOTBALL, L2=1, market fallback active, lambda=1 shadow.

No production .pkl is read/written, no Supabase call is made, and no Odds API call is made.
Market probabilities are the durable pre-match snapshot captured in Supabase on 2026-09-11.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types
from typing import Any, Mapping

import numpy as np
import pandas as pd
import requests

EXPERIMENT_ID = "LA_LIGA_MARKET_ANCHOR_PROSPECTIVE_20260915_V1"
EVIDENCE_CLASS = "PROSPECTIVE_SHADOW"
SOURCE_COMMIT = "df19777087fb89af049eedce44ff93f0aa6e6360"
LEAGUE = "LA_LIGA"
FEATURE_VARIANT = "ALL_FOOTBALL"
SHADOW_LAMBDA = 1.0
ACTIVE_LAMBDA = 0.0
L2_PENALTY = 1.0
TRAINING_DATA_THROUGH = pd.Timestamp("2026-06-30T23:59:59Z")
FEATURE_HISTORY_CUTOFF = pd.Timestamp("2026-09-15T00:00:00Z")
FIRST_KICKOFF = pd.Timestamp("2026-09-15T17:00:00Z")
BASE_URL = "https://www.football-data.co.uk/mmz4281/{code}/SP1.csv"
TRAIN_SEASONS = {
    "1617": "2016-2017",
    "1718": "2017-2018",
    "1819": "2018-2019",
    "1920": "2019-2020",
    "2021": "2020-2021",
    "2122": "2021-2022",
    "2223": "2022-2023",
    "2324": "2023-2024",
    "2425": "2024-2025",
    "2526": "2025-2026",
}
CURRENT_SEASON_CODE = "2627"
EXPECTED_FROZEN_GIT_BLOBS = {
    "historical_football_signal_lab.py": "401b3a0893371bfa4a488ec92a4a54af2678c8f7",
    "market_anchor_1x2_v1.py": "58c35bf3768f7bf2b951f19a37b9a5f46b6b9801",
}
SOURCE_NAME = {
    "Rayo Vallecano": "Vallecano",
    "Espanyol": "Espanol",
    "Alavés": "Alaves",
    "Elche CF": "Elche",
}

TARGETS: tuple[dict[str, Any], ...] = (
    {
        "event_id": "b9a6e597fd597637efa24b92d51dda62",
        "home_team": "Rayo Vallecano",
        "away_team": "Espanyol",
        "kickoff_utc": "2026-09-15T17:00:00Z",
        "market_snapshot_time_utc": "2026-09-11T15:45:28.192487Z",
        "bookmakers_count": 19,
        "market": [0.46932048598728, 0.275291229511983, 0.255388284500737],
    },
    {
        "event_id": "d6474326396cdd0e300afd0193c7c93d",
        "home_team": "Alavés",
        "away_team": "Valencia",
        "kickoff_utc": "2026-09-15T18:00:00Z",
        "market_snapshot_time_utc": "2026-09-11T15:45:28.192487Z",
        "bookmakers_count": 19,
        "market": [0.447759791488515, 0.304537995169928, 0.247702213341557],
    },
    {
        "event_id": "0b57607f4a514ee24df31b0c2db9ddc5",
        "home_team": "Elche CF",
        "away_team": "Real Madrid",
        "kickoff_utc": "2026-09-15T19:30:00Z",
        "market_snapshot_time_utc": "2026-09-11T15:45:28.192487Z",
        "bookmakers_count": 19,
        "market": [0.104522793893611, 0.165700942434781, 0.729776263671608],
    },
)

FORBIDDEN_OUTCOME_KEYS = {"result", "outcome", "score", "final_score", "home_goals", "away_goals", "ftr"}


def _sha256_json(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def git_blob_sha1(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def load_frozen_modules(source_dir: Path):
    for filename, expected in EXPECTED_FROZEN_GIT_BLOBS.items():
        path = source_dir / filename
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = git_blob_sha1(path)
        if actual != expected:
            raise RuntimeError(f"frozen source mismatch for {filename}: {actual} != {expected}")
    lab = load_module("historical_football_signal_lab", source_dir / "historical_football_signal_lab.py")
    runner_stub = types.ModuleType("historical_football_signal_runner")
    runner_stub.LEAGUES = {}
    runner_stub.download = lambda *args, **kwargs: None
    sys.modules["historical_football_signal_runner"] = runner_stub
    v1 = load_module("market_anchor_1x2_v1", source_dir / "market_anchor_1x2_v1.py")
    if float(v1.L2_PENALTY) != L2_PENALTY:
        raise RuntimeError("frozen L2 penalty changed")
    if FEATURE_VARIANT not in lab.FEATURE_SETS:
        raise RuntimeError("frozen feature variant missing")
    return lab, v1


def download_csv(code: str) -> tuple[pd.DataFrame, str]:
    url = BASE_URL.format(code=code)
    response = requests.get(url, timeout=60, headers={"User-Agent": "football-ai-la-liga-prospective/1"})
    response.raise_for_status()
    if len(response.content) < 500:
        raise RuntimeError(f"suspiciously small Football-Data response for {code}")
    return pd.read_csv(pd.io.common.BytesIO(response.content)), hashlib.sha256(response.content).hexdigest()


def build_training_frame(lab) -> tuple[pd.DataFrame, dict[str, str], dict[str, pd.DataFrame]]:
    raw_frames: list[pd.DataFrame] = []
    hashes: dict[str, str] = {}
    by_code: dict[str, pd.DataFrame] = {}
    for code, season in TRAIN_SEASONS.items():
        frame, digest = download_csv(code)
        by_code[code] = frame.copy()
        hashes[code] = digest
        frame = frame.copy()
        frame["_season"] = season
        raw_frames.append(frame)
    raw = pd.concat(raw_frames, ignore_index=True)
    features = lab.build_point_in_time_features(raw, LEAGUE, "MULTI_SEASON")
    keys = raw[["Date", "HomeTeam", "AwayTeam", "_season"]].copy()
    keys["match_date"] = pd.to_datetime(keys["Date"], dayfirst=True, errors="coerce")
    keys = keys.rename(columns={"HomeTeam": "home_team", "AwayTeam": "away_team", "_season": "season"})[
        ["match_date", "home_team", "away_team", "season"]
    ].drop_duplicates()
    features = features.drop(columns=["season"]).merge(
        keys, on=["match_date", "home_team", "away_team"], how="left", validate="one_to_one"
    )
    if features["season"].isna().any():
        raise RuntimeError("failed to restore training season labels")
    return features, hashes, by_code


def fit_artifact(lab, v1, frame: pd.DataFrame) -> dict[str, Any]:
    prepared = v1._prepare(frame)
    prepared = prepared[(prepared["league"] == LEAGUE) & prepared["season"].isin(TRAIN_SEASONS.values())].copy()
    if prepared.empty:
        raise RuntimeError("no eligible La Liga training rows")
    if pd.to_datetime(prepared["match_date"]).max() > TRAINING_DATA_THROUGH.tz_localize(None):
        raise RuntimeError("training data exceeds frozen cutoff")
    features = list(lab.FEATURE_SETS[FEATURE_VARIANT])
    market = v1._market(prepared)
    y = prepared["result"].map(lab.RESULT_TO_INT).to_numpy()
    model = v1.fit_residual_model(prepared[features], y, market, l2_penalty=L2_PENALTY)
    artifact = {
        "experiment_id": EXPERIMENT_ID,
        "league": LEAGUE,
        "feature_variant": FEATURE_VARIANT,
        "features": features,
        "shadow_lambda": SHADOW_LAMBDA,
        "active_lambda": ACTIVE_LAMBDA,
        "l2_penalty": L2_PENALTY,
        "training_data_through_utc": TRAINING_DATA_THROUGH.isoformat(),
        "training_rows": int(len(prepared)),
        "imputer_medians": [float(x) for x in model.imputer.statistics_],
        "scaler_mean": [float(x) for x in model.scaler.mean_],
        "scaler_scale": [float(x) for x in model.scaler.scale_],
        "weights": [[float(x) for x in row] for row in model.weights],
    }
    artifact["artifact_sha256"] = _sha256_json(artifact)
    return artifact


def build_target_features(lab, historical_by_code: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, str, dict[str, int]]:
    current, current_sha256 = download_csv(CURRENT_SEASON_CODE)
    frames = [historical_by_code[code].copy() for code in TRAIN_SEASONS]
    frames.append(current.copy())
    raw = pd.concat(frames, ignore_index=True)
    raw["match_date"] = pd.to_datetime(raw["Date"], dayfirst=True, errors="coerce")
    raw = raw.dropna(subset=["match_date", "HomeTeam", "AwayTeam", "FTR"])
    raw = raw.loc[raw["match_date"] < FEATURE_HISTORY_CUTOFF.tz_localize(None)].sort_values("match_date", kind="stable")

    histories = defaultdict(lambda: deque(maxlen=30))
    for _, row in raw.iterrows():
        home, away = str(row.HomeTeam), str(row.AwayTeam)
        hg, ag = float(row.FTHG), float(row.FTAG)
        hp, ap = (3.0, 0.0) if hg > ag else ((0.0, 3.0) if hg < ag else (1.0, 1.0))
        vals = {}
        for name, (home_col, away_col) in lab.STAT_COLUMNS.items():
            vals[name] = (pd.to_numeric(row.get(home_col), errors="coerce"), pd.to_numeric(row.get(away_col), errors="coerce"))
        histories[home].append(lab.TeamMatch(hp, hg, ag, vals["corners"][0], vals["corners"][1], vals["yellow"][0], vals["red"][0], True))
        histories[away].append(lab.TeamMatch(ap, ag, hg, vals["corners"][1], vals["corners"][0], vals["yellow"][1], vals["red"][1], False))

    records: list[dict[str, Any]] = []
    prior_counts: dict[str, int] = {}
    for target in TARGETS:
        home_source = SOURCE_NAME.get(target["home_team"], target["home_team"])
        away_source = SOURCE_NAME.get(target["away_team"], target["away_team"])
        if home_source not in histories or away_source not in histories:
            known = sorted(histories.keys())
            raise RuntimeError(f"missing source history for {home_source} vs {away_source}; known tail={known[-30:]}")
        record = {"event_id": target["event_id"]}
        record.update(lab._snapshot(histories[home_source], "home"))
        record.update(lab._snapshot(histories[away_source], "away"))
        records.append(record)
        prior_counts[target["event_id"]] = min(len(histories[home_source]), len(histories[away_source]))
    frame = lab.add_difference_features(pd.DataFrame(records).set_index("event_id"))
    return frame[list(lab.FEATURE_SETS[FEATURE_VARIANT])], current_sha256, prior_counts


def artifact_residual_logits(features: pd.DataFrame, artifact: Mapping[str, Any]) -> np.ndarray:
    names = list(artifact["features"])
    if list(features.columns) != names:
        raise RuntimeError("feature order mismatch")
    x = features.to_numpy(dtype=float)
    medians = np.asarray(artifact["imputer_medians"], dtype=float)
    missing = np.isnan(x)
    if missing.any():
        x = x.copy()
        x[missing] = np.take(medians, np.where(missing)[1])
    x = (x - np.asarray(artifact["scaler_mean"], dtype=float)) / np.asarray(artifact["scaler_scale"], dtype=float)
    x = np.column_stack([np.ones(len(x)), x])
    pair = x @ np.asarray(artifact["weights"], dtype=float)
    return np.column_stack([pair[:, 0], np.zeros(len(x)), pair[:, 1]])


def validate_targets() -> None:
    if len(TARGETS) != 3:
        raise RuntimeError("prospective cohort must contain exactly three events")
    if len({row["event_id"] for row in TARGETS}) != 3:
        raise RuntimeError("duplicate event_id")
    for row in TARGETS:
        if FORBIDDEN_OUTCOME_KEYS & {str(k).lower() for k in row}:
            raise RuntimeError("outcome field leaked into target manifest")
        p = np.asarray(row["market"], dtype=float)
        if p.shape != (3,) or not np.isfinite(p).all() or (p <= 0).any() or not np.isclose(p.sum(), 1.0, atol=1e-12):
            raise RuntimeError(f"invalid market probabilities for {row['event_id']}")
        kickoff = pd.Timestamp(row["kickoff_utc"])
        market_time = pd.Timestamp(row["market_snapshot_time_utc"])
        if market_time >= kickoff:
            raise RuntimeError("market snapshot must be strictly pre-kickoff")


def run(source_dir: Path, now_utc: pd.Timestamp | None = None) -> dict[str, Any]:
    validate_targets()
    capture_time = now_utc or pd.Timestamp(datetime.now(timezone.utc))
    capture_time = capture_time.tz_convert("UTC") if capture_time.tzinfo is not None else capture_time.tz_localize("UTC")
    if capture_time >= FIRST_KICKOFF:
        raise RuntimeError("prospective freeze closed: first kickoff has already started")

    lab, v1 = load_frozen_modules(source_dir)
    training, historical_hashes, historical_by_code = build_training_frame(lab)
    artifact = fit_artifact(lab, v1, training)
    target_features, current_sha256, prior_counts = build_target_features(lab, historical_by_code)
    market = np.asarray([row["market"] for row in TARGETS], dtype=float)
    residual = artifact_residual_logits(target_features, artifact)
    shadow = v1.market_anchored_probabilities(v1.validate_probabilities(market), residual, SHADOW_LAMBDA)
    active = v1.market_anchored_probabilities(v1.validate_probabilities(market), residual, ACTIVE_LAMBDA)
    if not np.allclose(active, market, atol=1e-15, rtol=0):
        raise RuntimeError("active lambda=0 must equal market exactly")

    predictions = []
    for i, target in enumerate(TARGETS):
        predictions.append({
            "event_id": target["event_id"],
            "home_team": target["home_team"],
            "away_team": target["away_team"],
            "kickoff_utc": target["kickoff_utc"],
            "market_snapshot_time_utc": target["market_snapshot_time_utc"],
            "bookmakers_count": int(target["bookmakers_count"]),
            "market_probabilities": [float(x) for x in market[i]],
            "active_lambda_0_probabilities": [float(x) for x in active[i]],
            "shadow_lambda_1_probabilities": [float(x) for x in shadow[i]],
            "feature_min_prior_matches": int(prior_counts[target["event_id"]]),
        })

    report = {
        "experiment_id": EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "research_only": True,
        "no_bet": True,
        "production_promotion": False,
        "outcomes_available_to_runner": False,
        "source_commit": SOURCE_COMMIT,
        "source_git_blobs": EXPECTED_FROZEN_GIT_BLOBS,
        "league": LEAGUE,
        "cohort_n": 3,
        "capture_time_utc": capture_time.isoformat(),
        "first_kickoff_utc": FIRST_KICKOFF.isoformat(),
        "feature_history_cutoff_utc": FEATURE_HISTORY_CUTOFF.isoformat(),
        "training_data_through_utc": TRAINING_DATA_THROUGH.isoformat(),
        "feature_variant": FEATURE_VARIANT,
        "shadow_lambda": SHADOW_LAMBDA,
        "active_lambda": ACTIVE_LAMBDA,
        "l2_penalty": L2_PENALTY,
        "training_rows": artifact["training_rows"],
        "candidate_artifact_sha256": artifact["artifact_sha256"],
        "football_data_sha256": {**historical_hashes, CURRENT_SEASON_CODE: current_sha256},
        "predictions": predictions,
    }
    report["freeze_sha256"] = _sha256_json(report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frozen-source-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("artifacts/la_liga_market_anchor_prospective_20260915/freeze.json"))
    args = parser.parse_args()
    report = run(args.frozen_source_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
