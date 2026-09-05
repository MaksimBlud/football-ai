from types import SimpleNamespace

import audit_turkey_portugal_team_identity as audit
from primeira_liga_runtime_config import PRIMEIRA_LIGA_RUNTIME_CONFIG


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def execute(self):
        return SimpleNamespace(data=self.rows)


class FakeSupabase:
    def __init__(self, rows):
        self.rows = rows

    def table(self, name):
        assert name == "odds_snapshots"
        return FakeQuery(self.rows)


def test_no_snapshots_is_explicit_blocker():
    football_data = {
        "season": "2026-2027",
        "source_rows": 20,
        "raw_teams": ["Benfica", "Porto"],
        "canonical_teams": ["Benfica", "Porto"],
    }
    snapshots = {
        "snapshot_rows": 0,
        "unique_events": 0,
        "raw_teams": [],
        "canonical_teams": [],
    }
    result = audit.compare_identity(PRIMEIRA_LIGA_RUNTIME_CONFIG, football_data, snapshots)
    assert result["status"] == "BLOCKED_NO_CANONICAL_SNAPSHOTS"
    assert result["provider_only_unmatched"] == []


def test_provider_subset_of_current_teams_is_ready():
    football_data = {
        "season": "2026-2027",
        "source_rows": 20,
        "raw_teams": ["Benfica", "Porto", "Sporting CP"],
        "canonical_teams": ["Benfica", "Porto", "Sporting CP"],
    }
    snapshots = {
        "snapshot_rows": 2,
        "unique_events": 1,
        "raw_teams": ["Benfica", "Porto"],
        "canonical_teams": ["Benfica", "Porto"],
    }
    result = audit.compare_identity(PRIMEIRA_LIGA_RUNTIME_CONFIG, football_data, snapshots)
    assert result["status"] == "READY"
    assert result["historical_not_observed_in_snapshots"] == ["Sporting CP"]


def test_unknown_provider_name_requires_alias():
    football_data = {
        "season": "2026-2027",
        "source_rows": 20,
        "raw_teams": ["Benfica", "Porto"],
        "canonical_teams": ["Benfica", "Porto"],
    }
    snapshots = {
        "snapshot_rows": 1,
        "unique_events": 1,
        "raw_teams": ["SL Benfica", "Porto"],
        "canonical_teams": ["SL Benfica", "Porto"],
    }
    result = audit.compare_identity(PRIMEIRA_LIGA_RUNTIME_CONFIG, football_data, snapshots)
    assert result["status"] == "ALIAS_REQUIRED"
    assert result["provider_only_unmatched"] == ["SL Benfica"]


def test_configured_alias_resolves_cross_source_name():
    aliases = {"SL Benfica": "Benfica"}
    assert audit._canonical("SL Benfica", aliases) == "Benfica"
    assert audit._canonical("Benfica", aliases) == "Benfica"


def test_snapshot_reader_uses_team_fields_and_deduplicates():
    rows = [
        {"event_id": "e1", "home_team": "Benfica", "away_team": "Porto"},
        {"event_id": "e1", "home_team": "Benfica", "away_team": "Porto"},
    ]
    result = audit.fetch_snapshot_teams(PRIMEIRA_LIGA_RUNTIME_CONFIG, FakeSupabase(rows))
    assert result["snapshot_rows"] == 2
    assert result["unique_events"] == 1
    assert result["raw_teams"] == ["Benfica", "Porto"]
