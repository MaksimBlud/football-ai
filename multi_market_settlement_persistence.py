"""Append-only durable contract for Multi-Market V2 research settlement.

The module is dependency-injected: callers pass a Supabase-like client. It
never imports the project database singleton, applies schema, calls an odds
provider, or calls a results provider.

Identity is fail-closed. A snapshot matches a canonical finished result only
when league, league-local kickoff date, home team and away team are an exact
unique match. No +/- day tolerance and no fuzzy team matching are permitted.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
import math
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from league_config import get_league_config
from multi_market_settlement import settle_multi_market_card


TABLE = "league_multi_market_settlements"
SCHEMA_VERSION = "MULTI_MARKET_SETTLEMENT_V2"
IDENTITY_VERSION = "LEAGUE_LOCAL_DATE_EXACT_TEAMS_V1"
EXISTING_KEY_BATCH_SIZE = 100


class SettlementIdentityError(ValueError):
    """Snapshot/result identity was missing, ambiguous, or inconsistent."""


class SettlementConflictError(RuntimeError):
    """An immutable settlement key already exists with different content."""


def _iso_datetime(value: Any, field: str = "datetime") -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
        except ValueError as exc:
            raise SettlementIdentityError(f"{field} must be an ISO datetime") from exc
    else:
        raise SettlementIdentityError(f"{field} must be an ISO datetime")
    if parsed.tzinfo is None:
        raise SettlementIdentityError(f"{field} must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _date(value: Any, field: str = "match_date") -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError as exc:
            raise SettlementIdentityError(f"{field} must be a date") from exc
    raise SettlementIdentityError(f"{field} must be a date")


def snapshot_local_match_date(snapshot: dict) -> date:
    league = str(snapshot.get("league") or "")
    if not league:
        raise SettlementIdentityError("snapshot league is required")
    config = get_league_config(league)
    kickoff = _iso_datetime(snapshot.get("kickoff_utc"), "kickoff_utc")
    return kickoff.astimezone(ZoneInfo(config.timezone)).date()


def validate_pre_kickoff_snapshot(snapshot: dict) -> None:
    kickoff = _iso_datetime(snapshot.get("kickoff_utc"), "kickoff_utc")
    snapshot_time = _iso_datetime(snapshot.get("snapshot_time_utc"), "snapshot_time_utc")
    if snapshot_time >= kickoff:
        raise SettlementIdentityError("snapshot_time_utc must be strictly before kickoff_utc")


def match_finished_result(snapshot: dict, results: Iterable[dict]) -> dict:
    """Return the one exact canonical finished result for a snapshot."""
    league = str(snapshot.get("league") or "")
    home = str(snapshot.get("home_team") or "")
    away = str(snapshot.get("away_team") or "")
    if not league or not home or not away:
        raise SettlementIdentityError("snapshot league/home_team/away_team are required")
    local_date = snapshot_local_match_date(snapshot)

    matches: list[dict] = []
    for row in results:
        if str(row.get("league") or "") != league:
            continue
        if str(row.get("home_team") or "") != home:
            continue
        if str(row.get("away_team") or "") != away:
            continue
        try:
            row_date = _date(row.get("match_date"))
        except SettlementIdentityError:
            continue
        if row_date == local_date:
            matches.append(dict(row))

    identity = (league, local_date.isoformat(), home, away)
    if not matches:
        raise SettlementIdentityError(f"no exact finished result for {identity!r}")
    if len(matches) != 1:
        raise SettlementIdentityError(f"ambiguous finished results for {identity!r}: {len(matches)}")
    return matches[0]


def validate_corner_outcome_identity(snapshot: dict, corner_outcome: dict) -> None:
    """Require a corner observation to carry its own exact fixture identity."""
    required = {"league", "match_date", "home_team", "away_team", "home_corners", "away_corners"}
    missing = required - set(corner_outcome)
    if missing:
        raise SettlementIdentityError(
            "corner outcome missing identity/outcome fields: " + ", ".join(sorted(missing))
        )

    expected_date = snapshot_local_match_date(snapshot)
    observed_date = _date(corner_outcome.get("match_date"), "corner match_date")
    comparisons = {
        "league": (str(snapshot.get("league") or ""), str(corner_outcome.get("league") or "")),
        "home_team": (str(snapshot.get("home_team") or ""), str(corner_outcome.get("home_team") or "")),
        "away_team": (str(snapshot.get("away_team") or ""), str(corner_outcome.get("away_team") or "")),
    }
    mismatches = [field for field, (expected, observed) in comparisons.items() if expected != observed]
    if observed_date != expected_date:
        mismatches.append("match_date")
    if "event_id" in corner_outcome and str(corner_outcome.get("event_id")) != str(snapshot.get("event_id")):
        mismatches.append("event_id")
    if mismatches:
        raise SettlementIdentityError("corner outcome identity mismatch: " + ", ".join(sorted(set(mismatches))))


def _finite_nonnegative_int(value: Any, field: str) -> int:
    if value is None or isinstance(value, bool):
        raise ValueError(f"{field} must be a non-negative integer")
    try:
        numeric = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative integer") from exc
    if not math.isfinite(numeric) or numeric < 0 or not numeric.is_integer():
        raise ValueError(f"{field} must be a non-negative integer")
    return int(numeric)


def build_outcome(snapshot: dict, result: dict, corner_outcome: dict | None = None) -> dict:
    outcome = {
        "home_goals": _finite_nonnegative_int(result.get("home_goals"), "home_goals"),
        "away_goals": _finite_nonnegative_int(result.get("away_goals"), "away_goals"),
    }
    if corner_outcome is not None:
        validate_corner_outcome_identity(snapshot, corner_outcome)
        outcome["home_corners"] = _finite_nonnegative_int(corner_outcome.get("home_corners"), "home_corners")
        outcome["away_corners"] = _finite_nonnegative_int(corner_outcome.get("away_corners"), "away_corners")
    return outcome


def outcome_completeness(outcome: dict) -> str:
    has_goals = outcome.get("home_goals") is not None and outcome.get("away_goals") is not None
    has_corners = outcome.get("home_corners") is not None and outcome.get("away_corners") is not None
    if not has_goals:
        return "INCOMPLETE"
    return "GOALS_AND_CORNERS" if has_corners else "GOALS_ONLY"


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def outcome_fingerprint(outcome: dict) -> str:
    return hashlib.sha256(_canonical_json(outcome).encode("utf-8")).hexdigest()


def settlement_key(snapshot_key: str, fingerprint: str) -> str:
    material = f"{snapshot_key}|{fingerprint}|{SCHEMA_VERSION}"
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _extract_card(snapshot: dict) -> dict:
    payload = snapshot.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("snapshot payload must be an object")
    if payload.get("schema_version") != "MULTI_MARKET_V1" or payload.get("research_only") is not True:
        raise ValueError("snapshot payload is not a research-only MULTI_MARKET_V1 payload")
    card = payload.get("card")
    if not isinstance(card, dict):
        raise ValueError("snapshot payload.card must be an object")
    return card


def build_settlement_record(
    snapshot: dict,
    result: dict,
    *,
    corner_outcome: dict | None = None,
) -> dict:
    """Build one immutable settlement revision for one immutable snapshot.

    A later exact corner observation creates a second revision because the
    outcome fingerprint changes. The earlier GOALS_ONLY row remains immutable.
    """
    validate_pre_kickoff_snapshot(snapshot)
    matched = match_finished_result(snapshot, [result])
    outcome = build_outcome(snapshot, matched, corner_outcome)
    completeness = outcome_completeness(outcome)
    if completeness == "INCOMPLETE":
        raise ValueError("goals are required before settlement")

    card = _extract_card(snapshot)
    settlement = settle_multi_market_card(card, outcome)
    fingerprint = outcome_fingerprint(outcome)
    snapshot_key_value = str(snapshot.get("snapshot_key") or "")
    if not snapshot_key_value:
        raise ValueError("snapshot_key is required")

    local_date = snapshot_local_match_date(snapshot)
    result_season = str(matched.get("season") or "")
    if not result_season:
        raise ValueError("matched result season is required")

    kickoff = _iso_datetime(snapshot["kickoff_utc"], "kickoff_utc")
    snapshot_time = _iso_datetime(snapshot["snapshot_time_utc"], "snapshot_time_utc")
    payload = {
        "schema_version": SCHEMA_VERSION,
        "research_only": True,
        "identity_version": IDENTITY_VERSION,
        "outcome": outcome,
        "outcome_completeness": completeness,
        "settlement": settlement,
    }
    return {
        "settlement_key": settlement_key(snapshot_key_value, fingerprint),
        "snapshot_key": snapshot_key_value,
        "league": str(snapshot["league"]),
        "event_id": str(snapshot["event_id"]),
        "home_team": str(snapshot["home_team"]),
        "away_team": str(snapshot["away_team"]),
        "kickoff_utc": kickoff.isoformat(),
        "snapshot_time_utc": snapshot_time.isoformat(),
        "result_season": result_season,
        "result_match_date": local_date.isoformat(),
        "outcome_fingerprint": fingerprint,
        "outcome_completeness": completeness,
        "payload": payload,
    }


def _response_rows(response: Any) -> list[dict]:
    return list(getattr(response, "data", None) or [])


def _immutable_equal(left: dict, right: dict) -> bool:
    return _canonical_json(left) == _canonical_json(right)


def _load_existing_by_keys(client, keys: list[str]) -> dict[str, dict]:
    """Read existing immutable revisions in bounded unique-key batches.

    Chunking avoids both a large PostgREST `in` URL and silent row-cap risk
    during future backfills. settlement_key is unique, so each bounded chunk
    can return at most EXISTING_KEY_BATCH_SIZE rows and needs no range paging.
    """
    existing: dict[str, dict] = {}
    for start in range(0, len(keys), EXISTING_KEY_BATCH_SIZE):
        batch = keys[start:start + EXISTING_KEY_BATCH_SIZE]
        response = client.table(TABLE).select("*").in_("settlement_key", batch).execute()
        for row in _response_rows(response):
            existing[str(row["settlement_key"])] = dict(row)
    return existing


def persist_settlement_records(client, records: Iterable[dict]) -> dict:
    """Insert immutable settlement revisions idempotently."""
    records = [dict(row) for row in records]
    if not records:
        return {"inserted": 0, "unchanged": 0, "conflicts": 0}

    keys = [str(row.get("settlement_key") or "") for row in records]
    if any(not key for key in keys):
        raise ValueError("settlement_key is required")
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate settlement_key in incoming batch")

    existing = _load_existing_by_keys(client, keys)
    inserted = 0
    unchanged = 0

    for record in records:
        key = str(record["settlement_key"])
        previous = existing.get(key)
        if previous is not None:
            comparable = {field: previous.get(field) for field in record}
            if not _immutable_equal(comparable, record):
                raise SettlementConflictError(f"immutable settlement conflict for {key}")
            unchanged += 1
            continue
        client.table(TABLE).insert(record).execute()
        existing[key] = record
        inserted += 1

    return {"inserted": inserted, "unchanged": unchanged, "conflicts": 0}
