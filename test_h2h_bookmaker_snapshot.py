from copy import deepcopy

import pytest

from h2h_bookmaker_snapshot import (
    SCHEMA_VERSION,
    TABLE,
    build_h2h_bookmaker_rows,
    save_h2h_bookmaker_snapshots,
)


SNAPSHOT_TIME = "2026-09-15T12:00:00+00:00"


def _event(*, commence_time="2026-09-15T18:00:00Z"):
    return {
        "id": "event-1",
        "commence_time": commence_time,
        "home_team": "Home FC",
        "away_team": "Away FC",
        "bookmakers": [
            {
                "key": "book-b",
                "title": "Book B",
                "markets": [
                    {
                        "key": "h2h",
                        "last_update": "2026-09-15T11:58:00Z",
                        "outcomes": [
                            {"name": "Home FC", "price": 2.20},
                            {"name": "Draw", "price": 3.80},
                            {"name": "Away FC", "price": 3.90},
                        ],
                    }
                ],
            },
            {
                "key": "book-a",
                "title": "Book A",
                "markets": [
                    {
                        "key": "h2h",
                        "last_update": "2026-09-15T11:59:00Z",
                        "outcomes": [
                            {"name": "Home FC", "price": 2.00},
                            {"name": "Draw", "price": 4.00},
                            {"name": "Away FC", "price": 4.00},
                        ],
                    }
                ],
            },
            {
                "key": "incomplete",
                "title": "Incomplete Book",
                "markets": [
                    {
                        "key": "h2h",
                        "last_update": "2026-09-15T11:57:00Z",
                        "outcomes": [
                            {"name": "Home FC", "price": 2.10},
                            {"name": "Away FC", "price": 3.95},
                        ],
                    }
                ],
            },
        ],
    }


def test_build_preserves_complete_bookmaker_quotes_and_aggregate():
    rows = build_h2h_bookmaker_rows(
        [_event()],
        league="SERIE_A",
        snapshot_time_utc=SNAPSHOT_TIME,
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["league"] == "SERIE_A"
    assert row["event_id"] == "event-1"
    assert row["raw_bookmakers_count"] == 3
    assert row["accepted_bookmakers_count"] == 2
    assert row["snapshot_time_utc"] < row["kickoff_utc"]
    assert len(row["payload_sha256"]) == 64

    payload = row["payload"]
    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["research_only"] is True
    assert payload["provider_market_keys"] == ["h2h"]
    assert [book["bookmaker_key"] for book in payload["bookmakers"]] == [
        "book-a",
        "book-b",
    ]
    assert payload["aggregate"]["bookmakers_count"] == 2
    assert payload["aggregate"]["home_odds"] == pytest.approx(2.10)
    assert payload["aggregate"]["draw_odds"] == pytest.approx(3.90)
    assert payload["aggregate"]["away_odds"] == pytest.approx(3.95)


def test_payload_hash_is_invariant_to_provider_bookmaker_order():
    original = _event()
    reversed_event = deepcopy(original)
    reversed_event["bookmakers"] = list(reversed(reversed_event["bookmakers"]))

    left = build_h2h_bookmaker_rows(
        [original], league="SERIE_A", snapshot_time_utc=SNAPSHOT_TIME
    )[0]
    right = build_h2h_bookmaker_rows(
        [reversed_event], league="SERIE_A", snapshot_time_utc=SNAPSHOT_TIME
    )[0]

    assert left["snapshot_key"] == right["snapshot_key"]
    assert left["payload_sha256"] == right["payload_sha256"]
    assert left["payload"] == right["payload"]


def test_non_pre_kickoff_events_are_rejected():
    at_snapshot = _event(commence_time="2026-09-15T12:00:00Z")
    already_started = _event(commence_time="2026-09-15T11:59:59Z")

    assert build_h2h_bookmaker_rows(
        [at_snapshot, already_started],
        league="SERIE_A",
        snapshot_time_utc=SNAPSHOT_TIME,
    ) == []


def test_payload_contains_no_result_or_score_fields():
    payload = build_h2h_bookmaker_rows(
        [_event()], league="SERIE_A", snapshot_time_utc=SNAPSHOT_TIME
    )[0]["payload"]
    serialized_keys = set()

    def visit(value):
        if isinstance(value, dict):
            serialized_keys.update(value)
            for nested in value.values():
                visit(nested)
        elif isinstance(value, list):
            for nested in value:
                visit(nested)

    visit(payload)
    assert not serialized_keys.intersection(
        {"result", "home_goals", "away_goals", "scores", "completed"}
    )


class _Response:
    def __init__(self, data):
        self.data = data


class _Table:
    def __init__(self, sink):
        self.sink = sink
        self.rows = None

    def insert(self, rows):
        self.rows = rows
        self.sink.append(("insert", rows))
        return self

    def execute(self):
        return _Response(self.rows)


class _Client:
    def __init__(self):
        self.calls = []
        self.table_names = []

    def table(self, name):
        self.table_names.append(name)
        return _Table(self.calls)


def test_save_only_inserts_already_fetched_events():
    client = _Client()
    count = save_h2h_bookmaker_snapshots(
        [_event()],
        league="SERIE_A",
        snapshot_time_utc=SNAPSHOT_TIME,
        supabase_client=client,
    )

    assert count == 1
    assert client.table_names == [TABLE]
    assert len(client.calls) == 1
    action, rows = client.calls[0]
    assert action == "insert"
    assert rows[0]["payload"]["bookmakers"][0]["bookmaker_key"] == "book-a"


def test_invalid_snapshot_timestamp_fails_closed():
    with pytest.raises(ValueError, match="snapshot_time_utc"):
        build_h2h_bookmaker_rows(
            [_event()],
            league="SERIE_A",
            snapshot_time_utc="not-a-time",
        )
