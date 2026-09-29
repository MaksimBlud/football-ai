"""V2B_TRAVEL_VENUE_FEASIBILITY_V1.

Source/provenance-only audit for reconstructing previous-match -> target-match
travel distance on the frozen 43-fixture V2B cohort.

No market rows, centre_delta, outcome labels, thresholds, betting or production
artifacts are read or changed.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from v2b_true_xg_replay_feasibility_v1 import (
    LEAGUE_SLUGS,
    TARGET_ALIASES,
    fetch_understat_league,
)

EXPERIMENT_ID = "V2B_TRAVEL_VENUE_FEASIBILITY_V1"
UPSTREAM_EXPERIMENT_ID = "V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1"
EXPECTED_UPSTREAM_ARTIFACT_ID = "11041563442"
EXPECTED_UPSTREAM_DIGEST = (
    "sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c"
)
EXPECTED_FIXTURES = 43
EXPECTED_TEAM_SIDES = 86
SEASON = 2026
TARGET_DATE = pd.Timestamp("2026-09-20")
WIKIDATA_API = "https://www.wikidata.org/w/api.php"
USER_AGENT = "football-ai-travel-feasibility/1.0 (research-only)"

SEARCH_ALIASES = {
    "AC Milan": "AC Milan football club",
    "Athletic Club": "Athletic Bilbao football club",
    "Atletico Madrid": "Atlético Madrid football club",
    "Bayer Leverkusen": "Bayer 04 Leverkusen football club",
    "Borussia M'gladbach": "Borussia Mönchengladbach football club",
    "Bournemouth": "AFC Bournemouth football club",
    "Brighton": "Brighton & Hove Albion football club",
    "CD Alaves": "Deportivo Alavés football club",
    "Celta Vigo": "Celta de Vigo football club",
    "Cologne": "1. FC Köln football club",
    "Como": "Como 1907 football club",
    "Coventry": "Coventry City football club",
    "Deportivo A Coruna": "Deportivo La Coruña football club",
    "Elversberg": "SV Elversberg football club",
    "Hamburg": "Hamburger SV football club",
    "Hull": "Hull City football club",
    "Inter": "Inter Milan football club",
    "Inter Milan": "Inter Milan football club",
    "Ipswich": "Ipswich Town football club",
    "Le Havre": "Le Havre AC football club",
    "Le Mans": "Le Mans FC football club",
    "Leeds": "Leeds United football club",
    "Leverkusen": "Bayer 04 Leverkusen football club",
    "Man City": "Manchester City football club",
    "Man Utd": "Manchester United football club",
    "Milan": "AC Milan football club",
    "Nottm Forest": "Nottingham Forest football club",
    "PSG": "Paris Saint-Germain football club",
    "Paris Saint-Germain": "Paris Saint-Germain football club",
    "Paderborn": "SC Paderborn 07 football club",
    "Racing Santander": "Racing de Santander football club",
    "RB Leipzig": "RB Leipzig football club",
    "Real Betis": "Real Betis football club",
    "Real Sociedad": "Real Sociedad football club",
    "SC Freiburg": "SC Freiburg football club",
    "Schalke": "FC Schalke 04 football club",
    "Stuttgart": "VfB Stuttgart football club",
    "Sunderland": "Sunderland AFC football club",
    "TSG Hoffenheim": "TSG 1899 Hoffenheim football club",
    "Tottenham": "Tottenham Hotspur football club",
    "VfB Stuttgart": "VfB Stuttgart football club",
}

FOOTBALL_DESCRIPTION_TERMS = (
    "football club",
    "association football",
    "soccer club",
    "professional football",
)


def _identity_key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return "".join(ch.lower() for ch in text if ch.isalnum())


def _date(value: Any) -> pd.Timestamp:
    stamp = pd.to_datetime(value, errors="coerce")
    if pd.isna(stamp):
        raise ValueError(f"invalid date: {value!r}")
    if getattr(stamp, "tzinfo", None) is not None:
        stamp = stamp.tz_convert("UTC").tz_localize(None)
    return pd.Timestamp(stamp).normalize()


def _validate_upstream(payload: dict[str, Any]) -> list[dict[str, Any]]:
    if payload.get("experiment_id") != UPSTREAM_EXPERIMENT_ID:
        raise RuntimeError("unexpected upstream experiment")
    if payload.get("status") != "FULL_43_RECONSTRUCTABLE_14D":
        raise RuntimeError("upstream full-calendar source is not complete")
    if payload.get("research_only") is not True:
        raise RuntimeError("upstream artifact is not research-only")
    if payload.get("source_feasibility_audit") is not True:
        raise RuntimeError("upstream source-feasibility flag missing")
    if int(payload.get("locked_fixture_count", -1)) != EXPECTED_FIXTURES:
        raise RuntimeError("unexpected upstream fixture count")
    if int(payload.get("full_calendar_feasible_fixture_count", -1)) != EXPECTED_FIXTURES:
        raise RuntimeError("upstream full-calendar coverage changed")
    for flag in (
        "market_rows_read",
        "v2b_odds_read",
        "centre_delta_read",
        "direction_test_performed",
        "match_outcome_target_used",
    ):
        if payload.get(flag) is not False:
            raise RuntimeError(f"upstream safety flag changed: {flag}")
    rows = payload.get("rows")
    if not isinstance(rows, list) or len(rows) != EXPECTED_FIXTURES:
        raise RuntimeError("unexpected upstream rows")
    return rows


def _understat_schedule(payload: dict[str, Any]) -> list[dict[str, Any]]:
    dates = payload.get("dates")
    if not isinstance(dates, list):
        return []
    rows = []
    for item in dates:
        if not isinstance(item, dict):
            continue
        h = item.get("h") or {}
        a = item.get("a") or {}
        home = str(h.get("title") or "").strip()
        away = str(a.get("title") or "").strip()
        raw_dt = item.get("datetime") or item.get("date")
        if not home or not away or not raw_dt:
            continue
        try:
            match_date = _date(raw_dt)
        except ValueError:
            continue
        rows.append(
            {
                "match_date": match_date,
                "home": home,
                "away": away,
                "is_result": bool(item.get("isResult", True)),
            }
        )
    return rows


def _resolve_understat_target_name(
    league: str,
    target_name: str,
    source_titles: set[str],
) -> str | None:
    desired = TARGET_ALIASES.get(league, {}).get(target_name, target_name)
    key = _identity_key(desired)
    matches = sorted(title for title in source_titles if _identity_key(title) == key)
    return matches[0] if len(matches) == 1 else None


def _nonleague_latest_host(load: dict[str, Any]) -> str | None:
    full_date = load.get("full_previous_match_date")
    league_date = load.get("league_previous_match_date")
    if not full_date or full_date == league_date:
        return None
    latest = [
        event for event in (load.get("nonleague_events_14d") or [])
        if str(event.get("date")) == str(full_date)
    ]
    if len(latest) != 1:
        return None
    label = str(latest[0].get("fixture_label") or "")
    parts = re.split(r"\s+vs\s+", label, maxsplit=1, flags=re.IGNORECASE)
    if len(parts) != 2 or not parts[0].strip():
        return None
    return parts[0].strip()


def _league_latest_host(
    *,
    league: str,
    target_name: str,
    previous_date: str,
    schedules: dict[str, list[dict[str, Any]]],
) -> tuple[str | None, str | None]:
    schedule = schedules.get(league, [])
    titles = {row["home"] for row in schedule} | {row["away"] for row in schedule}
    resolved = _resolve_understat_target_name(league, target_name, titles)
    if resolved is None:
        return None, None
    target_date = _date(previous_date)
    matches = [
        row for row in schedule
        if row["match_date"] == target_date
        and resolved in (row["home"], row["away"])
        and row["is_result"]
    ]
    if len(matches) != 1:
        return resolved, None
    return resolved, str(matches[0]["home"])


def reconstruct_previous_hosts(
    rows: list[dict[str, Any]],
    schedules: dict[str, list[dict[str, Any]]],
) -> tuple[list[dict[str, Any]], set[str]]:
    records: list[dict[str, Any]] = []
    venue_clubs: set[str] = set()

    for fixture in rows:
        current_host = str(fixture["home_team"])
        venue_clubs.add(current_host)

        for side in ("home", "away"):
            target_team = str(fixture[f"{side}_team"])
            load = fixture.get(f"{side}_load")
            if not isinstance(load, dict):
                previous_host = None
                source = "MISSING_LOAD"
                resolved_understat = None
            else:
                previous_host = _nonleague_latest_host(load)
                if previous_host is not None:
                    source = "FROZEN_NONLEAGUE_MANIFEST"
                    resolved_understat = None
                else:
                    resolved_understat, previous_host = _league_latest_host(
                        league=str(fixture["league"]),
                        target_name=target_team,
                        previous_date=str(load.get("full_previous_match_date") or ""),
                        schedules=schedules,
                    )
                    source = "UNDERSTAT_LEAGUE_SCHEDULE"

            if previous_host:
                venue_clubs.add(previous_host)

            records.append(
                {
                    "fixture_id": str(fixture["fixture_id"]),
                    "league": str(fixture["league"]),
                    "side": side,
                    "team": target_team,
                    "current_venue_host": current_host,
                    "previous_match_date": None if not isinstance(load, dict)
                    else load.get("full_previous_match_date"),
                    "previous_venue_host": previous_host,
                    "previous_venue_source": source,
                    "understat_target_title": resolved_understat,
                }
            )

    if len(records) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected team-side count")
    return records, venue_clubs


class WikidataResolver:
    def __init__(self, session: requests.Session):
        self.session = session
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.club_cache: dict[str, dict[str, Any]] = {}
        self.entity_cache: dict[str, dict[str, Any]] = {}

    def _request(self, params: dict[str, Any]) -> dict[str, Any]:
        response = self.session.get(WIKIDATA_API, params=params, timeout=30)
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("invalid Wikidata response")
        time.sleep(0.03)
        return payload

    def _search_club(self, club_name: str) -> tuple[str | None, dict[str, Any]]:
        query = SEARCH_ALIASES.get(club_name, f"{club_name} football club")
        payload = self._request(
            {
                "action": "wbsearchentities",
                "search": query,
                "language": "en",
                "format": "json",
                "limit": 10,
                "type": "item",
            }
        )
        results = payload.get("search") or []
        accepted = []
        for item in results:
            description = str(item.get("description") or "").lower()
            label = str(item.get("label") or "")
            if any(term in description for term in FOOTBALL_DESCRIPTION_TERMS):
                accepted.append(
                    {
                        "id": item.get("id"),
                        "label": label,
                        "description": item.get("description"),
                        "match": item.get("match"),
                    }
                )
        qid = str(accepted[0]["id"]) if accepted and accepted[0].get("id") else None
        return qid, {
            "query": query,
            "accepted_candidates": accepted[:5],
        }

    def _entity(self, qid: str) -> dict[str, Any]:
        if qid in self.entity_cache:
            return self.entity_cache[qid]
        payload = self._request(
            {
                "action": "wbgetentities",
                "ids": qid,
                "props": "claims|labels|aliases",
                "languages": "en",
                "format": "json",
            }
        )
        entity = (payload.get("entities") or {}).get(qid)
        if not isinstance(entity, dict):
            raise RuntimeError(f"Wikidata entity missing: {qid}")
        self.entity_cache[qid] = entity
        return entity

    @staticmethod
    def _claim_time(statement: dict[str, Any], prop: str) -> pd.Timestamp | None:
        qualifiers = statement.get("qualifiers") or {}
        values = qualifiers.get(prop) or []
        if not values:
            return None
        try:
            raw = values[0]["datavalue"]["value"]["time"]
            return pd.Timestamp(str(raw).lstrip("+")[:10])
        except Exception:
            return None

    def _current_home_venue_qid(self, club_entity: dict[str, Any]) -> str | None:
        claims = (club_entity.get("claims") or {}).get("P115") or []
        candidates = []
        for statement in claims:
            mainsnak = statement.get("mainsnak") or {}
            value = (mainsnak.get("datavalue") or {}).get("value") or {}
            qid = value.get("id")
            if not qid:
                continue
            end = self._claim_time(statement, "P582")
            start = self._claim_time(statement, "P580")
            if end is not None and end < TARGET_DATE:
                continue
            rank = str(statement.get("rank") or "normal")
            candidates.append(
                {
                    "qid": str(qid),
                    "rank": rank,
                    "start": start,
                    "end": end,
                }
            )
        if not candidates:
            return None
        candidates.sort(
            key=lambda row: (
                1 if row["rank"] == "preferred" else 0,
                row["start"].value if row["start"] is not None else -1,
            ),
            reverse=True,
        )
        return str(candidates[0]["qid"])

    @staticmethod
    def _coordinate(entity: dict[str, Any]) -> tuple[float, float] | None:
        claims = (entity.get("claims") or {}).get("P625") or []
        if not claims:
            return None
        ranked = sorted(
            claims,
            key=lambda statement: 1 if statement.get("rank") == "preferred" else 0,
            reverse=True,
        )
        for statement in ranked:
            value = ((statement.get("mainsnak") or {}).get("datavalue") or {}).get("value")
            if not isinstance(value, dict):
                continue
            lat = value.get("latitude")
            lon = value.get("longitude")
            try:
                lat_f = float(lat)
                lon_f = float(lon)
            except (TypeError, ValueError):
                continue
            if math.isfinite(lat_f) and math.isfinite(lon_f):
                return lat_f, lon_f
        return None

    @staticmethod
    def _label(entity: dict[str, Any], fallback: str) -> str:
        labels = entity.get("labels") or {}
        return str((labels.get("en") or {}).get("value") or fallback)

    def resolve_club_venue(self, club_name: str) -> dict[str, Any]:
        if club_name in self.club_cache:
            return self.club_cache[club_name]

        qid, search_meta = self._search_club(club_name)
        record: dict[str, Any] = {
            "club_name": club_name,
            "search": search_meta,
            "club_qid": qid,
            "club_label": None,
            "venue_qid": None,
            "venue_label": None,
            "latitude": None,
            "longitude": None,
            "resolved": False,
        }
        if qid is None:
            self.club_cache[club_name] = record
            return record

        try:
            club_entity = self._entity(qid)
            record["club_label"] = self._label(club_entity, club_name)
            venue_qid = self._current_home_venue_qid(club_entity)
            record["venue_qid"] = venue_qid
            if venue_qid is None:
                self.club_cache[club_name] = record
                return record
            venue_entity = self._entity(venue_qid)
            record["venue_label"] = self._label(venue_entity, venue_qid)
            coord = self._coordinate(venue_entity)
            if coord is None:
                self.club_cache[club_name] = record
                return record
            record["latitude"] = coord[0]
            record["longitude"] = coord[1]
            record["resolved"] = True
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}:{str(exc)[:250]}"

        self.club_cache[club_name] = record
        return record


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    radius = 6371.0088
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (
        math.sin(dphi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(dlambda / 2.0) ** 2
    )
    return 2.0 * radius * math.asin(min(1.0, math.sqrt(a)))


def audit(
    upstream: dict[str, Any],
    *,
    session: requests.Session | None = None,
) -> dict[str, Any]:
    rows = _validate_upstream(upstream)
    owned = session is None
    if session is None:
        session = requests.Session()

    payloads: dict[str, dict[str, Any]] = {}
    source_errors: dict[str, str] = {}
    try:
        for league in LEAGUE_SLUGS:
            try:
                payloads[league] = fetch_understat_league(
                    session,
                    league=league,
                    season=SEASON,
                )
            except Exception as exc:
                source_errors[league] = f"{type(exc).__name__}:{str(exc)[:250]}"

        schedules = {
            league: _understat_schedule(payload)
            for league, payload in payloads.items()
        }
        team_sides, venue_clubs = reconstruct_previous_hosts(rows, schedules)

        resolver = WikidataResolver(session)
        venue_records = {
            club: resolver.resolve_club_venue(club)
            for club in sorted(venue_clubs)
        }

        resolved_sides = 0
        previous_host_reconstructed = 0
        previous_coordinates_resolved = 0
        current_coordinates_resolved = 0

        for row in team_sides:
            previous_host = row["previous_venue_host"]
            current_host = row["current_venue_host"]
            if previous_host:
                previous_host_reconstructed += 1

            previous = venue_records.get(previous_host) if previous_host else None
            current = venue_records.get(current_host)

            previous_ok = bool(previous and previous.get("resolved"))
            current_ok = bool(current and current.get("resolved"))
            previous_coordinates_resolved += int(previous_ok)
            current_coordinates_resolved += int(current_ok)

            row["previous_venue"] = None if previous is None else {
                key: previous.get(key)
                for key in (
                    "club_qid",
                    "club_label",
                    "venue_qid",
                    "venue_label",
                    "latitude",
                    "longitude",
                    "resolved",
                )
            }
            row["current_venue"] = None if current is None else {
                key: current.get(key)
                for key in (
                    "club_qid",
                    "club_label",
                    "venue_qid",
                    "venue_label",
                    "latitude",
                    "longitude",
                    "resolved",
                )
            }

            if previous_ok and current_ok:
                distance = haversine_km(
                    float(previous["latitude"]),
                    float(previous["longitude"]),
                    float(current["latitude"]),
                    float(current["longitude"]),
                )
                row["travel_km_since_previous_match"] = distance
                resolved_sides += 1
            else:
                row["travel_km_since_previous_match"] = None

        current_hosts = sorted({str(row["home_team"]) for row in rows})
        current_hosts_resolved = sum(
            bool(venue_records.get(host, {}).get("resolved"))
            for host in current_hosts
        )
        unresolved_clubs = sorted(
            club for club, record in venue_records.items()
            if not record.get("resolved")
        )

        full = bool(
            len(current_hosts) == EXPECTED_FIXTURES
            and current_hosts_resolved == EXPECTED_FIXTURES
            and previous_host_reconstructed == EXPECTED_TEAM_SIDES
            and previous_coordinates_resolved == EXPECTED_TEAM_SIDES
            and current_coordinates_resolved == EXPECTED_TEAM_SIDES
            and resolved_sides == EXPECTED_TEAM_SIDES
            and not source_errors
        )

        if source_errors:
            status = "UNDERSTAT_SOURCE_GAPS"
        elif previous_host_reconstructed < EXPECTED_TEAM_SIDES:
            status = "PREVIOUS_VENUE_IDENTITY_GAPS"
        elif unresolved_clubs:
            status = "WIKIDATA_VENUE_COORDINATE_GAPS"
        elif full:
            status = "FULL_43_TRAVEL_PROXY_FEASIBLE"
        else:
            status = "PARTIAL_TRAVEL_PROXY_FEASIBILITY"

        distances = [
            float(row["travel_km_since_previous_match"])
            for row in team_sides
            if row["travel_km_since_previous_match"] is not None
        ]

        report = {
            "experiment_id": EXPERIMENT_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "research_only": True,
            "source_feasibility_audit": True,
            "travel_proxy_definition": (
                "haversine(previous fixture host club current home venue, "
                "target fixture home club current home venue)"
            ),
            "venue_model_limitation": (
                "host-club current home venue proxy; neutral/exceptional historical "
                "venues are not independently verified in V1"
            ),
            "upstream_artifact_id": EXPECTED_UPSTREAM_ARTIFACT_ID,
            "upstream_artifact_digest": EXPECTED_UPSTREAM_DIGEST,
            "locked_fixture_count": EXPECTED_FIXTURES,
            "team_side_count": EXPECTED_TEAM_SIDES,
            "understat_schedule_sources_ready": len(payloads),
            "understat_source_errors": source_errors,
            "current_target_host_count": len(current_hosts),
            "current_target_hosts_resolved": int(current_hosts_resolved),
            "previous_host_identity_reconstructed": int(previous_host_reconstructed),
            "previous_venue_coordinates_resolved": int(previous_coordinates_resolved),
            "current_venue_coordinates_resolved_team_sides": int(
                current_coordinates_resolved
            ),
            "travel_distance_resolved_team_sides": int(resolved_sides),
            "unique_venue_club_count": len(venue_records),
            "resolved_venue_club_count": int(
                sum(bool(record.get("resolved")) for record in venue_records.values())
            ),
            "unresolved_venue_clubs": unresolved_clubs,
            "status": status,
            "market_rows_read": False,
            "v2b_odds_read": False,
            "opening_lambda_read": False,
            "fair_centre_read": False,
            "centre_delta_read": False,
            "direction_test_performed": False,
            "match_outcome_target_used": False,
            "threshold_fitted_to_outcomes": False,
            "odds_api_requests": 0,
            "supabase_operations": 0,
            "production_model_operations": 0,
            "distance_summary_km": None if not distances else {
                "count": len(distances),
                "mean": float(pd.Series(distances).mean()),
                "median": float(pd.Series(distances).median()),
                "max": max(distances),
                "zero_or_near_zero_le_5km": int(sum(value <= 5.0 for value in distances)),
            },
            "venue_records": venue_records,
            "rows": team_sides,
        }
        return report
    finally:
        if owned:
            session.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full-calendar-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    upstream = json.loads(
        args.full_calendar_report.read_text(encoding="utf-8")
    )
    report = audit(upstream)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
