"""V2B_TRAVEL_VENUE_FEASIBILITY_V1.

Source-only audit for a venue-city travel proxy on the frozen 43-fixture V2B
cohort. Previous-match host identity comes from the already-frozen full-calendar
artifact plus public Understat league schedule. Club->city identity comes from a
pinned openfootball/clubs archive; coordinates come from the GeoNames cities500
bulk dump.

No market rows, centre_delta, target outcomes, thresholds, betting or production
artifacts are read or changed.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import re
import tarfile
import unicodedata
import zipfile
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

OPENFOOTBALL_COMMIT = "ae3800227c449447b3a337fc0aac79a8f02f4c8b"
OPENFOOTBALL_URL = (
    "https://codeload.github.com/openfootball/clubs/tar.gz/"
    + OPENFOOTBALL_COMMIT
)
GEONAMES_URL = "https://download.geonames.org/export/dump/cities500.zip"
USER_AGENT = "football-ai-travel-feasibility/1.1 (research-only)"

COUNTRY_DIR_TO_ISO = {
    "albania": "AL",
    "andorra": "AD",
    "armenia": "AM",
    "austria": "AT",
    "azerbaijan": "AZ",
    "belarus": "BY",
    "belgium": "BE",
    "bosnia-n-herzegovina": "BA",
    "bulgaria": "BG",
    "croatia": "HR",
    "cyprus": "CY",
    "czech-republic": "CZ",
    "denmark": "DK",
    "england": "GB",
    "estonia": "EE",
    "faroe-islands": "FO",
    "finland": "FI",
    "france": "FR",
    "georgia": "GE",
    "germany": "DE",
    "gibraltar": "GI",
    "greece": "GR",
    "hungary": "HU",
    "iceland": "IS",
    "ireland": "IE",
    "italy": "IT",
    "kosovo": "XK",
    "latvija": "LV",
    "liechtenstein": "LI",
    "lithuania": "LT",
    "luxembourg": "LU",
    "macedonia": "MK",
    "malta": "MT",
    "moldova": "MD",
    "monaco": "MC",
    "montenegro": "ME",
    "netherlands": "NL",
    "northern-ireland": "GB",
    "norway": "NO",
    "poland": "PL",
    "portugal": "PT",
    "romania": "RO",
    "russia": "RU",
    "san-marino": "SM",
    "scotland": "GB",
    "serbia": "RS",
    "slovakia": "SK",
    "slovenia": "SI",
    "spain": "ES",
    "sweden": "SE",
    "switzerland": "CH",
    "turkey": "TR",
    "ukraine": "UA",
    "wales": "GB",
}

# Identity plumbing only. These convert provider/fixture-label names to aliases
# used by the pinned club catalog. They are frozen before any direction join.
CLUB_NAME_ALIASES = {
    "Athletic Club": "Athletic Bilbao",
    "CD Alaves": "Alaves",
    "Deportivo A Coruna": "Deportivo La Coruna",
    "Inter Milan": "Inter",
    "Man City": "Manchester City",
    "Man Utd": "Manchester United",
    "Nottm Forest": "Nottingham Forest",
    "PSG": "Paris Saint-Germain",
    "RB Leipzig": "RB Leipzig",
    "SC Freiburg": "SC Freiburg",
    "TSG Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "VfB Stuttgart",
}

# City-name plumbing for a few club catalog localities that are football-ground
# districts/suburbs rather than the intended travel-city centroid.
CITY_NAME_ALIASES = {
    ("GB", "falmer"): "Brighton",
    ("GB", "westbridgford"): "Nottingham",
}


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


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
    rows: list[dict[str, Any]] = []
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
    matches = sorted(
        title for title in source_titles
        if _identity_key(title) == key
    )
    return matches[0] if len(matches) == 1 else None


def _nonleague_latest_host(load: dict[str, Any]) -> str | None:
    full_date = load.get("full_previous_match_date")
    league_date = load.get("league_previous_match_date")
    if not full_date or full_date == league_date:
        return None
    latest = [
        event
        for event in (load.get("nonleague_events_14d") or [])
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
    resolved = _resolve_understat_target_name(
        league,
        target_name,
        titles,
    )
    if resolved is None:
        return None, None
    try:
        target_date = _date(previous_date)
    except ValueError:
        return resolved, None
    matches = [
        row
        for row in schedule
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
            resolved_understat = None

            if not isinstance(load, dict):
                previous_host = None
                source = "MISSING_LOAD"
            else:
                previous_host = _nonleague_latest_host(load)
                if previous_host is not None:
                    source = "FROZEN_NONLEAGUE_MANIFEST"
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
                    "previous_match_date": (
                        None
                        if not isinstance(load, dict)
                        else load.get("full_previous_match_date")
                    ),
                    "previous_venue_host": previous_host,
                    "previous_venue_source": source,
                    "understat_target_title": resolved_understat,
                }
            )

    if len(records) != EXPECTED_TEAM_SIDES:
        raise RuntimeError("unexpected team-side count")
    return records, venue_clubs


def _download_bytes(
    session: requests.Session,
    url: str,
    *,
    attempts: int = 3,
) -> bytes:
    last_error: Exception | None = None
    for _ in range(attempts):
        try:
            response = session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=90,
            )
            response.raise_for_status()
            if not response.content:
                raise RuntimeError(f"empty bulk source: {url}")
            return bytes(response.content)
        except Exception as exc:  # pragma: no cover - live retry path
            last_error = exc
    raise RuntimeError(
        f"bulk source download failed: {url}: {type(last_error).__name__}: {last_error}"
    )


def _clean_city(value: str) -> str | None:
    city = str(value).strip()
    city = city.split("›", 1)[0].strip()
    city = city.split("//", 1)[0].strip()
    city = re.sub(r"\s*\([^)]*\)\s*$", "", city).strip()
    city = city.strip(" ,;")
    if not city or city.startswith("@"):
        return None
    if re.fullmatch(r"(?:18|19|20)\d{2}", city):
        return None
    if re.fullmatch(r"[\d_]+", city):
        return None
    return city


def _extract_city_from_club_line(line: str) -> str | None:
    clean = line.split("##", 1)[0].split("#", 1)[0].strip()
    parts = [part.strip() for part in clean.split(",")]
    if len(parts) < 2:
        return None
    for token in reversed(parts[1:]):
        city = _clean_city(token)
        if city is None:
            continue
        if token.lstrip().startswith("@"):
            continue
        return city
    return None


def _parse_club_file(
    text: str,
    *,
    country_code: str,
    source_path: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None

    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith(("#", "=")):
            continue

        if raw[:1].isspace():
            if current is not None and stripped.startswith("|"):
                alias_text = stripped.split("#", 1)[0]
                for alias in alias_text.split("|"):
                    value = alias.strip()
                    if value:
                        current["aliases"].append(value)
            continue

        if stripped.lower().startswith(("ii)", "iii)", "iv)")):
            current = None
            continue

        clean = stripped.split("##", 1)[0].split("#", 1)[0].strip()
        if not clean:
            current = None
            continue
        canonical = clean.split(",", 1)[0].strip()
        if not canonical or canonical.startswith(("-", "[")):
            current = None
            continue

        city = _extract_city_from_club_line(clean)
        current = {
            "canonical": canonical,
            "aliases": [],
            "city": city,
            "country_code": country_code,
            "source_path": source_path,
        }
        records.append(current)

    return records


def parse_openfootball_archive(payload: bytes) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile() or not member.name.endswith(".clubs.txt"):
                continue
            parts = member.name.split("/")
            try:
                europe_index = parts.index("europe")
            except ValueError:
                continue
            if europe_index + 1 >= len(parts):
                continue
            country_dir = parts[europe_index + 1]
            country_code = COUNTRY_DIR_TO_ISO.get(country_dir)
            if country_code is None:
                continue
            handle = archive.extractfile(member)
            if handle is None:
                continue
            text = handle.read().decode("utf-8-sig", errors="replace")
            records.extend(
                _parse_club_file(
                    text,
                    country_code=country_code,
                    source_path=member.name,
                )
            )
    if not records:
        raise RuntimeError("openfootball archive yielded no club records")
    return records


def build_club_index(
    records: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    index: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        names = [record["canonical"], *record["aliases"]]
        for name in names:
            key = _identity_key(name)
            if not key:
                continue
            index.setdefault(key, []).append(record)
    return index


def resolve_club_city(
    club_name: str,
    index: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    lookup = CLUB_NAME_ALIASES.get(club_name, club_name)
    candidates = index.get(_identity_key(lookup), [])
    # Deduplicate repeated alias references to the same source row.
    unique: dict[tuple[str, str, str | None], dict[str, Any]] = {}
    for record in candidates:
        key = (
            str(record["source_path"]),
            str(record["canonical"]),
            record["city"],
        )
        unique[key] = record
    candidates = list(unique.values())

    with_city = [row for row in candidates if row.get("city")]
    if len(with_city) == 1:
        row = with_city[0]
        return {
            "club_name": club_name,
            "lookup_name": lookup,
            "resolved": True,
            "canonical": row["canonical"],
            "city": row["city"],
            "country_code": row["country_code"],
            "source_path": row["source_path"],
            "candidate_count": len(with_city),
        }

    return {
        "club_name": club_name,
        "lookup_name": lookup,
        "resolved": False,
        "canonical": None,
        "city": None,
        "country_code": None,
        "source_path": None,
        "candidate_count": len(with_city),
        "candidates": [
            {
                "canonical": row["canonical"],
                "city": row["city"],
                "country_code": row["country_code"],
                "source_path": row["source_path"],
            }
            for row in with_city[:10]
        ],
    }


GEONAMES_COLUMNS = [
    "geonameid",
    "name",
    "asciiname",
    "alternatenames",
    "latitude",
    "longitude",
    "feature_class",
    "feature_code",
    "country_code",
    "cc2",
    "admin1_code",
    "admin2_code",
    "admin3_code",
    "admin4_code",
    "population",
    "elevation",
    "dem",
    "timezone",
    "modification_date",
]


def parse_geonames_archive(payload: bytes) -> pd.DataFrame:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = [name for name in archive.namelist() if name.endswith(".txt")]
        if len(names) != 1:
            raise RuntimeError(f"unexpected GeoNames archive members: {names}")
        with archive.open(names[0]) as handle:
            frame = pd.read_csv(
                handle,
                sep="\t",
                names=GEONAMES_COLUMNS,
                dtype={"country_code": "string"},
                keep_default_na=False,
                low_memory=False,
            )
    if frame.empty:
        raise RuntimeError("GeoNames city frame is empty")
    frame["population"] = pd.to_numeric(frame["population"], errors="coerce").fillna(0)
    frame["latitude"] = pd.to_numeric(frame["latitude"], errors="coerce")
    frame["longitude"] = pd.to_numeric(frame["longitude"], errors="coerce")
    frame = frame[
        frame["latitude"].notna()
        & frame["longitude"].notna()
        & frame["country_code"].ne("")
    ].copy()
    return frame


def build_city_index(
    frame: pd.DataFrame,
) -> dict[tuple[str, str], list[dict[str, Any]]]:
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for row in frame.itertuples(index=False):
        names = [row.name, row.asciiname]
        if row.alternatenames:
            names.extend(str(row.alternatenames).split(","))
        record = {
            "geonameid": int(row.geonameid),
            "name": str(row.name),
            "asciiname": str(row.asciiname),
            "country_code": str(row.country_code),
            "latitude": float(row.latitude),
            "longitude": float(row.longitude),
            "population": int(row.population),
        }
        seen: set[str] = set()
        for name in names:
            key = _identity_key(name)
            if not key or key in seen:
                continue
            seen.add(key)
            index.setdefault((record["country_code"], key), []).append(record)
    return index


def resolve_city_coordinate(
    *,
    country_code: str,
    city: str,
    index: dict[tuple[str, str], list[dict[str, Any]]],
) -> dict[str, Any]:
    normalized = _identity_key(city)
    lookup_city = CITY_NAME_ALIASES.get(
        (country_code, normalized),
        city,
    )
    candidates = index.get(
        (country_code, _identity_key(lookup_city)),
        [],
    )
    if not candidates:
        return {
            "resolved": False,
            "requested_city": city,
            "lookup_city": lookup_city,
            "country_code": country_code,
            "candidate_count": 0,
        }

    best = max(
        candidates,
        key=lambda row: (
            int(row["population"]),
            -int(row["geonameid"]),
        ),
    )
    return {
        "resolved": True,
        "requested_city": city,
        "lookup_city": lookup_city,
        "country_code": country_code,
        "candidate_count": len(candidates),
        **best,
    }


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

    understat_payloads: dict[str, dict[str, Any]] = {}
    understat_errors: dict[str, str] = {}

    try:
        for league in LEAGUE_SLUGS:
            try:
                understat_payloads[league] = fetch_understat_league(
                    session,
                    league=league,
                    season=SEASON,
                )
            except Exception as exc:
                understat_errors[league] = (
                    f"{type(exc).__name__}:{str(exc)[:250]}"
                )

        schedules = {
            league: _understat_schedule(payload)
            for league, payload in understat_payloads.items()
        }
        team_sides, venue_clubs = reconstruct_previous_hosts(
            rows,
            schedules,
        )

        openfootball_bytes = _download_bytes(
            session,
            OPENFOOTBALL_URL,
        )
        geonames_bytes = _download_bytes(
            session,
            GEONAMES_URL,
        )

        club_records = parse_openfootball_archive(openfootball_bytes)
        club_index = build_club_index(club_records)
        city_frame = parse_geonames_archive(geonames_bytes)
        city_index = build_city_index(city_frame)

        club_resolutions: dict[str, dict[str, Any]] = {}
        for club in sorted(venue_clubs):
            resolved = resolve_club_city(
                club,
                club_index,
            )
            if resolved["resolved"]:
                resolved["city_coordinate"] = resolve_city_coordinate(
                    country_code=str(resolved["country_code"]),
                    city=str(resolved["city"]),
                    index=city_index,
                )
            else:
                resolved["city_coordinate"] = None
            club_resolutions[club] = resolved

        previous_host_reconstructed = 0
        previous_club_city_resolved = 0
        current_club_city_resolved = 0
        previous_coordinate_resolved = 0
        current_coordinate_resolved = 0
        travel_resolved = 0

        for row in team_sides:
            previous_host = row["previous_venue_host"]
            current_host = row["current_venue_host"]

            if previous_host:
                previous_host_reconstructed += 1

            previous = (
                club_resolutions.get(str(previous_host))
                if previous_host
                else None
            )
            current = club_resolutions.get(str(current_host))

            previous_city_ok = bool(
                previous
                and previous.get("resolved")
            )
            current_city_ok = bool(
                current
                and current.get("resolved")
            )
            previous_club_city_resolved += int(previous_city_ok)
            current_club_city_resolved += int(current_city_ok)

            previous_coord = (
                previous.get("city_coordinate")
                if previous_city_ok
                else None
            )
            current_coord = (
                current.get("city_coordinate")
                if current_city_ok
                else None
            )
            previous_coord_ok = bool(
                previous_coord
                and previous_coord.get("resolved")
            )
            current_coord_ok = bool(
                current_coord
                and current_coord.get("resolved")
            )
            previous_coordinate_resolved += int(previous_coord_ok)
            current_coordinate_resolved += int(current_coord_ok)

            row["previous_club_city"] = previous
            row["current_club_city"] = current

            if previous_coord_ok and current_coord_ok:
                distance = haversine_km(
                    float(previous_coord["latitude"]),
                    float(previous_coord["longitude"]),
                    float(current_coord["latitude"]),
                    float(current_coord["longitude"]),
                )
                if not math.isfinite(distance) or distance < 0.0:
                    raise RuntimeError("invalid travel distance")
                row["travel_city_km_since_previous_match"] = distance
                travel_resolved += 1
            else:
                row["travel_city_km_since_previous_match"] = None

        unresolved_clubs = sorted(
            club
            for club, resolution in club_resolutions.items()
            if not resolution.get("resolved")
        )
        unresolved_cities = sorted(
            club
            for club, resolution in club_resolutions.items()
            if resolution.get("resolved")
            and not (
                resolution.get("city_coordinate")
                and resolution["city_coordinate"].get("resolved")
            )
        )

        if understat_errors:
            status = "UNDERSTAT_SOURCE_GAPS"
        elif previous_host_reconstructed < EXPECTED_TEAM_SIDES:
            status = "PREVIOUS_HOST_IDENTITY_GAPS"
        elif unresolved_clubs:
            status = "OPENFOOTBALL_CLUB_CITY_GAPS"
        elif unresolved_cities:
            status = "GEONAMES_CITY_COORDINATE_GAPS"
        elif travel_resolved == EXPECTED_TEAM_SIDES:
            status = "FULL_43_TRAVEL_CITY_PROXY_FEASIBLE"
        else:
            status = "PARTIAL_TRAVEL_CITY_PROXY_FEASIBILITY"

        distances = [
            float(row["travel_city_km_since_previous_match"])
            for row in team_sides
            if row["travel_city_km_since_previous_match"] is not None
        ]

        return {
            "experiment_id": EXPERIMENT_ID,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "research_only": True,
            "source_feasibility_audit": True,
            "travel_proxy_definition": (
                "haversine(previous fixture host club home-city centroid, "
                "target fixture home club home-city centroid)"
            ),
            "geographic_precision": "CLUB_HOME_CITY_CENTROID_PROXY",
            "openfootball_commit": OPENFOOTBALL_COMMIT,
            "openfootball_archive_sha256": _sha256_bytes(openfootball_bytes),
            "geonames_source": GEONAMES_URL,
            "geonames_archive_sha256": _sha256_bytes(geonames_bytes),
            "upstream_artifact_id": EXPECTED_UPSTREAM_ARTIFACT_ID,
            "upstream_artifact_digest": EXPECTED_UPSTREAM_DIGEST,
            "locked_fixture_count": EXPECTED_FIXTURES,
            "team_side_count": EXPECTED_TEAM_SIDES,
            "understat_schedule_sources_ready": len(understat_payloads),
            "understat_source_errors": understat_errors,
            "previous_host_identity_reconstructed": int(
                previous_host_reconstructed
            ),
            "previous_club_city_resolved": int(previous_club_city_resolved),
            "current_club_city_resolved_team_sides": int(
                current_club_city_resolved
            ),
            "previous_city_coordinates_resolved": int(
                previous_coordinate_resolved
            ),
            "current_city_coordinates_resolved_team_sides": int(
                current_coordinate_resolved
            ),
            "travel_distance_resolved_team_sides": int(travel_resolved),
            "unique_venue_club_count": len(club_resolutions),
            "club_city_resolved_count": int(
                sum(
                    bool(value.get("resolved"))
                    for value in club_resolutions.values()
                )
            ),
            "city_coordinate_resolved_count": int(
                sum(
                    bool(
                        value.get("city_coordinate")
                        and value["city_coordinate"].get("resolved")
                    )
                    for value in club_resolutions.values()
                )
            ),
            "unresolved_clubs": unresolved_clubs,
            "unresolved_cities": unresolved_cities,
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
            "distance_summary_km": (
                None
                if not distances
                else {
                    "count": len(distances),
                    "mean": float(pd.Series(distances).mean()),
                    "median": float(pd.Series(distances).median()),
                    "max": max(distances),
                    "zero_or_near_zero_le_5km": int(
                        sum(value <= 5.0 for value in distances)
                    ),
                }
            ),
            "club_resolutions": club_resolutions,
            "rows": team_sides,
        }
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
