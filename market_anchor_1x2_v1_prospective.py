"""Outcome-blind prospective seed capture for frozen MARKET_ANCHOR_1X2_V1.

This module predicts only the immutable pre-kickoff Serie A seed committed in
experiments/market_anchor_1x2_v1_prospective_seed_input.json.  It does not query
Supabase, read settlement/result tables, tune the frozen V1 construction, or write
production artifacts.  Historical current-season rows are admitted only when their
match date is strictly before the local calendar date of the saved market snapshot;
post-snapshot rows are skipped before outcome/stat fields are inspected.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import requests

from historical_football_signal_lab import FEATURE_SETS, add_difference_features, build_point_in_time_features
from historical_football_signal_runner import BASE, download
from market_anchor_1x2_v1 import (
    L2_PENALTY,
    TRAIN_SEASONS,
    _market,
    _prepare,
    fit_residual_model,
    market_anchored_probabilities,
)
from serie_a_runtime_config import SERIE_A_ALIASES, SERIE_A_RUNTIME_CONFIG

EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1_PROSPECTIVE_SEED"
PARENT_EXPERIMENT_ID = "MARKET_ANCHOR_1X2_V1"
EVIDENCE_CLASS = "PROSPECTIVE_PRE_KICKOFF"
EXPECTED_SEED_N = 10
TARGET_LEAGUE = "SERIE_A"
FROZEN_FEATURE_VARIANT = "ALL_FOOTBALL"
FROZEN_LAMBDA = 1.0
CURRENT_SEASON_CODE = "2627"
CURRENT_SEASON_URL = BASE.format(code=CURRENT_SEASON_CODE, comp="I1")
SOURCE_TO_CANONICAL = {**SERIE_A_ALIASES, "Atalanta": "Atalanta BC"}
PROB_TOL = 1e-12
STATE_QUANTUM_DIGITS = 12


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _utc(value: str) -> pd.Timestamp:
    ts = pd.to_datetime(value, utc=True, errors="coerce")
    if pd.isna(ts):
        raise ValueError(f"invalid UTC timestamp: {value!r}")
    return pd.Timestamp(ts)


def _devig_odds(home: float, draw: float, away: float) -> np.ndarray:
    odds = np.asarray([home, draw, away], dtype=float)
    if not np.isfinite(odds).all() or (odds <= 1.0).any():
        raise ValueError("invalid 1X2 odds in prospective seed")
    inv = 1.0 / odds
    return inv / inv.sum()


def load_and_validate_seed(path: Path) -> dict:
    seed = json.loads(path.read_text(encoding="utf-8"))
    if seed.get("experiment_id") != EXPERIMENT_ID:
        raise ValueError("unexpected prospective experiment_id")
    if seed.get("evidence_class") != EVIDENCE_CLASS:
        raise ValueError("prospective evidence class mismatch")
    if seed.get("membership_frozen") is not True or seed.get("outcome_fields_read") is not False:
        raise ValueError("prospective seed must be frozen and outcome-blind")
    if seed.get("target_league") != TARGET_LEAGUE:
        raise ValueError("prospective seed league mismatch")
    if seed.get("frozen_feature_variant") != FROZEN_FEATURE_VARIANT or float(seed.get("frozen_lambda")) != FROZEN_LAMBDA:
        raise ValueError("prospective seed changed frozen V1 construction")

    freeze = _utc(seed["inventory_freeze_utc"])
    events = list(seed.get("events") or [])
    if len(events) != EXPECTED_SEED_N:
        raise ValueError(f"expected exactly {EXPECTED_SEED_N} seed events")
    ids = [str(event["event_id"]) for event in events]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate prospective event_id")

    for event in events:
        kickoff = _utc(event["kickoff_utc"])
        snapshot = _utc(event["snapshot_time_utc"])
        if not snapshot < freeze < kickoff:
            raise ValueError(f"event {event['event_id']} is not frozen pre-kickoff")
        raw = _devig_odds(float(event["home_odds"]), float(event["draw_odds"]), float(event["away_odds"]))
        saved = np.asarray(
            [event["market_home_prob"], event["market_draw_prob"], event["market_away_prob"]],
            dtype=float,
        )
        if not np.isfinite(saved).all() or not np.allclose(raw, saved, atol=PROB_TOL, rtol=0):
            raise ValueError(f"saved market probabilities mismatch raw odds for {event['event_id']}")
    seed["events"] = sorted(events, key=lambda event: (_utc(event["kickoff_utc"]), str(event["event_id"])))
    return seed


def normalize_source_team(value: str) -> str:
    name = str(value).strip()
    return SOURCE_TO_CANONICAL.get(name, name)


def _parse_date(value: str) -> pd.Timestamp:
    parsed = pd.to_datetime(str(value).strip(), dayfirst=True, errors="coerce")
    if pd.isna(parsed):
        raise ValueError(f"unparseable Football-Data date: {value!r}")
    return pd.Timestamp(parsed).normalize()


def parse_current_season_outcome_blind(content: bytes, *, snapshot_utc: pd.Timestamp) -> pd.DataFrame:
    """Return only current-season rows strictly before the snapshot's Rome date.

    Date/team identity is inspected first. Rows on or after the snapshot calendar date
    are skipped before FTR, goals, corners or card fields are accessed. This is more
    conservative than a same-day kickoff-time reconstruction and prevents any
    post-snapshot result from entering the prospective feature state.
    """
    local_cutoff_date = snapshot_utc.tz_convert("Europe/Rome").date()
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    safe: list[dict[str, Any]] = []
    for row in reader:
        match_date = _parse_date(row.get("Date", ""))
        home = normalize_source_team(row.get("HomeTeam", ""))
        away = normalize_source_team(row.get("AwayTeam", ""))
        if match_date.date() >= local_cutoff_date:
            continue
        # Outcome/stat fields are intentionally touched only after the temporal gate.
        result = str(row.get("FTR", "")).strip()
        if result not in {"H", "D", "A"}:
            raise ValueError(f"unsafe/incomplete finished current-season row: {home} - {away}")
        def number(column: str) -> float:
            value = pd.to_numeric(pd.Series([row.get(column)]), errors="coerce").iloc[0]
            return np.nan if pd.isna(value) else float(value)
        safe.append({
            "Date": match_date.strftime("%d/%m/%Y"),
            "Time": str(row.get("Time", "") or ""),
            "HomeTeam": home,
            "AwayTeam": away,
            "FTHG": number("FTHG"),
            "FTAG": number("FTAG"),
            "FTR": result,
            "HC": number("HC"), "AC": number("AC"),
            "HY": number("HY"), "AY": number("AY"),
            "HR": number("HR"), "AR": number("AR"),
        })
    return pd.DataFrame(safe)


def load_canonical_history(raw_dir: Path, *, current_content: bytes, snapshot_utc: pd.Timestamp) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for code in SERIE_A_RUNTIME_CONFIG.historical_source.season_codes:
        path = raw_dir / f"serie_a_{code}.csv"
        frame = pd.read_csv(path)
        frame["HomeTeam"] = frame["HomeTeam"].map(normalize_source_team)
        frame["AwayTeam"] = frame["AwayTeam"].map(normalize_source_team)
        frames.append(frame)
    current = parse_current_season_outcome_blind(current_content, snapshot_utc=snapshot_utc)
    if not current.empty:
        frames.append(current)
    return pd.concat(frames, ignore_index=True, sort=False)


def build_fixture_feature_row(history: pd.DataFrame, event: dict, features: list[str]) -> tuple[pd.DataFrame, int, int, str]:
    kickoff = _utc(event["kickoff_utc"]).tz_convert("Europe/Rome")
    dummy = {
        "Date": kickoff.strftime("%d/%m/%Y"),
        "Time": kickoff.strftime("%H:%M"),
        "HomeTeam": str(event["home_team"]),
        "AwayTeam": str(event["away_team"]),
        "FTHG": 0.0,
        "FTAG": 0.0,
        "FTR": "D",
        "HC": 0.0, "AC": 0.0,
        "HY": 0.0, "AY": 0.0,
        "HR": 0.0, "AR": 0.0,
    }
    augmented = pd.concat([history, pd.DataFrame([dummy])], ignore_index=True, sort=False)
    point = build_point_in_time_features(augmented, TARGET_LEAGUE, "PROSPECTIVE")
    point = add_difference_features(point)
    match = point[
        point["home_team"].astype(str).eq(str(event["home_team"]))
        & point["away_team"].astype(str).eq(str(event["away_team"]))
        & point["match_date"].eq(kickoff.tz_localize(None).normalize())
    ]
    if len(match) != 1:
        raise RuntimeError(f"failed to isolate prospective feature row for {event['event_id']}: {len(match)}")
    row = match.iloc[0]
    feature_frame = pd.DataFrame([{name: row[name] for name in features}])
    feature_payload = {
        name: (None if pd.isna(row[name]) else round(float(row[name]), STATE_QUANTUM_DIGITS))
        for name in features
    }
    return (
        feature_frame,
        int(row["home_prior_matches"]),
        int(row["away_prior_matches"]),
        canonical_json_sha256(feature_payload),
    )


def quantized_model_state_sha256(model, features: list[str]) -> str:
    def q(values) -> list[float]:
        return [round(float(value), STATE_QUANTUM_DIGITS) for value in np.asarray(values).ravel()]
    payload = {
        "feature_order": list(features),
        "l2_penalty": L2_PENALTY,
        "imputer_statistics": q(model.imputer.statistics_),
        "scaler_mean": q(model.scaler.mean_),
        "scaler_scale": q(model.scaler.scale_),
        "weights": q(model.weights),
        "quantized_decimal_places": STATE_QUANTUM_DIGITS,
    }
    return canonical_json_sha256(payload)


def assert_frozen_selection(report_path: Path) -> None:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    league = next((row for row in report.get("league_reports", []) if row.get("league") == TARGET_LEAGUE), None)
    if league is None:
        raise RuntimeError("frozen OOT report missing Serie A")
    if league.get("selected_feature_variant") != FROZEN_FEATURE_VARIANT or float(league.get("selected_lambda")) != FROZEN_LAMBDA:
        raise RuntimeError("frozen OOT report does not authorize this prospective construction")
    if report.get("residual_accepted") is not True or report.get("active_mode") != "RESIDUAL":
        raise RuntimeError("parent V1 pooled gate was not accepted")


def generate(seed_path: Path, frozen_report_path: Path, work_dir: Path) -> dict:
    assert_frozen_selection(frozen_report_path)
    seed = load_and_validate_seed(seed_path)
    features = list(FEATURE_SETS[FROZEN_FEATURE_VARIANT])

    historical = download(SERIE_A_RUNTIME_CONFIG, TARGET_LEAGUE, work_dir / "raw")
    prepared = _prepare(historical)
    train = prepared[prepared["season"].isin(TRAIN_SEASONS)].copy()
    if len(train) == 0:
        raise RuntimeError("empty frozen training split")
    model = fit_residual_model(
        train[features],
        train["result"].map({"H": 0, "D": 1, "A": 2}).to_numpy(),
        _market(train),
    )
    model_state_sha = quantized_model_state_sha256(model, features)

    snapshots = {_utc(event["snapshot_time_utc"]) for event in seed["events"]}
    if len(snapshots) != 1:
        raise RuntimeError("V1 prospective seed currently requires one exact shared snapshot")
    snapshot = next(iter(snapshots))

    response = requests.get(CURRENT_SEASON_URL, timeout=60)
    response.raise_for_status()
    if len(response.content) < 500:
        raise RuntimeError("suspiciously small current-season Football-Data response")
    history = load_canonical_history(work_dir / "raw", current_content=response.content, snapshot_utc=snapshot)
    current_safe = parse_current_season_outcome_blind(response.content, snapshot_utc=snapshot)

    predictions = []
    labels = np.asarray(["H", "D", "A"])
    for event in seed["events"]:
        feature_frame, home_prior, away_prior, feature_sha = build_fixture_feature_row(history, event, features)
        market = _devig_odds(float(event["home_odds"]), float(event["draw_odds"]), float(event["away_odds"]))
        residual_logits = model.residual_logits(feature_frame)
        candidate = market_anchored_probabilities(market.reshape(1, 3), residual_logits, FROZEN_LAMBDA)[0]
        predictions.append({
            "event_id": str(event["event_id"]),
            "home_team": str(event["home_team"]),
            "away_team": str(event["away_team"]),
            "kickoff_utc": _utc(event["kickoff_utc"]).isoformat().replace("+00:00", "Z"),
            "snapshot_time_utc": _utc(event["snapshot_time_utc"]).isoformat().replace("+00:00", "Z"),
            "market_home_prob": float(market[0]),
            "market_draw_prob": float(market[1]),
            "market_away_prob": float(market[2]),
            "candidate_home_prob": float(candidate[0]),
            "candidate_draw_prob": float(candidate[1]),
            "candidate_away_prob": float(candidate[2]),
            "candidate_minus_market_home": float(candidate[0] - market[0]),
            "candidate_minus_market_draw": float(candidate[1] - market[1]),
            "candidate_minus_market_away": float(candidate[2] - market[2]),
            "market_pick": str(labels[int(market.argmax())]),
            "candidate_pick": str(labels[int(candidate.argmax())]),
            "home_prior_matches": home_prior,
            "away_prior_matches": away_prior,
            "feature_sha256_q12": feature_sha,
        })

    result = {
        "experiment_id": EXPERIMENT_ID,
        "parent_experiment_id": PARENT_EXPERIMENT_ID,
        "evidence_class": EVIDENCE_CLASS,
        "research_only": True,
        "production_promotion": False,
        "bet_decision": "NO_BET",
        "membership_frozen": True,
        "outcome_fields_read": False,
        "inventory_freeze_utc": seed["inventory_freeze_utc"],
        "seed_n": len(predictions),
        "target_league": TARGET_LEAGUE,
        "frozen_feature_variant": FROZEN_FEATURE_VARIANT,
        "frozen_lambda": FROZEN_LAMBDA,
        "train_seasons": list(TRAIN_SEASONS),
        "current_history_rule": "strictly earlier local calendar date than exact saved market snapshot; later rows skipped before outcome/stat access",
        "current_safe_rows_admitted": int(len(current_safe)),
        "model_state_sha256_q12": model_state_sha,
        "feature_order": features,
        "seed_input_sha256": hashlib.sha256(seed_path.read_bytes()).hexdigest(),
        "predictions": predictions,
    }
    if len({row["event_id"] for row in predictions}) != EXPECTED_SEED_N:
        raise RuntimeError("prospective output identity count mismatch")
    if any(any(key in row for key in ("result", "outcome", "score")) for row in predictions):
        raise RuntimeError("outcome-like field leaked into prospective prediction output")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=Path, default=Path("experiments/market_anchor_1x2_v1_prospective_seed_input.json"))
    parser.add_argument("--frozen-report", type=Path, default=Path("experiments/market_anchor_1x2_v1_report.json"))
    parser.add_argument("--work-dir", type=Path, default=Path("artifacts/market_anchor_1x2_v1_prospective/work"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/market_anchor_1x2_v1_prospective/predictions.json"))
    args = parser.parse_args()
    report = generate(args.seed, args.frozen_report, args.work_dir)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
