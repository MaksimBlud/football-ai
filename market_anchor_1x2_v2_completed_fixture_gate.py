"""Read-only builder for the frozen V2 completed-fixture identity attestation.

This adapter queries only match_date/home_team/away_team. It never selects or
returns target outcomes. The pure prospective evaluator remains database-free;
callers can pass this result to it after collecting eligible forecast records.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Mapping

from market_anchor_1x2_v2_prospective_evaluator import (
    COMPLETED_FIXTURE_GATE_COLUMNS,
    COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
    COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
    COMPLETED_FIXTURE_GATE_SCHEMA,
    COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
    PRIMARY_LEAGUE,
    PRIMARY_SEASON_END,
    PRIMARY_SEASON_START,
    _sha_fixture_set,
)
from serie_a_v2_current_form_source_capture import _canonical_team

PAGE_SIZE = 1000
MAX_ROWS = 10000


def _capture_utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("completed-fixture metadata clock must have a real UTC offset")
    return value.astimezone(timezone.utc)


def _match_date(value: Any) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        try:
            parsed = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("completed-fixture metadata date must be canonical YYYY-MM-DD") from exc
        if parsed.isoformat() != value:
            raise ValueError("completed-fixture metadata date must be canonical YYYY-MM-DD")
        return parsed
    raise ValueError("completed-fixture metadata row lacks a valid match_date")


def read_completed_fixture_gate(
    client: Any, *, captured_at: datetime
) -> tuple[set[tuple[str, str, str]], dict[str, Any]]:
    """Query identity-only metadata and construct the evaluator's exact attestation.

    The attestation is computed from the actual rows returned by this query,
    rather than accepted from a caller-provided count or digest. Exact row-key
    validation also fails closed if a mocked, proxy, or changed response adds a
    result/score field despite the frozen select list.
    """
    captured = _capture_utc(captured_at)
    cutoff = captured.date()
    query = (
        client.table("league_finished_results")
        .select(",".join(COMPLETED_FIXTURE_GATE_COLUMNS))
        .eq("league", PRIMARY_LEAGUE)
        .eq("season", "2026-2027")
        .gte("match_date", PRIMARY_SEASON_START.isoformat())
        .lt("match_date", cutoff.isoformat())
    )

    identities: set[tuple[str, str, str]] = set()
    start = 0
    while True:
        response = query.range(start, start + PAGE_SIZE - 1).execute()
        rows = getattr(response, "data", None)
        if not isinstance(rows, list):
            raise ValueError("completed-fixture metadata query returned a malformed row page")
        for row in rows:
            if not isinstance(row, Mapping) or set(row) != set(COMPLETED_FIXTURE_GATE_COLUMNS):
                raise ValueError("completed-fixture query returned fields outside the frozen identity-only allowlist")
            match_day = _match_date(row["match_date"])
            if not (PRIMARY_SEASON_START <= match_day <= PRIMARY_SEASON_END):
                raise ValueError("completed-fixture metadata contains an identity outside the frozen primary season")
            if match_day >= cutoff:
                raise ValueError("completed-fixture metadata contains a same-day or future identity")
            home = _canonical_team(row["home_team"])
            away = _canonical_team(row["away_team"])
            if home.casefold() == away.casefold():
                raise ValueError("completed-fixture metadata contains identical canonical teams")
            identity = (match_day.isoformat(), home, away)
            reversed_identity = (identity[0], away, home)
            if reversed_identity in identities and reversed_identity != identity:
                raise ValueError("completed-fixture metadata contains a reversed duplicate identity")
            identities.add(identity)
        if len(rows) < PAGE_SIZE:
            break
        start += PAGE_SIZE
        if start >= MAX_ROWS:
            raise ValueError("completed-fixture metadata pagination exceeded the frozen safety bound")

    if not identities:
        raise ValueError("completed-fixture metadata query returned no eligible primary identities")

    attestation: dict[str, Any] = {
        "schema_version": COMPLETED_FIXTURE_GATE_SCHEMA,
        "source_table": COMPLETED_FIXTURE_GATE_SOURCE_TABLE,
        "selected_columns": list(COMPLETED_FIXTURE_GATE_COLUMNS),
        "league": PRIMARY_LEAGUE,
        "season": "2026-2027",
        "query_contract_id": COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_ID,
        "query_contract_sha256": COMPLETED_FIXTURE_GATE_QUERY_CONTRACT_SHA256,
        "captured_at_utc": captured.isoformat().replace("+00:00", "Z"),
        "cutoff_date_exclusive_utc": cutoff.isoformat(),
        "completed_fixture_identity_count": len(identities),
        "completed_fixture_identity_sha256": _sha_fixture_set(identities),
        "outcome_columns_selected": False,
        "target_outcomes_read": False,
    }
    return identities, attestation
