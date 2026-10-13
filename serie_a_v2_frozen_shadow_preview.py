"""Read-only, non-promotable Serie A shadow inference using frozen Sept V2 weights.

Reads the *existing* Supabase odds_snapshots ledger (optionally), never Odds API
or outcome/settlement tables. Requires externally supplied exact pre-kickoff
features, whose authenticity this module cannot independently attest.
Results are ephemeral diagnostics, NEVER prospective-admissible or production.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone, timedelta
import json
import math
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

import market_anchor_1x2_v2_shadow as v2

FROZEN_FILE = Path(__file__).resolve().parent / (
    "research/models/market_anchor_v2_serie_a_frozen_candidate.json"
)
FROZEN_SHA = "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
SCHEMA = "serie-a-market-anchor-v2-shadow-inference.v1"
MAX_QUOTE_AGE = timedelta(hours=24)
FORBIDDEN = frozenset((
    "result", "outcome", "score", "home_goals", "away_goals",
    "final_score", "settlement", "prediction_correct", "match_winner"
))
MARKET_KEYS = (
    "event_id", "league", "home_team", "away_team", "commence_time_utc",
    "snapshot_time_utc", "home_odds", "draw_odds", "away_odds",
)
FEATURE_KEYS = (
    "event_id", "home_team", "away_team", "commence_time_utc",
    "feature_history_cutoff_utc", "features",
)


def parse_utc(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp must be an offset-aware string")
    dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        raise ValueError("naive clock-time not allowed")
    return dt.astimezone(timezone.utc)


def _name(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("fixture/identity requires non-empty strings")
    return value.strip()


def _market(row: Mapping[str, Any]) -> tuple[float, float, float]:
    inv = []
    for key in ("home_odds", "draw_odds", "away_odds"):
        value = row.get(key)
        if isinstance(value, bool) or value is None:
            raise ValueError("missing bookmaker decimal prices")
        number = float(value)
        if not (math.isfinite(number) and number > 1):
            raise ValueError("invalid bookmaker decimal prices")
        inv.append(1 / number)
    total = sum(inv)
    return tuple(x / total for x in inv)


def load_verified_original() -> dict[str, Any]:
    candidate = json.loads(FROZEN_FILE.read_text(encoding="utf-8"))
    v2.validate_candidate_artifact(candidate)
    if (candidate["artifact_sha256"] != FROZEN_SHA
        or candidate["primary_league"] != "SERIE_A"
        or candidate["active_lambda"] != 0.0
        or candidate["stability_gate_passed"] is not False
        or candidate["research_only"] is not True
        or candidate["automatic_promotion"] is not False):
        raise ValueError("frozen V2 research model status or SHA unexpectedly changed")
    return candidate


def _key(row: Mapping[str, Any]) -> tuple[str, str, str, datetime]:
    return (_name(row["event_id"]), _name(row["home_team"]),
            _name(row["away_team"]), parse_utc(row["commence_time_utc"]))


def _guard_outcome_free(row: Mapping[str, Any]):
    if set(row).intersection(FORBIDDEN):
        raise ValueError("outcomes or settlement fields forbidden at capture time")
    features = row.get("features")
    if isinstance(features, Mapping) and set(features).intersection(FORBIDDEN):
        raise ValueError("result fields cannot be provided as model features")


def shadow_preview(
    market_snapshots: Iterable[Mapping[str, Any]],
    feature_snapshots: Iterable[Mapping[str, Any]],
    *,
    as_of_utc: datetime,
) -> dict[str, Any]:
    """Score only fresh future exact identities; never create an AI product forecast.

    'Features' MUST originate from a separate leakage-safe as-of pipeline.
    This module cannot verify that source; it marks every preview NOT eligible
    for the strict preregistered prospective V2 cohort. Do not persist it.
    """
    if as_of_utc.tzinfo is None:
        raise ValueError("as_of_utc must be timezone-aware")
    now = as_of_utc.astimezone(timezone.utc)
    original = load_verified_original()
    feature_keys = tuple(original["features"])
    feature_by_key: dict[tuple[str, str, str, datetime], Mapping[str, Any]] = {}
    for item in feature_snapshots:
        _guard_outcome_free(item)
        if not all(k in item for k in FEATURE_KEYS):
            raise ValueError("feature manifest has missing fields")
        ident = _key(item)
        if ident in feature_by_key:
            raise ValueError("duplicate feature identity")
        feature_by_key[ident] = item

    unique: set[tuple[str, str, str, datetime, datetime]] = set()
    latest: dict[tuple[str, str, str, datetime], tuple[datetime, Mapping[str, Any]]] = {}
    for row in market_snapshots:
        _guard_outcome_free(row)
        if not all(k in row for k in MARKET_KEYS):
            raise ValueError("market observation has missing fields")
        if row["league"] != "SERIE_A":
            raise ValueError("non-Serie-A observations forbidden")
        ident = _key(row)
        if ident[1] == ident[2]:
            raise ValueError("identical home/away team identities")
        snapshot = parse_utc(row["snapshot_time_utc"])
        observation_key = (*ident, snapshot)
        if observation_key in unique:
            raise ValueError("duplicate exact market observation")
        unique.add(observation_key)
        if not snapshot < ident[3]:
            raise ValueError("market quote at or after kickoff")
        old = latest.get(ident)
        if old is None or snapshot > old[0]:
            latest[ident] = (snapshot, row)

    previews = []
    blocked = {"EXPIRED_FIXTURE": 0, "FUTURE_QUOTE": 0, "STALE_MARKET": 0,
               "NO_FEATURES": 0, "INVALID_FEATURE_CUTOFF": 0, "INVALID_MARKET": 0}
    for ident, (snapshot, row) in sorted(latest.items(), key=lambda p: (p[0][3], p[0][0])):
        event_id, home, away, kickoff = ident
        if not now < kickoff:
            blocked["EXPIRED_FIXTURE"] += 1
            continue
        if not snapshot <= now:
            blocked["FUTURE_QUOTE"] += 1
            continue
        if now - snapshot > MAX_QUOTE_AGE:
            blocked["STALE_MARKET"] += 1
            continue
        feature = feature_by_key.get(ident)
        if feature is None:
            blocked["NO_FEATURES"] += 1
            continue
        cutoff = parse_utc(feature["feature_history_cutoff_utc"])
        if not cutoff <= snapshot:
            blocked["INVALID_FEATURE_CUTOFF"] += 1
            continue
        if not isinstance(feature["features"], Mapping) or set(feature["features"]) != set(feature_keys):
            raise ValueError("feature manifest differs from exact 19-feature original")
        vector = []
        for field in feature_keys:
            raw = feature["features"][field]
            if raw is None:
                vector.append(np.nan)  # exact frozen median imputation
                continue
            if isinstance(raw, bool):
                raise ValueError("invalid boolean model feature")
            value = float(raw)
            if not math.isfinite(value):
                raise ValueError("non-finite model feature")
            vector.append(value)
        try:
            market = _market(row)
        except (TypeError, ValueError, OverflowError):
            blocked["INVALID_MARKET"] += 1
            continue
        df = pd.DataFrame([vector], columns=list(feature_keys))
        p = np.array([market], dtype=float)
        active = v2.predict_candidate(p, df, original)[0]
        shadow = v2.predict_shadow_residual(p, df, original)[0]
        if not np.allclose(active, p[0], atol=1e-12, rtol=0):
            raise ValueError("failed frozen lambda=0 market identity invariant")
        if not np.isfinite(shadow).all() or not np.isclose(shadow.sum(), 1.0, atol=1e-12):
            raise ValueError("invalid shadow probabilities")
        previews.append({
            "league": "SERIE_A", "event_id": event_id,
            "home_team": home, "away_team": away,
            "kickoff_utc": kickoff.isoformat(), "market_snapshot_time_utc": snapshot.isoformat(),
            "feature_history_cutoff_utc": cutoff.isoformat(),
            "market_1x2": list(market),
            "active_market_fallback_1x2": active.tolist(),
            "shadow_v2_residual_1x2": shadow.tolist(),
            "model_candidate_sha256": FROZEN_SHA,
            "shadow_evidence_status": "UNVERIFIED_EXTERNAL_FEATURE_PROVENANCE",
            "eligible_for_frozen_prospective_cohort": False,
            "eligible_for_product_publication": False,
            "no_bet": True,
        })
    return {
        "schema_version": SCHEMA,
        "mode": "READ_ONLY_DIAGNOSTIC_NOT_PROSPECTIVE",
        "candidate_sha256": FROZEN_SHA,
        "league": "SERIE_A",
        "as_of_utc": now.isoformat(),
        "market_fallback_is_ai_model": False,
        "stability_gate_passed": False,
        "active_lambda": 0.0,
        "requires_independent_feature_provenance_and_incumbent_for_prospective_capture": True,
        "eligible_for_product_publication": False,
        "paid_provider_calls": 0,
        "database_writes": 0,
        "scored": len(previews),
        "blocked": blocked,
        "previews": previews,
        "no_bet": True,
    }


def fetch_saved_upcoming_serie_a_quotes(client: Any, *, now: datetime) -> list[dict]:
    """Read *existing* observations only. No odds provider call or DB write."""
    items = (
        client.table("odds_snapshots")
        .select(",".join(MARKET_KEYS))
        .eq("league", "SERIE_A")
        .gt("commence_time_utc", now.astimezone(timezone.utc).isoformat())
        .order("snapshot_time_utc", desc=True)
        .limit(1000).execute().data or []
    )
    return list(items)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Pre-match Serie A frozen V2 shadow preview; read-only, no betting or promotion"
    )
    parser.add_argument("--features-json", type=Path, required=True,
                        help="External pre-kickoff feature manifest; cannot grant prospective evidence")
    parser.add_argument("--saved-supabase-quotes", action="store_true", required=True,
                        help="Read existing odds_snapshots only; never calls Odds API")
    args = parser.parse_args()
    from database import supabase
    now = datetime.now(timezone.utc)
    features = json.loads(args.features_json.read_text(encoding="utf-8"))
    if not isinstance(features, list):
        raise ValueError("features-json must contain a list")
    report = shadow_preview(
        fetch_saved_upcoming_serie_a_quotes(supabase, now=now),
        features, as_of_utc=now,
    )
    print(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
