from pathlib import Path

import pandas as pd
import pytest

from prospective_availability_features import build_availability_features
from prospective_availability_provider import ProviderContractError, resolve_league
from prospective_availability_snapshot import match_provider_fixture, normalize_poll


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
    def raise_for_status(self):
        return None
    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payload):
        self.payload = payload
        self.calls = []
    def get(self, url, headers, params, timeout):
        self.calls.append((url, headers, params, timeout))
        return FakeResponse(self.payload)


def league_payload(league_id=135, injuries=True):
    return {
        "errors": {},
        "response": [
            {
                "league": {"id": league_id, "name": "Serie A"},
                "country": {"name": "Italy"},
                "seasons": [{"year": 2026, "coverage": {"injuries": injuries}}],
            }
        ],
    }


def provider_fixture(home="Manchester City", away="Arsenal", fixture_id=77):
    return {
        "fixture": {"id": fixture_id, "date": "2026-09-12T14:00:00+00:00"},
        "teams": {
            "home": {"id": 1, "name": home},
            "away": {"id": 2, "name": away},
        },
    }


def canonical_fixture():
    return {
        "league": "EPL",
        "home_team": "Man City",
        "away_team": "Arsenal",
        "commence_time_utc": "2026-09-12T14:00:00Z",
    }


def test_serie_a_id_is_resolved_live_and_coverage_is_required():
    session = FakeSession(league_payload())
    resolved = resolve_league(session, "secret", "SERIE_A", 2026)
    assert resolved.provider_league_id == 135
    assert session.calls[0][2] == {"country": "Italy", "season": 2026}
    assert session.calls[0][1]["x-apisports-key"] == "secret"

    with pytest.raises(ProviderContractError, match="coverage.injuries"):
        resolve_league(FakeSession(league_payload(injuries=False)), "secret", "SERIE_A", 2026)


def test_fixture_matching_is_alias_aware_and_fail_closed_on_ambiguity():
    canonical = canonical_fixture()
    fixture = provider_fixture()
    matched = match_provider_fixture(
        canonical,
        [fixture],
        aliases={"Manchester City": "Man City"},
    )
    assert matched["fixture"]["id"] == 77
    with pytest.raises(ValueError, match="must be unique"):
        match_provider_fixture(
            canonical,
            [fixture, provider_fixture(fixture_id=78)],
            aliases={"Manchester City": "Man City"},
        )


def test_zero_item_poll_is_retained_and_post_kickoff_poll_is_rejected():
    poll, observations = normalize_poll(
        canonical_row=canonical_fixture(),
        provider_fixture=provider_fixture(),
        injury_payload={"errors": {}, "response": []},
        observed_at_utc="2026-09-12T10:00:00Z",
    )
    assert poll["item_count"] == 0
    assert observations.empty
    with pytest.raises(ValueError, match="before kickoff"):
        normalize_poll(
            canonical_row=canonical_fixture(),
            provider_fixture=provider_fixture(),
            injury_payload={"errors": {}, "response": []},
            observed_at_utc="2026-09-12T14:00:00Z",
        )


def test_snapshot_rows_use_canonical_team_side_and_information_time():
    injury = {
        "errors": {},
        "response": [
            {
                "team": {"id": 1, "name": "Manchester City"},
                "player": {"id": 99, "name": "Player A", "type": "Missing Fixture", "reason": "Ankle Injury"},
            }
        ],
    }
    poll, observations = normalize_poll(
        canonical_row=canonical_fixture(),
        provider_fixture=provider_fixture(),
        injury_payload=injury,
        observed_at_utc="2026-09-12T10:00:00Z",
    )
    row = observations.iloc[0]
    assert row["team_name"] == "Man City"
    assert row["availability_type"] == "Injury"
    assert row["first_seen_timestamp_utc"] == pd.Timestamp("2026-09-12T10:00:00Z")
    assert row["poll_key"] == poll["poll_key"]


def test_features_use_latest_poll_not_later_information_and_reflect_disappearance():
    market = pd.DataFrame(
        [
            {
                **canonical_fixture(),
                "snapshot_time_utc": "2026-09-12T10:30:00Z",
            },
            {
                **canonical_fixture(),
                "snapshot_time_utc": "2026-09-12T12:30:00Z",
            },
        ]
    )
    polls = pd.DataFrame(
        [
            {**canonical_fixture(), "poll_key": "p1", "observed_at_utc": "2026-09-12T10:00:00Z"},
            {**canonical_fixture(), "poll_key": "p2", "observed_at_utc": "2026-09-12T12:00:00Z"},
            {**canonical_fixture(), "poll_key": "future", "observed_at_utc": "2026-09-12T13:00:00Z"},
        ]
    )
    observations = pd.DataFrame(
        [
            {"poll_key": "p1", "team_name": "Man City", "provider_player_id": 99, "availability_type": "Injury"},
            {"poll_key": "future", "team_name": "Arsenal", "provider_player_id": 100, "availability_type": "Suspension"},
        ]
    )
    features = build_availability_features(market, polls, observations)
    assert features.loc[0, "home_unavailable_count"] == 1
    assert features.loc[0, "availability_poll_key"] == "p1"
    # Player disappeared in p2: latest known full state is empty.
    assert features.loc[1, "home_unavailable_count"] == 0
    assert features.loc[1, "away_unavailable_count"] == 0
    assert features.loc[1, "availability_poll_key"] == "p2"


def test_migration_is_additive_insert_only_and_has_time_guards():
    sql = Path("supabase/migrations/202609030002_prospective_availability.sql").read_text().lower()
    assert "prospective_availability_polls" in sql
    assert "prospective_availability_observations" in sql
    assert "observed_at_utc < commence_time_utc" in sql
    assert "first_seen_timestamp_utc <= observed_at_utc" in sql
    assert " for insert " in sql
    assert " for select " in sql
    assert " for update " not in sql
    assert " for delete " not in sql


def test_collector_has_global_provider_preflight_before_any_league_collection():
    source = Path("prospective_availability_collector.py").read_text()
    preflight = "resolved = preflight_provider(session, api_key)"
    collection = "metrics = collect_league("
    assert preflight in source
    assert collection in source
    assert source.index(preflight) < source.index(collection)
    assert "resolved_league=resolved[league]" in source
