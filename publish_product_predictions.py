"""Publish already-generated Football AI predictions to durable Supabase storage.

This script does not train models and does not call The Odds API. Its default mode
is validation/dry-run. Live insertion requires explicit ``--publish``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping
from zoneinfo import ZoneInfo

from product_snapshot_store import PREDICTION_SCHEMA_VERSION, PREDICTION_TABLE
from team_names import normalize_team_name


PUBLISHER_VERSION = "product-publisher.v1"
DEFAULT_PREDICTIONS = Path("data/upcoming_round_predictions.csv")
DEFAULT_FIXTURES = Path("data/upcoming_matches.csv")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _text(value: Any) -> str:
    return str(value or "").strip()


def _float(value: Any, *, required: bool = False) -> float | None:
    text = _text(value)
    if not text:
        if required:
            raise ValueError("required numeric value is missing")
        return None
    parsed = float(text)
    if not math.isfinite(parsed):
        raise ValueError("numeric value must be finite")
    return parsed


def _bool(value: Any) -> bool | None:
    text = _text(value).lower()
    if not text:
        return None
    if text in {"true", "1", "yes"}:
        return True
    if text in {"false", "0", "no"}:
        return False
    raise ValueError(f"invalid boolean value: {value!r}")


def _iso_utc(value: Any) -> str:
    text = _text(value)
    if not text:
        raise ValueError("kickoff timestamp is required")
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        raise ValueError("kickoff timestamp must include timezone")
    return parsed.astimezone(timezone.utc).isoformat()


def fixture_kickoff_utc(row: Mapping[str, Any]) -> str:
    explicit_utc = _text(row.get("commence_time_utc"))
    if explicit_utc:
        return _iso_utc(explicit_utc)

    uk_value = _text(row.get("match_datetime_uk"))
    if not uk_value:
        raise ValueError(
            "fixture requires commence_time_utc or match_datetime_uk"
        )

    parsed = datetime.fromisoformat(uk_value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=ZoneInfo("Europe/London"))
    return parsed.astimezone(timezone.utc).isoformat()


def _fixture_key(row: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (
        _text(row.get("home_team_model") or row.get("home_team")),
        _text(row.get("away_team_model") or row.get("away_team")),
        _text(row.get("match_date")),
        _text(row.get("match_time")),
    )


def _sha256(path: Path | None) -> str | None:
    if path is None:
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_snapshot_rows(
    prediction_rows: Iterable[Mapping[str, Any]],
    fixture_rows: Iterable[Mapping[str, Any]],
    *,
    league: str,
    run_id: str,
    generated_at_utc: str,
    model_1x2_version: str | None = None,
    model_1x2_sha256: str | None = None,
    model_goals_version: str | None = None,
    model_goals_sha256: str | None = None,
) -> list[dict[str, Any]]:
    fixtures = {_fixture_key(row): dict(row) for row in fixture_rows}
    output: list[dict[str, Any]] = []

    for raw_prediction in prediction_rows:
        prediction = dict(raw_prediction)
        key = _fixture_key(prediction)
        fixture = fixtures.get(key)
        if fixture is None:
            raise ValueError(
                "prediction has no exact fixture row: " + " | ".join(key)
            )

        output.append(
            {
                "snapshot_schema_version": PREDICTION_SCHEMA_VERSION,
                "run_id": run_id,
                "generated_at_utc": _iso_utc(generated_at_utc),
                "league": _text(fixture.get("league")) or league,
                "event_id": _text(fixture.get("event_id")) or None,
                "commence_time_utc": fixture_kickoff_utc(fixture),
                "match_date": _text(prediction.get("match_date")),
                "match_time": _text(prediction.get("match_time")),
                "home_team": _text(prediction.get("home_team")),
                "away_team": _text(prediction.get("away_team")),
                "home_team_model": _text(prediction.get("home_team_model")),
                "away_team_model": _text(prediction.get("away_team_model")),
                "prediction": _text(prediction.get("prediction")) or None,
                "prediction_strength": _text(
                    prediction.get("prediction_strength")
                )
                or None,
                "model_agreement": _bool(prediction.get("model_agreement")),
                "home_probability": _float(
                    prediction.get("home_probability"), required=True
                ),
                "draw_probability": _float(
                    prediction.get("draw_probability"), required=True
                ),
                "away_probability": _float(
                    prediction.get("away_probability"), required=True
                ),
                "expected_home_goals": _float(
                    prediction.get("expected_home_goals")
                ),
                "expected_away_goals": _float(
                    prediction.get("expected_away_goals")
                ),
                "expected_total_goals": _float(
                    prediction.get("expected_total_goals")
                ),
                "over_2_5_probability": _float(
                    prediction.get("over_2_5_probability")
                ),
                "under_2_5_probability": _float(
                    prediction.get("under_2_5_probability")
                ),
                "btts_yes_probability": _float(
                    prediction.get("btts_yes_probability")
                ),
                "btts_no_probability": _float(
                    prediction.get("btts_no_probability")
                ),
                "top_score": _text(prediction.get("top_score")) or None,
                "top_score_probability": _float(
                    prediction.get("top_score_probability")
                ),
                "model_1x2_version": model_1x2_version,
                "model_1x2_sha256": model_1x2_sha256,
                "model_goals_version": model_goals_version,
                "model_goals_sha256": model_goals_sha256,
                "publisher_version": PUBLISHER_VERSION,
            }
        )

    return output


def _same_fixture(
    prediction: Mapping[str, Any],
    odds: Mapping[str, Any],
) -> bool:
    if _text(prediction.get("league")) != _text(odds.get("league")):
        return False
    home = normalize_team_name(_text(odds.get("home_team")))
    away = normalize_team_name(_text(odds.get("away_team")))
    if home != _text(prediction.get("home_team_model")):
        return False
    if away != _text(prediction.get("away_team_model")):
        return False
    kickoff_a = datetime.fromisoformat(
        _text(prediction.get("commence_time_utc"))
    )
    kickoff_b = datetime.fromisoformat(
        _text(odds.get("commence_time_utc")).replace("Z", "+00:00")
    )
    return abs((kickoff_a - kickoff_b).total_seconds()) <= 300


def resolve_event_ids(
    rows: list[dict[str, Any]],
    odds_rows: Iterable[Mapping[str, Any]],
) -> int:
    """Fill missing provider event ids from already-stored odds snapshots only."""
    odds = list(odds_rows)
    resolved = 0
    for row in rows:
        if row.get("event_id"):
            continue
        matches = [candidate for candidate in odds if _same_fixture(row, candidate)]
        event_ids = {_text(candidate.get("event_id")) for candidate in matches}
        event_ids.discard("")
        if len(event_ids) == 1:
            row["event_id"] = next(iter(event_ids))
            resolved += 1
    return resolved


def _load_stored_odds(supabase_client: Any) -> list[dict[str, Any]]:
    response = (
        supabase_client
        .table("odds_snapshots")
        .select("league,event_id,commence_time_utc,home_team,away_team")
        .order("snapshot_time_utc", desc=True)
        .limit(5000)
        .execute()
    )
    return response.data or []


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_PREDICTIONS)
    parser.add_argument("--fixtures", type=Path, default=DEFAULT_FIXTURES)
    parser.add_argument("--league", default="EPL")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--generated-at-utc", default=None)
    parser.add_argument("--model-1x2-version", default=None)
    parser.add_argument("--model-goals-version", default=None)
    parser.add_argument("--model-1x2-artifact", type=Path, default=None)
    parser.add_argument("--model-goals-artifact", type=Path, default=None)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Insert validated rows into live Supabase. Without this flag: dry-run.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_at = args.generated_at_utc or datetime.now(timezone.utc).isoformat()
    run_id = args.run_id or str(uuid.uuid4())

    rows = build_snapshot_rows(
        _read_csv(args.input),
        _read_csv(args.fixtures),
        league=args.league,
        run_id=run_id,
        generated_at_utc=generated_at,
        model_1x2_version=args.model_1x2_version,
        model_1x2_sha256=_sha256(args.model_1x2_artifact),
        model_goals_version=args.model_goals_version,
        model_goals_sha256=_sha256(args.model_goals_artifact),
    )

    if args.publish:
        from database import supabase

        resolved = resolve_event_ids(rows, _load_stored_odds(supabase))
        response = supabase.table(PREDICTION_TABLE).insert(rows).execute()
        inserted = len(response.data or [])
        if inserted != len(rows):
            raise RuntimeError(
                f"expected {len(rows)} inserted rows, received {inserted}"
            )
        print(
            f"Published {inserted} immutable prediction snapshots; "
            f"event ids resolved from stored odds: {resolved}."
        )
    else:
        with_event = sum(1 for row in rows if row.get("event_id"))
        print(
            f"DRY RUN: validated {len(rows)} prediction snapshots; "
            f"fixture-provided event ids: {with_event}."
        )
        print("Nothing was written. Use --publish for explicit insertion.")


if __name__ == "__main__":
    main()
