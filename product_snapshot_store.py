"""Durable product prediction snapshot reader.

Prediction snapshots are immutable model outputs. Bookmaker prices are loaded
independently from ``odds_snapshots`` and joined only by provider ``event_id``.
This keeps model output and market price as separate data sources.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from product_markets import build_product_market_view, fixture_key


PREDICTION_TABLE = "product_prediction_snapshots"
ODDS_TABLE = "odds_snapshots"
PREDICTION_SCHEMA_VERSION = "product-prediction.v1"

# Deliberately contains only fields needed by the public product contract.
# Model artifact hashes/version provenance stay server/service-role only.
PREDICTION_COLUMNS = ",".join(
    [
        "snapshot_schema_version",
        "generated_at_utc",
        "league",
        "event_id",
        "commence_time_utc",
        "match_date",
        "match_time",
        "home_team",
        "away_team",
        "home_team_model",
        "away_team_model",
        "prediction",
        "prediction_strength",
        "model_agreement",
        "home_probability",
        "draw_probability",
        "away_probability",
        "expected_home_goals",
        "expected_away_goals",
        "expected_total_goals",
        "over_2_5_probability",
        "under_2_5_probability",
        "btts_yes_probability",
        "btts_no_probability",
        "top_score",
        "top_score_probability",
    ]
)

ODDS_COLUMNS = ",".join(
    [
        "event_id",
        "snapshot_time_utc",
        "commence_time_utc",
        "home_team",
        "away_team",
        "home_odds",
        "draw_odds",
        "away_odds",
    ]
)


def _parse_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value or "").strip()
        if not text:
            raise ValueError("datetime value is required")
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def prediction_identity(row: Mapping[str, Any]) -> tuple[str, ...]:
    event_id = str(row.get("event_id") or "").strip()
    if event_id:
        return ("event_id", event_id)

    return (
        "fixture",
        str(row.get("league") or "").strip(),
        str(row.get("home_team_model") or "").strip(),
        str(row.get("away_team_model") or "").strip(),
        _parse_datetime(row.get("commence_time_utc")).isoformat(),
    )


def select_latest_prediction_snapshots(
    rows: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Keep the newest immutable model snapshot for each scheduled fixture."""
    latest: dict[tuple[str, ...], dict[str, Any]] = {}

    for raw in rows:
        row = dict(raw)
        if row.get("snapshot_schema_version") != PREDICTION_SCHEMA_VERSION:
            continue

        identity = prediction_identity(row)
        generated_at = _parse_datetime(row.get("generated_at_utc"))
        current = latest.get(identity)
        if current is None or generated_at > _parse_datetime(
            current.get("generated_at_utc")
        ):
            latest[identity] = row

    return sorted(
        latest.values(),
        key=lambda row: _parse_datetime(row.get("commence_time_utc")),
    )


def select_latest_odds_by_event(
    rows: Iterable[Mapping[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Keep the newest stored market snapshot for every event id."""
    latest: dict[str, dict[str, Any]] = {}

    for raw in rows:
        row = dict(raw)
        event_id = str(row.get("event_id") or "").strip()
        if not event_id:
            continue

        snapshot_time = _parse_datetime(row.get("snapshot_time_utc"))
        current = latest.get(event_id)
        if current is None or snapshot_time > _parse_datetime(
            current.get("snapshot_time_utc")
        ):
            latest[event_id] = row

    return latest


def _prediction_for_product(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        key: row.get(key)
        for key in (
            "league",
            "event_id",
            "commence_time_utc",
            "match_date",
            "match_time",
            "home_team",
            "away_team",
            "home_team_model",
            "away_team_model",
            "prediction",
            "prediction_strength",
            "model_agreement",
            "home_probability",
            "draw_probability",
            "away_probability",
            "expected_home_goals",
            "expected_away_goals",
            "expected_total_goals",
            "over_2_5_probability",
            "under_2_5_probability",
            "btts_yes_probability",
            "btts_no_probability",
            "top_score",
            "top_score_probability",
        )
    }


def build_product_view_from_snapshot_rows(
    prediction_rows: Iterable[Mapping[str, Any]],
    odds_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """Join immutable model snapshots to independent market snapshots."""
    latest_predictions = select_latest_prediction_snapshots(prediction_rows)
    latest_odds = select_latest_odds_by_event(odds_rows)

    predictions: list[dict[str, Any]] = []
    odds_by_fixture: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for snapshot in latest_predictions:
        prediction = _prediction_for_product(snapshot)
        predictions.append(prediction)

        event_id = str(snapshot.get("event_id") or "").strip()
        odds = latest_odds.get(event_id) if event_id else None
        if odds is not None:
            odds_by_fixture[fixture_key(prediction)] = {
                "home_odds": odds.get("home_odds"),
                "draw_odds": odds.get("draw_odds"),
                "away_odds": odds.get("away_odds"),
            }

    payload = build_product_market_view(
        predictions,
        odds_by_fixture=odds_by_fixture,
    )
    payload["data_source"] = {
        "predictions": PREDICTION_TABLE,
        "odds": ODDS_TABLE,
        "join": "event_id",
        "prediction_snapshot_count": len(latest_predictions),
        "priced_event_count": sum(
            1
            for row in latest_predictions
            if str(row.get("event_id") or "").strip() in latest_odds
        ),
    }
    return payload


def load_product_market_view(
    supabase_client: Any,
    *,
    now_utc: datetime | None = None,
    horizon_days: int = 14,
) -> dict[str, Any]:
    """Load upcoming model snapshots and matching stored odds from Supabase."""
    now = now_utc or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("now_utc must be timezone-aware")
    now = now.astimezone(timezone.utc)
    horizon = now + timedelta(days=horizon_days)

    prediction_response = (
        supabase_client
        .table(PREDICTION_TABLE)
        .select(PREDICTION_COLUMNS)
        .gte("commence_time_utc", now.isoformat())
        .lt("commence_time_utc", horizon.isoformat())
        .order("generated_at_utc", desc=True)
        .limit(1000)
        .execute()
    )
    prediction_rows = prediction_response.data or []
    latest_predictions = select_latest_prediction_snapshots(prediction_rows)

    event_ids = sorted(
        {
            str(row.get("event_id") or "").strip()
            for row in latest_predictions
            if str(row.get("event_id") or "").strip()
        }
    )

    odds_rows: list[Mapping[str, Any]] = []
    if event_ids:
        odds_response = (
            supabase_client
            .table(ODDS_TABLE)
            .select(ODDS_COLUMNS)
            .in_("event_id", event_ids)
            .gte("commence_time_utc", now.isoformat())
            .lt("commence_time_utc", horizon.isoformat())
            .order("snapshot_time_utc", desc=True)
            .limit(5000)
            .execute()
        )
        odds_rows = odds_response.data or []

    return build_product_view_from_snapshot_rows(
        latest_predictions,
        odds_rows,
    )
