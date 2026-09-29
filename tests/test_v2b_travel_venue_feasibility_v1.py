from __future__ import annotations

import io
import tarfile
import zipfile

import numpy as np
import pandas as pd
import pytest

import v2b_travel_venue_feasibility_v1 as mod


def test_nonleague_latest_host_uses_frozen_fixture_orientation():
    load = {
        "full_previous_match_date": "2026-09-16",
        "league_previous_match_date": "2026-09-13",
        "nonleague_events_14d": [
            {
                "date": "2026-09-16",
                "fixture_label": "Manchester United vs Brighton & Hove Albion",
            }
        ],
    }
    assert mod._nonleague_latest_host(load) == "Manchester United"


def test_nonleague_latest_host_is_none_when_league_is_latest():
    load = {
        "full_previous_match_date": "2026-09-13",
        "league_previous_match_date": "2026-09-13",
        "nonleague_events_14d": [],
    }
    assert mod._nonleague_latest_host(load) is None


def test_understat_schedule_parses_home_and_away():
    payload = {
        "dates": [
            {
                "datetime": "2026-09-12 15:00:00",
                "isResult": True,
                "h": {"title": "Arsenal"},
                "a": {"title": "Everton"},
            }
        ]
    }
    rows = mod._understat_schedule(payload)
    assert rows == [
        {
            "match_date": pd.Timestamp("2026-09-12"),
            "home": "Arsenal",
            "away": "Everton",
            "is_result": True,
        }
    ]


def test_league_latest_host_resolves_target_alias():
    schedules = {
        "EPL": [
            {
                "match_date": pd.Timestamp("2026-09-12"),
                "home": "Manchester City",
                "away": "Everton",
                "is_result": True,
            }
        ]
    }
    resolved, host = mod._league_latest_host(
        league="EPL",
        target_name="Man City",
        previous_date="2026-09-12",
        schedules=schedules,
    )
    assert resolved == "Manchester City"
    assert host == "Manchester City"


def test_extract_city_from_openfootball_club_line():
    line = "Arsenal FC, 1886, @ Emirates Stadium, London (Highbury)"
    assert mod._extract_city_from_club_line(line) == "London"


def test_openfootball_parser_keeps_alias_and_country():
    text = """Arsenal FC, 1886, @ Emirates Stadium, London (Highbury)
  | Arsenal | FC Arsenal
  | Arsenal Football Club
"""
    rows = mod._parse_club_file(
        text,
        country_code="GB",
        source_path="europe/england/eng.clubs.txt",
    )
    assert len(rows) == 1
    assert rows[0]["canonical"] == "Arsenal FC"
    assert rows[0]["city"] == "London"
    assert "Arsenal" in rows[0]["aliases"]


def test_openfootball_archive_parser_reads_country_directory():
    source = b"""Arsenal FC, 1886, @ Emirates Stadium, London
  | Arsenal
"""
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        info = tarfile.TarInfo(
            name="clubs-test/europe/england/eng.clubs.txt"
        )
        info.size = len(source)
        archive.addfile(info, io.BytesIO(source))

    records = mod.parse_openfootball_archive(buffer.getvalue())
    assert records[0]["country_code"] == "GB"
    assert records[0]["city"] == "London"


def test_club_resolver_uses_alias():
    records = [
        {
            "canonical": "Manchester City FC",
            "aliases": ["Manchester City", "Man City"],
            "city": "Manchester",
            "country_code": "GB",
            "source_path": "eng.clubs.txt",
        }
    ]
    result = mod.resolve_club_city(
        "Man City",
        mod.build_club_index(records),
    )
    assert result["resolved"] is True
    assert result["city"] == "Manchester"
    assert result["country_code"] == "GB"


def test_geonames_archive_and_alias_resolution():
    row = "\t".join(
        [
            "2643743",
            "London",
            "London",
            "Londres,Londra",
            "51.50853",
            "-0.12574",
            "P",
            "PPLC",
            "GB",
            "",
            "ENG",
            "",
            "",
            "",
            "7556900",
            "",
            "25",
            "Europe/London",
            "2026-01-01",
        ]
    )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, mode="w") as archive:
        archive.writestr("cities500.txt", row + "\n")

    frame = mod.parse_geonames_archive(buffer.getvalue())
    index = mod.build_city_index(frame)
    result = mod.resolve_city_coordinate(
        country_code="GB",
        city="Londres",
        index=index,
    )
    assert result["resolved"] is True
    assert result["name"] == "London"
    assert result["latitude"] == pytest.approx(51.50853)


def test_city_alias_maps_falmer_to_brighton():
    frame = pd.DataFrame(
        [
            {
                "geonameid": 2654710,
                "name": "Brighton",
                "asciiname": "Brighton",
                "alternatenames": "",
                "latitude": 50.82838,
                "longitude": -0.13947,
                "feature_class": "P",
                "feature_code": "PPL",
                "country_code": "GB",
                "cc2": "",
                "admin1_code": "ENG",
                "admin2_code": "",
                "admin3_code": "",
                "admin4_code": "",
                "population": 290395,
                "elevation": "",
                "dem": 0,
                "timezone": "Europe/London",
                "modification_date": "2026-01-01",
            }
        ]
    )
    index = mod.build_city_index(frame)
    result = mod.resolve_city_coordinate(
        country_code="GB",
        city="Falmer",
        index=index,
    )
    assert result["resolved"] is True
    assert result["lookup_city"] == "Brighton"


def test_haversine_zero_for_same_city():
    assert mod.haversine_km(
        51.5,
        -0.1,
        51.5,
        -0.1,
    ) == pytest.approx(0.0)


def test_haversine_is_symmetric_and_positive():
    london_to_madrid = mod.haversine_km(
        51.5074,
        -0.1278,
        40.4168,
        -3.7038,
    )
    madrid_to_london = mod.haversine_km(
        40.4168,
        -3.7038,
        51.5074,
        -0.1278,
    )
    assert london_to_madrid > 1000
    assert london_to_madrid == pytest.approx(madrid_to_london)


def test_source_contract_is_bulk_and_pinned():
    assert mod.OPENFOOTBALL_COMMIT == (
        "ae3800227c449447b3a337fc0aac79a8f02f4c8b"
    )
    assert "cities500.zip" in mod.GEONAMES_URL
    assert "wikidata" not in mod.GEONAMES_URL.lower()


def test_scope_is_exact_43_fixture_source_audit():
    assert mod.EXPECTED_FIXTURES == 43
    assert mod.EXPECTED_TEAM_SIDES == 86
    assert mod.SEASON == 2026
    assert mod.EXPERIMENT_ID == "V2B_TRAVEL_VENUE_FEASIBILITY_V1"


def test_elversberg_city_override_is_source_plumbing_only():
    result = mod.resolve_club_city("Elversberg", {})
    assert result["resolved"] is True
    assert result["city"] == "Spiesen-Elversberg"
    assert result["country_code"] == "DE"
    assert result["identity_override"] is True


def test_fc_cologne_alias_targets_openfootball_german_alias():
    records = [
        {
            "canonical": "1. FC Köln",
            "aliases": ["Köln", "FC Köln"],
            "city": "Köln",
            "country_code": "DE",
            "source_path": "de.clubs.txt",
        }
    ]
    result = mod.resolve_club_city(
        "FC Cologne",
        mod.build_club_index(records),
    )
    assert result["resolved"] is True
    assert result["canonical"] == "1. FC Köln"


def test_villarreal_city_alias_uses_vila_real():
    assert mod.CITY_NAME_ALIASES[("ES", "villarreal")] == "Vila-real"
