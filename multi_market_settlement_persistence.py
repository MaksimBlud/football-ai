"""Append-only durable contract for Multi-Market V2 research settlement.

The module is deliberately dependency-injected: callers pass a Supabase-like
client. It never imports the project database singleton, never applies schema,
and never calls an odds/results provider.

Identity is fail-closed. A bookmaker snapshot can match a canonical finished
result only when league, league-local kickoff date, home team and away team are
an exact unique match. No +/- day tolerance or fuzzy team matching is allowed.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
import hashlib
import json
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from league_config import get_league_config
from multi_market_settlement import settle_multi_market_card


TABLE = "league_multi_market_settlements"
SCHEMA_VERSION = "MULTI_MARKET_SETTLEMENT_V2"
IDENTITY_VERSION = "LEAGUE_LOCAL_DATE_EXACT_TEAMS_V1"


class SettlementIdentityError(ValueError):
    """Raised when snapshot/result identity cannot be resolved uniquely."""


class SettlementConflictError(RuntimeError):
    """Raised when an existing immutable settlement key has different data."""


def _iso_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    else:
        raise SettlementIdentityError("kickoff_utc must be an ISO datetime")
    if parsed.tzinfo is None:
        raise SettlementIdentityError("kickoff_utc must be timezone-aware")
    return parsed.astimezone(timezone.utc)


def _date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value[:10])
    raise SettlementIdentityError("match_date must be a date")


def snapshot_local_match_date(snapshot: dict) -> date:
    league = str(snapshot.get("league") or "")
    config = get_league_config(league)
    kickoff = _iso_datetime(snapshot.get("kickoff_utc"))
    return kickoff.astimezone(ZoneInfo(config.timezone)).date()


def match_finished_result(snapshot: dict, results: Iterable[dict]) -> dict:
    """Return the one exact canonical finished result for a snapshot.

    Required equality:
      league
      league-local date derived from kickoff_utc
      home_team
      away_team
    """
    league = str(snapshot.get("league") or "")
    home = str(snapshot.get("home_team") or "")
    away = str(snapshot.get("away_team") or "")
    if not league or not home or not away:
        raise SettlementIdentityError("snapshot league/home_team/away_team are required")
    local_date = snapshot_local_match_date(snapshot)

    matches = []
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

    if not matches:
        raise SettlementIdentityError(
            f"no exact finished result for {(league, local_date.isoformat(), home, away)!r}"
        )
    if len(matches) != 1:
        raise SettlementIdentityError(
            f"ambiguous finished results for {(league, local_date.isoformat(), home, away)!r}: {len(matches)}"
        )
    return matches[0]


def _finite_nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a non-negative integer")
    try:
        number = int(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be a non-negative integer") from exc
    if number < 0 or str(number) != str(value).strip() and not isinstance(value, int):
        # Accept numeric strings such as "2"; reject lossy values such as 2.5.
        try:
            if float(value) != float(number):
                raise ValueError(f"{field} must be a non-negative integer")
        except (TypeError, ValueError):
            raise ValueError(f"{field} must be a non-negative integer")
    return number


def build_outcome(result: dict, corner_outcome: dict | None = None) -> dict:
    outcome = {
        "home_goals": _finite_nonnegative_int(result.get("home_goals"), "home_goals"),
        "away_goals": _finite_nonnegative_int(result.get("away_goals"), "away_goals"),
    }
    if corner_outcome is not None:
        home_corners = corner_outcome.get("home_corners")
        away_corners = corner_outcome.get("away_corners")
        if (home_corners is None) != (away_corners is None):
            raise ValueError("corner outcome must provide both home_corners and away_corners")
        if home_corners is not None:
            outcome["home_corners"] = _finite_nonnegative_int(home_corners, "home_corners")
            outcome["away_corners"] = _finite_nonnegative_int(away_corners, "away_corners")
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
    """Build one immutable settlement revision.

    A later corner result intentionally creates a second revision because the
    outcome fingerprint changes. Existing GOALS_ONLY rows are never updated.
    """
    matched = match_finished_result(snapshot, [result])
    outcome = build_outcome(matched, corner_outcome)
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
        "kickoff_utc": _iso_datetime(snapshot["kickoff_utc"]).isoformat(),
        "snapshot_time_utc": _iso_datetime(snapshot["snapshot_time_utc"]).isoformat(),
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


def persist_settlement_records(client, records: Iterable[dict]) -> dict:
    """Insert immutable settlement revisions idempotently.

    Existing rows with the same settlement_key must be byte-semantically equal
    on all supplied immutable fields. Different outcome fingerprints naturally
    use different keys and therefore append a new revision.
    """
    records = [dict(row) for row in records]
    if not records:
        return {"inserted": 0, "unchanged": 0, "conflicts": 0}

    keys = [str(row.get("settlement_key") or "") for row in records]
    if any(not key for key in keys):
        raise ValueError("settlement_key is required")
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate settlement_key in incoming batch")

    response = client.table(TABLE).select("*").in_("settlement_key", keys).execute()
    existing = {str(row["settlement_key"]): dict(row) for row in _response_rows(response)}
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
