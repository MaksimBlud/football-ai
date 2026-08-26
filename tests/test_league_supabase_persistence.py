from __future__ import annotations

import pandas as pd
import pytest

import league_supabase_persistence as adapter

from league_live_persistence import (
    PersistenceConflictError,
)

from league_runtime_config import (
    LA_LIGA_RUNTIME_CONFIG,
)


CONFIG = LA_LIGA_RUNTIME_CONFIG


class Response:
    def __init__(self, data=None):
        self.data = (
            data
            if data is not None
            else []
        )


class Query:
    def __init__(
        self,
        client,
        table,
    ):
        self.client = client
        self.table_name = table
        self.operation = "select"
        self.payload = None
        self.filters = []

    def select(self, *_args, **_kwargs):
        self.operation = "select"
        return self

    def eq(self, column, value):
        self.filters.append(
            (
                column,
                value,
            )
        )
        return self

    def order(self, *_args, **_kwargs):
        return self

    def limit(self, *_args, **_kwargs):
        return self

    def insert(self, payload):
        self.operation = "insert"
        self.payload = dict(payload)
        return self

    def execute(self):
        if self.client.fail_tables.get(
            self.table_name
        ):
            raise RuntimeError(
                self.client.fail_tables[
                    self.table_name
                ]
            )

        rows = self.client.tables.setdefault(
            self.table_name,
            [],
        )

        if self.operation == "insert":
            rows.append(
                dict(
                    self.payload
                )
            )

            return Response(
                [
                    dict(
                        self.payload
                    )
                ]
            )

        result = [
            dict(row)
            for row in rows
        ]

        for column, value in self.filters:
            result = [
                row
                for row in result
                if row.get(column)
                == value
            ]

        return Response(
            result
        )


class FakeClient:
    def __init__(self):
        self.tables = {
            adapter.GENERIC_OBSERVATION_TABLE:
                [],
            adapter.GENERIC_RESULTS_TABLE:
                [],
        }

        self.fail_tables = {}

    def table(self, name):
        return Query(
            self,
            name,
        )


def observation_frame():
    return pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "event_id":
                    "event-1",
                "snapshot_time_utc":
                    "2026-08-26T10:00:00Z",
                "commence_time_utc":
                    "2026-08-26T18:00:00Z",
                "market_argmax":
                    "H",
                "shadow_argmax":
                    "H",
                "pre_kickoff_valid":
                    True,
                "research_only":
                    True,
            }
        ]
    )


def result_frame():
    return pd.DataFrame(
        [
            {
                "league":
                    "LA_LIGA",
                "season":
                    "2026-2027",
                "match_date":
                    "2026-08-26",
                "home_team":
                    "Getafe",
                "away_team":
                    "Sevilla",
                "home_goals":
                    2,
                "away_goals":
                    1,
                "result":
                    "H",
            }
        ]
    )


def test_schema_ready():
    client = FakeClient()

    state = adapter.check_schema(
        client
    )

    assert state.status == "PASS"
    assert (
        state.detail
        == "GENERIC_DATABASE_SCHEMA_READY"
    )


def test_schema_missing_is_wait():
    client = FakeClient()

    client.fail_tables[
        adapter.GENERIC_OBSERVATION_TABLE
    ] = "relation does not exist"

    state = adapter.check_schema(
        client
    )

    assert state.status == "WAIT"


def test_database_failure_is_fail():
    client = FakeClient()

    client.fail_tables[
        adapter.GENERIC_OBSERVATION_TABLE
    ] = "connection refused"

    state = adapter.check_schema(
        client
    )

    assert state.status == "FAIL"


def test_observation_insert_then_replay_is_idempotent():
    client = FakeClient()

    first = adapter.persist_observations(
        client,
        observation_frame(),
        CONFIG,
    )

    second = adapter.persist_observations(
        client,
        observation_frame(),
        CONFIG,
    )

    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["unchanged"] == 1


def test_observation_conflict_rejected():
    client = FakeClient()

    adapter.persist_observations(
        client,
        observation_frame(),
        CONFIG,
    )

    existing = client.tables[
        adapter.GENERIC_OBSERVATION_TABLE
    ][0]

    existing[
        "payload"
    ][
        "market_argmax"
    ] = "A"

    with pytest.raises(
        PersistenceConflictError,
    ):
        adapter.persist_observations(
            client,
            observation_frame(),
            CONFIG,
        )


def test_result_insert_then_replay_is_idempotent():
    client = FakeClient()

    first = adapter.persist_results(
        client,
        result_frame(),
        CONFIG,
    )

    second = adapter.persist_results(
        client,
        result_frame(),
        CONFIG,
    )

    assert first["inserted"] == 1
    assert second["inserted"] == 0
    assert second["unchanged"] == 1


def test_result_conflict_rejected():
    client = FakeClient()

    adapter.persist_results(
        client,
        result_frame(),
        CONFIG,
    )

    stored = client.tables[
        adapter.GENERIC_RESULTS_TABLE
    ][0]

    stored[
        "home_goals"
    ] = 9

    with pytest.raises(
        PersistenceConflictError,
    ):
        adapter.persist_results(
            client,
            result_frame(),
            CONFIG,
        )


def test_fetch_is_league_scoped():
    client = FakeClient()

    client.tables[
        adapter.GENERIC_RESULTS_TABLE
    ] = [
        {
            "league": "LA_LIGA",
            "season": "2026-2027",
            "match_date": "2026-08-26",
        },
        {
            "league": "EPL",
            "season": "2026-2027",
            "match_date": "2026-08-26",
        },
    ]

    result = adapter.fetch_results(
        client,
        CONFIG,
    )

    assert set(
        result["league"]
    ) == {
        "LA_LIGA",
    }


def test_observation_storage_record_matches_sql_columns():
    import league_live_persistence as core

    validated = core.validate_observations(
        observation_frame(),
        CONFIG,
    )

    record = (
        adapter
        .observation_storage_record(
            validated
            .iloc[0]
            .to_dict()
        )
    )

    assert set(
        record
    ) == set(
        adapter
        .OBSERVATION_STORAGE_COLUMNS
    )

    assert (
        record[
            "payload"
        ][
            "market_argmax"
        ]
        == "H"
    )

    assert (
        record[
            "payload"
        ][
            "shadow_argmax"
        ]
        == "H"
    )

    assert (
        record[
            "payload"
        ][
            "pre_kickoff_valid"
        ]
        is True
    )

    assert (
        record[
            "payload"
        ][
            "research_only"
        ]
        is True
    )


def test_observation_roundtrip_restores_runtime_columns():
    import league_live_persistence as core

    validated = core.validate_observations(
        observation_frame(),
        CONFIG,
    )

    stored = (
        adapter
        .observation_storage_record(
            validated
            .iloc[0]
            .to_dict()
        )
    )

    restored = (
        adapter
        .observation_runtime_record(
            stored
        )
    )

    assert (
        restored[
            "market_argmax"
        ]
        == "H"
    )

    assert (
        restored[
            "shadow_argmax"
        ]
        == "H"
    )

    assert (
        restored[
            "pre_kickoff_valid"
        ]
        is True
    )

    assert (
        restored[
            "research_only"
        ]
        is True
    )


def test_real_insert_payload_contains_no_flat_non_schema_columns():
    client = FakeClient()

    adapter.persist_observations(
        client,
        observation_frame(),
        CONFIG,
    )

    stored = client.tables[
        adapter.GENERIC_OBSERVATION_TABLE
    ][0]

    assert set(
        stored
    ) == set(
        adapter
        .OBSERVATION_STORAGE_COLUMNS
    )

    assert (
        "market_argmax"
        not in stored
    )

    assert (
        stored[
            "payload"
        ][
            "market_argmax"
        ]
        == "H"
    )


def test_fetch_observations_flattens_payload():
    client = FakeClient()

    adapter.persist_observations(
        client,
        observation_frame(),
        CONFIG,
    )

    fetched = (
        adapter.fetch_observations(
            client,
            CONFIG,
        )
    )

    assert len(
        fetched
    ) == 1

    assert (
        fetched
        .iloc[0][
            "market_argmax"
        ]
        == "H"
    )

    assert bool(
        fetched
        .iloc[0][
            "research_only"
        ]
    )


def test_python_date_is_json_safe():
    from datetime import date

    result = adapter._normalize_record(
        {
            "match_date":
                date(
                    2026,
                    8,
                    26,
                ),
        }
    )

    assert (
        result[
            "match_date"
        ]
        == "2026-08-26"
    )


def test_result_insert_payload_is_json_safe():
    import json

    client = FakeClient()

    adapter.persist_results(
        client,
        result_frame(),
        CONFIG,
    )

    stored = client.tables[
        adapter.GENERIC_RESULTS_TABLE
    ][0]

    encoded = json.dumps(
        stored
    )

    assert encoded
    assert (
        stored[
            "match_date"
        ]
        == "2026-08-26"
    )


def test_observation_payload_datetime_representation_is_canonical():
    payload_space = {
        "market_generated_at_utc":
            "2026-08-23 07:31:20.043389+00:00",
        "recorded_at_utc":
            "2026-08-23 15:37:20.071911+00:00",
    }

    payload_t = {
        "market_generated_at_utc":
            "2026-08-23T07:31:20.043389+00:00",
        "recorded_at_utc":
            "2026-08-23T15:37:20.071911+00:00",
    }

    assert (
        adapter._canonical_observation_payload(
            payload_space
        )
        ==
        adapter._canonical_observation_payload(
            payload_t
        )
    )

    canonical = (
        adapter._canonical_observation_payload(
            payload_space
        )
    )

    assert (
        canonical[
            "market_generated_at_utc"
        ]
        ==
        "2026-08-23T07:31:20.043389+00:00"
    )

    assert (
        canonical[
            "recorded_at_utc"
        ]
        ==
        "2026-08-23T15:37:20.071911+00:00"
    )
