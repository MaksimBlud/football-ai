"""Bootstrap durable product prediction snapshots from the EPL AI/market ledger.

This is a one-way, append-only bridge for already-produced model output. It does
not run inference, train, promote a model, or call The Odds API.

Dry-run is the default. Live insertion requires explicit ``--publish``.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

PAIR_TABLE = "epl_ai_market_pair_ledger"
PRODUCT_TABLE = "product_prediction_snapshots"
PUBLISHER_VERSION = "product-publisher.pair-ledger-bootstrap.v1"
SCHEMA_VERSION = "product-prediction.v1"
LONDON = ZoneInfo("Europe/London")

PAIR_COLUMNS = ",".join(
    [
        "experiment_id",
        "league",
        "event_id",
        "provider_home_team",
        "provider_away_team",
        "model_home_team",
        "model_away_team",
        "kickoff_utc",
        "model_generated_at_utc",
        "model_home_prob",
        "model_draw_prob",
        "model_away_prob",
        "model_artifact_sha256",
        "code_commit_sha",
    ]
)


def _parse_datetime(value: Any) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def select_latest_pair_rows(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Keep newest model generation per provider event id."""
    latest: dict[str, dict[str, Any]] = {}
    for raw in rows:
        row = dict(raw)
        event_id = str(row.get("event_id") or "").strip()
        if not event_id:
            continue
        generated_at = _parse_datetime(row.get("model_generated_at_utc"))
        current = latest.get(event_id)
        if current is None or generated_at > _parse_datetime(
            current.get("model_generated_at_utc")
        ):
            latest[event_id] = row
    return sorted(latest.values(), key=lambda r: _parse_datetime(r["kickoff_utc"]))


def prediction_code(row: Mapping[str, Any]) -> str:
    candidates = {
        "HOME": float(row["model_home_prob"]),
        "DRAW": float(row["model_draw_prob"]),
        "AWAY": float(row["model_away_prob"]),
    }
    return max(candidates, key=candidates.get)


def snapshot_from_pair_row(
    row: Mapping[str, Any],
    *,
    run_id: str,
) -> dict[str, Any]:
    """Convert one durable pair-ledger model row into product-prediction.v1."""
    kickoff = _parse_datetime(row["kickoff_utc"])
    generated_at = _parse_datetime(row["model_generated_at_utc"])
    local_kickoff = kickoff.astimezone(LONDON)

    probabilities = [
        float(row["model_home_prob"]),
        float(row["model_draw_prob"]),
        float(row["model_away_prob"]),
    ]
    if any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("model probability outside [0, 1]")
    if abs(sum(probabilities) - 1.0) > 1e-6:
        raise ValueError("1X2 probabilities must sum to 1")

    return {
        "snapshot_schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generated_at_utc": generated_at.isoformat(),
        "league": str(row.get("league") or "EPL"),
        "event_id": str(row["event_id"]),
        "commence_time_utc": kickoff.isoformat(),
        "match_date": local_kickoff.date().isoformat(),
        "match_time": local_kickoff.strftime("%H:%M"),
        "home_team": str(row["provider_home_team"]),
        "away_team": str(row["provider_away_team"]),
        "home_team_model": str(row["model_home_team"]),
        "away_team_model": str(row["model_away_team"]),
        "prediction": prediction_code(row),
        "prediction_strength": None,
        "model_agreement": None,
        "home_probability": probabilities[0],
        "draw_probability": probabilities[1],
        "away_probability": probabilities[2],
        "expected_home_goals": None,
        "expected_away_goals": None,
        "expected_total_goals": None,
        "over_2_5_probability": None,
        "under_2_5_probability": None,
        "btts_yes_probability": None,
        "btts_no_probability": None,
        "top_score": None,
        "top_score_probability": None,
        "model_1x2_version": str(row.get("experiment_id") or "EPL_AI_MARKET_PAIR_V1"),
        "model_1x2_sha256": str(row["model_artifact_sha256"]),
        "model_goals_version": None,
        "model_goals_sha256": None,
        "publisher_version": PUBLISHER_VERSION,
    }


def build_bootstrap_rows(
    pair_rows: Iterable[Mapping[str, Any]],
) -> tuple[str | None, list[dict[str, Any]]]:
    latest = select_latest_pair_rows(pair_rows)
    if not latest:
        return None, []
    generation = max(_parse_datetime(r["model_generated_at_utc"]) for r in latest)
    run_id = f"pair-ledger-bootstrap:{generation.strftime('%Y%m%dT%H%M%SZ')}"
    return run_id, [snapshot_from_pair_row(row, run_id=run_id) for row in latest]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--horizon-days", type=int, default=14)
    args = parser.parse_args()
    if args.horizon_days < 1 or args.horizon_days > 30:
        raise SystemExit("--horizon-days must be between 1 and 30")

    from database import supabase

    now = datetime.now(timezone.utc)
    horizon = now + timedelta(days=args.horizon_days)
    response = (
        supabase.table(PAIR_TABLE)
        .select(PAIR_COLUMNS)
        .gte("kickoff_utc", now.isoformat())
        .lt("kickoff_utc", horizon.isoformat())
        .order("model_generated_at_utc", desc=True)
        .limit(1000)
        .execute()
    )
    run_id, rows = build_bootstrap_rows(response.data or [])
    print(f"run_id={run_id} rows={len(rows)} publish={args.publish}")
    if not args.publish or not rows:
        return

    existing = (
        supabase.table(PRODUCT_TABLE)
        .select("event_id")
        .eq("run_id", run_id)
        .execute()
    )
    existing_ids = {str(row["event_id"]) for row in (existing.data or [])}
    insert_rows = [row for row in rows if row["event_id"] not in existing_ids]
    if insert_rows:
        supabase.table(PRODUCT_TABLE).insert(insert_rows).execute()

    verify = (
        supabase.table(PRODUCT_TABLE)
        .select("event_id")
        .eq("run_id", run_id)
        .execute()
    )
    persisted = {str(row["event_id"]) for row in (verify.data or [])}
    expected = {str(row["event_id"]) for row in rows}
    if persisted != expected:
        raise RuntimeError("bootstrap verification failed")
    print(f"verified={len(persisted)}")


if __name__ == "__main__":
    main()
