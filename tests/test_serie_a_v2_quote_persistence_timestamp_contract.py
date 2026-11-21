"""Offline proof that the repository's Serie A odds writer leaves created_at to Postgres.

The live database has created_at DEFAULT now(), but no immutability trigger:
service_role can still override it. These tests pin only the trusted repository
collector path; they do not claim that the database column is tamper-proof.
"""
from types import SimpleNamespace

import pandas as pd

import save_serie_a_odds_snapshot as serie_a
from save_odds_snapshot import DB_COLUMNS


def _synthetic_frame():
    row = {column: None for column in DB_COLUMNS}
    row.update({
        "league": "SERIE_A",
        "snapshot_time_utc": "2026-11-20T03:00:00+00:00",
        "event_id": "synthetic-serie-a-event",
        "commence_time_utc": "2026-11-20T18:00:00+00:00",
        "home_team": "Synthetic Home",
        "away_team": "Synthetic Away",
        "bookmakers_count": 1,
        "home_odds": 2.0,
        "draw_odds": 3.2,
        "away_odds": 4.0,
        "home_probability": 0.5,
        "draw_probability": 0.3125,
        "away_probability": 0.1875,
        # Deliberately hostile caller-supplied timestamp: the collector must drop it.
        "created_at": "2000-01-01T00:00:00+00:00",
    })
    return pd.DataFrame([row])


def test_shared_odds_payload_contract_does_not_include_created_at():
    assert "created_at" not in DB_COLUMNS
    assert "created_at" not in serie_a.DB_COLUMNS


def test_serie_a_build_db_rows_drops_caller_supplied_created_at():
    rows = serie_a.build_db_rows(_synthetic_frame())

    assert len(rows) == 1
    assert rows[0]["league"] == "SERIE_A"
    assert "created_at" not in rows[0]


def test_serie_a_upsert_payload_leaves_created_at_to_database_default():
    class FakeTable:
        def __init__(self):
            self.rows = None
            self.conflict = None

        def upsert(self, rows, on_conflict):
            self.rows = rows
            self.conflict = on_conflict
            return self

        def execute(self):
            return SimpleNamespace(data=[{"id": 1}])

    class FakeClient:
        def __init__(self):
            self.table_name = None
            self.fake_table = FakeTable()

        def table(self, name):
            self.table_name = name
            return self.fake_table

    client = FakeClient()
    inserted = serie_a.save_supabase(_synthetic_frame(), supabase_client=client)

    assert inserted == 1
    assert client.table_name == "odds_snapshots"
    assert client.fake_table.conflict == serie_a.DB_CONFLICT_TARGET
    assert len(client.fake_table.rows) == 1
    assert "created_at" not in client.fake_table.rows[0]
    assert client.fake_table.rows[0]["event_id"] == "synthetic-serie-a-event"


def test_snapshot_builder_uses_only_the_shared_database_columns(monkeypatch):
    monkeypatch.setattr(
        serie_a,
        "aggregate_event_h2h",
        lambda _event: {
            "event_id": "synthetic-serie-a-event",
            "commence_time": "2026-11-20T18:00:00Z",
            "home_team": "Synthetic Home",
            "away_team": "Synthetic Away",
            "bookmakers_count": 1,
            "home_odds": 2.0,
            "draw_odds": 3.2,
            "away_odds": 4.0,
            "home_probability": 0.5,
            "draw_probability": 0.3125,
            "away_probability": 0.1875,
        },
    )

    frame = serie_a.build_snapshot_rows([{}], "2026-11-20T03:00:00Z")

    assert list(frame.columns) == DB_COLUMNS
    assert "created_at" not in frame.columns
