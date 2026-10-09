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
        # An at/after-kickoff model result cannot be shown as a pre-match forecast.
        if generated_at >= _parse_datetime(row.get("commence_time_utc")):
            continue
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


def _market_matches_prediction(
    odds: Mapping[str, Any], prediction: Mapping[str, Any],
) -> bool:
    """Fail closed unless the quote belongs to the exact pre-match fixture."""
    event_id = str(prediction.get("event_id") or "").strip()
    if not event_id or event_id != str(odds.get("event_id") or "").strip():
        return False
    try:
        kickoff = _parse_datetime(prediction.get("commence_time_utc"))
        if _parse_datetime(odds.get("commence_time_utc")) != kickoff:
            return False
        if _parse_datetime(odds.get("snapshot_time_utc")) >= kickoff:
            return False
    except (ValueError, TypeError, OverflowError):
        return False
    for side in ("home_team", "away_team"):
        expected = " ".join(str(prediction.get(side) or "").split()).casefold()
        actual = " ".join(str(odds.get(side) or "").split()).casefold()
        if not expected or actual != expected:
            return False
    return True


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
    prediction_by_event = {
        str(row["event_id"]).strip(): row
        for row in latest_predictions
        if str(row.get("event_id") or "").strip()
    }
    # Filter before latest-selection. A newer invalid quote must not mask
    # an older, still-valid pre-kickoff quote for the same provider event.
    eligible_odds = [
        row for row in odds_rows
        if _market_matches_prediction(
            row, prediction_by_event.get(str(row.get("event_id") or "").strip(), {})
        )
    ]
    latest_odds = select_latest_odds_by_event(eligible_odds)

    # The product adapter still indexes prices by legacy fixture_key.
    # Ambiguous keys must remain unpriced, even when event IDs differ.
    fixture_counts: dict[tuple[str, str, str, str], int] = {}
    for snapshot in latest_predictions:
        key = fixture_key(snapshot)
        fixture_counts[key] = fixture_counts.get(key, 0) + 1
    ambiguous_fixtures = {key for key, count in fixture_counts.items() if count > 1}

    predictions: list[dict[str, Any]] = []
    odds_by_fixture: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for snapshot in latest_predictions:
        prediction = _prediction_for_product(snapshot)
        predictions.append(prediction)

        event_id = str(snapshot.get("event_id") or "").strip()
        odds = latest_odds.get(event_id) if event_id else None
        if odds is not None and fixture_key(prediction) not in ambiguous_fixtures:
            odds_by_fixture[fixture_key(prediction)] = {
                "home_odds": odds.get("home_odds"),
                "draw_odds": odds.get("draw_odds"),
                "away_odds": odds.get("away_odds"),
            }

    payload = build_product_market_view(
        predictions,
        odds_by_fixture=odds_by_fixture,
    )
    # Verify adapter order and identity before attaching source provenance.
    for item, snapshot in zip(payload["matches"], latest_predictions, strict=True):
        metadata = item["match"]
        if (
            metadata.get("event_id") != snapshot.get("event_id")
            or metadata.get("commence_time_utc") != snapshot.get("commence_time_utc")
        ):
            raise ValueError("Product fixture provenance alignment failed")
        event_id = str(snapshot.get("event_id") or "").strip()
        ambiguous = fixture_key(snapshot) in ambiguous_fixtures
        quote = latest_odds.get(event_id) if event_id and not ambiguous else None
        metadata["prediction_generated_at_utc"] = _parse_datetime(
            snapshot.get("generated_at_utc")
        ).isoformat()
        metadata["market_snapshot_time_utc"] = (
            _parse_datetime(quote.get("snapshot_time_utc")).isoformat()
            if quote is not None else None
        )
        metadata["market_snapshot_status"] = (
            "ambiguous_fixture" if ambiguous
            else "verified_prekickoff" if quote is not None
            else "no_verified_prekickoff_quote"
        )

    payload["data_source"] = {
        "predictions": PREDICTION_TABLE,
        "odds": ODDS_TABLE,
        "join": "event_id",
        "prediction_snapshot_count": len(latest_predictions),
        "priced_event_count": sum(
            1
            for row in latest_predictions
            if (
                str(row.get("event_id") or "").strip() in latest_odds
                and fixture_key(row) not in ambiguous_fixtures
            )
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
