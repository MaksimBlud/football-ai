"""Inert source and timestamp contract for prospective availability research.

This module defines data semantics only. It does not fetch external data,
persist observations, train models, modify production artifacts, or activate
any live prediction path.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from fixture_identity import CANONICAL_FIXTURE_IDENTITY
from league_config import EPL, LA_LIGA, SERIE_A, validate_league_identifier


PROVIDER: Final[str] = "API_FOOTBALL"
PROVIDER_BASE_URL: Final[str] = "https://v3.football.api-sports.io"
INJURIES_ENDPOINT: Final[str] = "/injuries"
FIXTURES_ENDPOINT: Final[str] = "/fixtures"
LEAGUES_ENDPOINT: Final[str] = "/leagues"

# API-Football documents Premier League=39 and La Liga=140 as stable IDs.
# Serie A remains intentionally unresolved here until a live /leagues lookup
# is captured by the collector bootstrap. Do not guess or silently substitute.
API_FOOTBALL_LEAGUE_IDS: Final[dict[str, int | None]] = {
    EPL.identifier: 39,
    LA_LIGA.identifier: 140,
    SERIE_A.identifier: None,
}

RESEARCH_LEAGUES: Final[tuple[str, ...]] = tuple(API_FOOTBALL_LEAGUE_IDS)

CANONICAL_AVAILABILITY_FIELDS: Final[tuple[str, ...]] = (
    "provider",
    "provider_fixture_id",
    "provider_team_id",
    "provider_player_id",
    "league",
    "home_team",
    "away_team",
    "commence_time_utc",
    "team_name",
    "player_name",
    "availability_type",
    "reason",
    "source_timestamp_utc",
    "source_timestamp_kind",
    "observed_at_utc",
    "first_seen_timestamp_utc",
    "raw_payload_sha256",
)

SOURCE_TIMESTAMP_KINDS: Final[tuple[str, ...]] = (
    "provider_published",
    "collector_observed",
)

ALLOWED_AVAILABILITY_TYPES: Final[tuple[str, ...]] = (
    "Injury",
    "Suspension",
)


@dataclass(frozen=True)
class AvailabilityObservationContract:
    """Canonical information-time rules for one availability observation."""

    provider: str = PROVIDER
    endpoint: str = INJURIES_ENDPOINT
    fixture_identity: tuple[str, ...] = CANONICAL_FIXTURE_IDENTITY
    required_fields: tuple[str, ...] = CANONICAL_AVAILABILITY_FIELDS


def validate_contract() -> None:
    if PROVIDER != "API_FOOTBALL":
        raise ValueError("Unexpected prospective availability provider")

    if INJURIES_ENDPOINT != "/injuries":
        raise ValueError("Unexpected availability endpoint")

    for league in RESEARCH_LEAGUES:
        validate_league_identifier(league)

    if API_FOOTBALL_LEAGUE_IDS[EPL.identifier] != 39:
        raise ValueError("Unexpected API-Football EPL league id")

    if API_FOOTBALL_LEAGUE_IDS[LA_LIGA.identifier] != 140:
        raise ValueError("Unexpected API-Football La Liga league id")

    if API_FOOTBALL_LEAGUE_IDS[SERIE_A.identifier] is not None:
        raise ValueError("Serie A id must remain unresolved until live verification")

    required = set(CANONICAL_AVAILABILITY_FIELDS)
    for field in (
        "league",
        "home_team",
        "away_team",
        "commence_time_utc",
        "observed_at_utc",
        "first_seen_timestamp_utc",
        "source_timestamp_utc",
        "source_timestamp_kind",
    ):
        if field not in required:
            raise ValueError(f"Availability contract missing {field}")


def information_available_before_cutoff(
    *,
    first_seen_timestamp_utc,
    prediction_cutoff_utc,
) -> bool:
    """Return whether an observation was actually known by the collector.

    Research eligibility is controlled by first-seen time, not by injury
    start/end dates or other retrospective event-time fields.
    """

    return first_seen_timestamp_utc <= prediction_cutoff_utc


AVAILABILITY_OBSERVATION_CONTRACT = AvailabilityObservationContract()
validate_contract()
