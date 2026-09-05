from __future__ import annotations

from types import SimpleNamespace

import pandas as pd

import league_supabase_persistence as adapter
from league_runtime_config import LA_LIGA_RUNTIME_CONFIG as CONFIG


class Query:
    def __init__(self, client, table):
        self.client = client
        self.table_name = table
        self.filters = []
        self.orders = []
        self.window = None
        self.operation = "select"
        self.payload = None

    def select(self, *_args, **_kwargs):
        self.operation = "select"
        return self

    def eq(self, column, value):
        self.filters.append((column, value))
        return self

    def order(self, column, desc=False):
        self.orders.append((column, bool(desc)))
        return self

    def range(self, start, end):
        self.window = (start, end)
        self.client.ranges.append((self.table_name, start, end))
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = dict(payload)
        return self

    def execute(self):
        rows = self.client.tables.setdefault(self.table_name, [])
        if self.operation == "insert":
            rows.append(dict(self.payload))
            self.client.inserts.append((self.table_name, dict(self.payload)))
            return SimpleNamespace(data=[dict(self.payload)])

        result = [dict(row) for row in rows]
        for column, value in self.filters:
            result = [row for row in result if row.get(column) == value]
        # Apply stable sorts in reverse precedence so the first requested field
        # remains the primary key, matching PostgREST multi-order semantics.
        for column, desc in reversed(self.orders):
            result.sort(key=lambda row: str(row.get(column) or ""), reverse=desc)
        if self.window is not None:
            start, end = self.window
            result = result[start : end + 1]
        return SimpleNamespace(data=result)


class Client:
    def __init__(self, tables=None):
        self.tables = tables or {}
        self.ranges = []
        self.inserts = []

    def table(self, name):
        return Query(self, name)


def _result_row(index: int) -> dict:
    day = index % 28 + 1
    month = index % 9 + 1
    return {
        "league": "LA_LIGA",
        "season": "2026-2027",
        "match_date": f"2026-{month:02d}-{day:02d}",
        "home_team": f"Home {index:04d}",
        "away_team": f"Away {index:04d}",
        "home_goals": index % 4,
        "away_goals": (index + 1) % 4,
        "result": "H" if index % 4 > (index + 1) % 4 else "A",
    }


def test_generic_page_reader_reads_until_short_page():
    rows = [
        {"league": "LA_LIGA", "id": 1},
        {"league": "LA_LIGA", "id": 2},
        {"league": "LA_LIGA", "id": 3},
        {"league": "LA_LIGA", "id": 4},
        {"league": "LA_LIGA", "id": 5},
        {"league": "EPL", "id": 6},
    ]
    client = Client({"x": rows})

    fetched = adapter._fetch_league_rows(
        client,
        "x",
        "LA_LIGA",
        order_fields=("id",),
        page_size=2,
    )

    assert [row["id"] for row in fetched] == [1, 2, 3, 4, 5]
    assert client.ranges == [
        ("x", 0, 1),
        ("x", 2, 3),
        ("x", 4, 5),
    ]


def test_fetch_results_uses_multiple_postgrest_pages():
    rows = [_result_row(index) for index in range(1001)]
    client = Client({adapter.GENERIC_RESULTS_TABLE: rows})

    fetched = adapter.fetch_results(client, CONFIG)

    assert len(fetched) == 1001
    assert client.ranges == [
        (adapter.GENERIC_RESULTS_TABLE, 0, 999),
        (adapter.GENERIC_RESULTS_TABLE, 1000, 1999),
    ]


def test_persist_results_finds_identical_row_beyond_first_page():
    rows = [_result_row(index) for index in range(1000)]
    target = {
        "league": "LA_LIGA",
        "season": "2026-2027",
        "match_date": "2026-12-31",
        "home_team": "Target Home",
        "away_team": "Target Away",
        "home_goals": 2,
        "away_goals": 1,
        "result": "H",
    }
    rows.append(dict(target))
    client = Client({adapter.GENERIC_RESULTS_TABLE: rows})

    outcome = adapter.persist_results(client, pd.DataFrame([target]), CONFIG)

    assert outcome == {"inserted": 0, "unchanged": 1, "conflicts": 0}
    assert client.inserts == []
    assert (adapter.GENERIC_RESULTS_TABLE, 1000, 1999) in client.ranges


def test_fetch_observations_pages_and_flattens_payload():
    rows = []
    for index in range(1001):
        rows.append(
            {
                "observation_key": f"obs-{index:04d}",
                "league": "LA_LIGA",
                "event_id": f"event-{index:04d}",
                "snapshot_time_utc": f"2026-09-01T10:{index % 60:02d}:00+00:00",
                "commence_time_utc": "2026-09-01T18:00:00+00:00",
                "payload": {
                    "market_argmax": "H",
                    "shadow_argmax": "H",
                    "pre_kickoff_valid": True,
                    "research_only": True,
                },
            }
        )
    client = Client({adapter.GENERIC_OBSERVATION_TABLE: rows})

    fetched = adapter.fetch_observations(client, CONFIG)

    assert len(fetched) == 1001
    assert fetched["market_argmax"].eq("H").all()
    assert fetched["research_only"].eq(True).all()
    assert client.ranges == [
        (adapter.GENERIC_OBSERVATION_TABLE, 0, 999),
        (adapter.GENERIC_OBSERVATION_TABLE, 1000, 1999),
    ]
