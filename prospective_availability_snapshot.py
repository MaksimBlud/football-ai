"""Normalize append-only API-Football availability polls and poll items."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
import unicodedata

import pandas as pd

from prospective_availability_contract import PROVIDER
from prospective_availability_provider import canonical_json_sha256


def utc_timestamp(value) -> pd.Timestamp:
    result = pd.Timestamp(value)
    if result.tzinfo is None:
        result = result.tz_localize("UTC")
    return result.tz_convert("UTC")


def normalized_team_token(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", "", text.casefold())


def normalize_provider_team(value: str, aliases: dict[str, str]) -> str:
    value = str(value).strip()
    return aliases.get(value, value)


def match_provider_fixture(
    canonical_row: dict,
    provider_fixtures: list[dict],
    *,
    aliases: dict[str, str],
    kickoff_tolerance_minutes: int = 15,
) -> dict:
    target_home = normalized_team_token(canonical_row["home_team"])
    target_away = normalized_team_token(canonical_row["away_team"])
    target_kickoff = utc_timestamp(canonical_row["commence_time_utc"])
    matches = []
    for item in provider_fixtures:
        teams = item.get("teams") or {}
        fixture = item.get("fixture") or {}
        home = normalize_provider_team((teams.get("home") or {}).get("name", ""), aliases)
        away = normalize_provider_team((teams.get("away") or {}).get("name", ""), aliases)
        kickoff = pd.to_datetime(fixture.get("date"), utc=True, errors="coerce")
        if pd.isna(kickoff):
            continue
        if normalized_team_token(home) != target_home or normalized_team_token(away) != target_away:
            continue
        delta = abs((kickoff - target_kickoff).total_seconds()) / 60.0
        if delta <= kickoff_tolerance_minutes:
            matches.append(item)
    if len(matches) != 1:
        raise ValueError(f"Provider fixture match must be unique; matches={len(matches)}")
    return matches[0]


def _availability_type(item: dict) -> str:
    player = item.get("player") or {}
    text = " ".join(str(player.get(key) or "") for key in ("type", "reason")).casefold()
    return "Suspension" if "susp" in text else "Injury"


def _state_key(provider_fixture_id, provider_team_id, provider_player_id, availability_type, reason) -> str:
    raw = "|".join(
        map(
            str,
            (PROVIDER, provider_fixture_id, provider_team_id, provider_player_id, availability_type, reason or ""),
        )
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def normalize_poll(
    *,
    canonical_row: dict,
    provider_fixture: dict,
    injury_payload: dict,
    observed_at_utc,
) -> tuple[dict, pd.DataFrame]:
    observed = utc_timestamp(observed_at_utc)
    kickoff = utc_timestamp(canonical_row["commence_time_utc"])
    if observed >= kickoff:
        raise ValueError("Availability poll must be observed before kickoff")
    fixture = provider_fixture.get("fixture") or {}
    provider_fixture_id = int(fixture["id"])
    raw_sha = canonical_json_sha256(injury_payload)
    poll_material = "|".join(
        (str(PROVIDER), str(provider_fixture_id), str(canonical_row["league"]), kickoff.isoformat(), raw_sha)
    )
    poll_key = hashlib.sha256(poll_material.encode("utf-8")).hexdigest()
    poll = {
        "poll_key": poll_key,
        "provider": PROVIDER,
        "provider_fixture_id": provider_fixture_id,
        "league": str(canonical_row["league"]),
        "home_team": str(canonical_row["home_team"]),
        "away_team": str(canonical_row["away_team"]),
        "commence_time_utc": kickoff,
        "observed_at_utc": observed,
        "raw_payload_sha256": raw_sha,
        "item_count": len(injury_payload.get("response") or []),
        "payload": injury_payload,
    }
    rows = []
    for item in injury_payload.get("response") or []:
        team = item.get("team") or {}
        player = item.get("player") or {}
        availability_type = _availability_type(item)
        reason = str(player.get("reason") or player.get("type") or "").strip()
        provider_team_id = int(team["id"])
        provider_player_id = int(player["id"])
        state_key = _state_key(
            provider_fixture_id,
            provider_team_id,
            provider_player_id,
            availability_type,
            reason,
        )
        observation_key = hashlib.sha256(f"{poll_key}|{state_key}".encode("utf-8")).hexdigest()
        rows.append(
            {
                "observation_key": observation_key,
                "state_key": state_key,
                "poll_key": poll_key,
                "provider": PROVIDER,
                "provider_fixture_id": provider_fixture_id,
                "provider_team_id": provider_team_id,
                "provider_player_id": provider_player_id,
                "league": str(canonical_row["league"]),
                "home_team": str(canonical_row["home_team"]),
                "away_team": str(canonical_row["away_team"]),
                "commence_time_utc": kickoff,
                "team_name": str(team.get("name") or "").strip(),
                "player_name": str(player.get("name") or "").strip(),
                "availability_type": availability_type,
                "reason": reason,
                "source_timestamp_utc": observed,
                "source_timestamp_kind": "collector_observed",
                "observed_at_utc": observed,
                "first_seen_timestamp_utc": observed,
                "raw_payload_sha256": canonical_json_sha256(item),
            }
        )
    return poll, pd.DataFrame(rows)
