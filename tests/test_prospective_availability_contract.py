from datetime import UTC, datetime

import pytest

from prospective_availability_contract import (
    ALLOWED_AVAILABILITY_TYPES,
    API_FOOTBALL_LEAGUE_IDS,
    AVAILABILITY_OBSERVATION_CONTRACT,
    CANONICAL_AVAILABILITY_FIELDS,
    PROVIDER,
    RESEARCH_LEAGUES,
    SOURCE_TIMESTAMP_KINDS,
    information_available_before_cutoff,
    validate_contract,
)


def test_contract_is_research_scoped_and_stable():
    validate_contract()

    assert PROVIDER == "API_FOOTBALL"
    assert RESEARCH_LEAGUES == ("EPL", "LA_LIGA", "SERIE_A")
    assert API_FOOTBALL_LEAGUE_IDS == {
        "EPL": 39,
        "LA_LIGA": 140,
        "SERIE_A": None,
    }
    assert AVAILABILITY_OBSERVATION_CONTRACT.endpoint == "/injuries"
    assert AVAILABILITY_OBSERVATION_CONTRACT.fixture_identity == (
        "league",
        "home_team",
        "away_team",
        "commence_time_utc",
    )


def test_contract_requires_information_time_fields():
    fields = set(CANONICAL_AVAILABILITY_FIELDS)

    assert {
        "observed_at_utc",
        "first_seen_timestamp_utc",
        "source_timestamp_utc",
        "source_timestamp_kind",
        "raw_payload_sha256",
    } <= fields
    assert SOURCE_TIMESTAMP_KINDS == (
        "provider_published",
        "collector_observed",
    )
    assert ALLOWED_AVAILABILITY_TYPES == ("Injury", "Suspension")


def test_first_seen_controls_prediction_eligibility():
    cutoff = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)

    assert information_available_before_cutoff(
        first_seen_timestamp_utc=datetime(2026, 9, 5, 11, 59, tzinfo=UTC),
        prediction_cutoff_utc=cutoff,
    )
    assert not information_available_before_cutoff(
        first_seen_timestamp_utc=datetime(2026, 9, 5, 12, 1, tzinfo=UTC),
        prediction_cutoff_utc=cutoff,
    )


def test_naive_and_aware_datetimes_are_not_silently_mixed():
    with pytest.raises(TypeError):
        information_available_before_cutoff(
            first_seen_timestamp_utc=datetime(2026, 9, 5, 11, 59),
            prediction_cutoff_utc=datetime(2026, 9, 5, 12, 0, tzinfo=UTC),
        )
