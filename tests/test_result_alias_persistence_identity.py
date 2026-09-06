import pandas as pd
import pytest

import league_supabase_persistence as persistence
from league_live_persistence import PersistenceConflictError
from league_runtime_config import EPL_RUNTIME_CONFIG


class Response:
    def __init__(self, data=None):
        self.data = list(data or [])


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.payload = None
        self.filters = []

    def select(self, *_args, **_kwargs):
        return self

    def eq(self, field, value):
        self.filters.append((field, value))
        return self

    def order(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = dict(payload)
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.operation == "insert":
            rows.append(dict(self.payload))
            return Response([self.payload])
        data = [dict(row) for row in rows]
        for field, value in self.filters:
            data = [row for row in data if row.get(field) == value]
        return Response(data)


class Client:
    def __init__(self, result_rows):
        self.tables = {
            persistence.GENERIC_RESULTS_TABLE: [dict(row) for row in result_rows],
            persistence.GENERIC_OBSERVATION_TABLE: [],
        }

    def table(self, name):
        return Query(self, name)


def result_row(home_team="Brighton", *, home_goals=1, away_goals=1, result="D"):
    return {
        "league": "EPL",
        "season": "2026/2027",
        "match_date": "2026-09-05",
        "match_time": "15:00",
        "home_team": home_team,
        "away_team": "Leeds",
        "home_goals": home_goals,
        "away_goals": away_goals,
        "result": result,
        "source": "football-data.org",
        "source_competition": "PL",
    }


def test_legacy_alias_existing_row_prevents_duplicate_canonical_insert():
    client = Client([result_row("Brighton Hove")])
    incoming = pd.DataFrame([result_row("Brighton")])

    metrics = persistence.persist_results(client, incoming, EPL_RUNTIME_CONFIG)

    assert metrics == {"inserted": 0, "unchanged": 1, "conflicts": 0}
    assert len(client.tables[persistence.GENERIC_RESULTS_TABLE]) == 1


def test_alias_equivalent_existing_conflict_fails_closed():
    client = Client([result_row("Brighton Hove", home_goals=2, away_goals=1, result="H")])
    incoming = pd.DataFrame([result_row("Brighton")])

    with pytest.raises(PersistenceConflictError, match="Finished-result conflict"):
        persistence.persist_results(client, incoming, EPL_RUNTIME_CONFIG)

    assert len(client.tables[persistence.GENERIC_RESULTS_TABLE]) == 1


def test_conflicting_alias_equivalent_existing_history_fails_before_write():
    client = Client([
        result_row("Brighton Hove"),
        result_row("Brighton", home_goals=2, away_goals=1, result="H"),
    ])
    incoming = pd.DataFrame([result_row("Brighton")])

    with pytest.raises(
        PersistenceConflictError,
        match="Existing alias-equivalent finished-result conflict",
    ):
        persistence.persist_results(client, incoming, EPL_RUNTIME_CONFIG)

    assert len(client.tables[persistence.GENERIC_RESULTS_TABLE]) == 2
