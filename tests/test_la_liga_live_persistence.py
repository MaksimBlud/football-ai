from types import SimpleNamespace

import pandas as pd
import pytest

import la_liga_live_persistence as persistence


class DatabaseError(Exception):
    def __init__(
        self,
        message,
        *,
        code=None,
    ):
        super().__init__(message)
        self.code = code


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
        self.filters = {}

    def select(
        self,
        _columns,
    ):
        return self

    def eq(
        self,
        column,
        value,
    ):
        self.filters[
            column
        ] = value
        return self

    def limit(
        self,
        _value,
    ):
        return self

    def insert(
        self,
        payload,
    ):
        self.operation = "insert"
        self.payload = payload
        return self

    def execute(self):
        if (
            self.table_name
            in self.client.missing
        ):
            error = DatabaseError(
                "relation does not exist",
                code="42P01",
            )
            raise error

        table = self.client.rows.setdefault(
            self.table_name,
            [],
        )

        if self.operation == "insert":
            race = self.client.race.pop(
                self.table_name,
                None,
            )

            if race is not None:
                table.append(
                    race
                )
                raise DatabaseError(
                    "duplicate key",
                    code="23505",
                )

            table.append(
                self.payload.copy()
            )

            return SimpleNamespace(
                data=[
                    self.payload
                ]
            )

        matches = []

        for row in table:
            if all(
                row.get(key)
                == value
                for key, value
                in self.filters.items()
            ):
                matches.append(
                    row.copy()
                )

        return SimpleNamespace(
            data=matches
        )


class FakeClient:
    def __init__(
        self,
        *,
        missing=(),
    ):
        self.rows = {}
        self.missing = set(
            missing
        )
        self.race = {}

    def table(
        self,
        name,
    ):
        return Query(
            self,
            name,
        )


def observation(
    *,
    key="obs-1",
    shadow_home=0.50,
):
    return {
        "league":
            "LA_LIGA",
        "event_id":
            "event-1",
        "commence_time_utc":
            "2026-08-24T20:00:00+00:00",
        "home_team":
            "Barcelona",
        "away_team":
            "Valencia",
        "home_prior_matches":
            380,
        "away_prior_matches":
            380,
        "structural_ready":
            True,
        "structural_score":
            1.2,
        "correction_enabled":
            True,
        "realized_correction_weight":
            1.0,
        "market_home_probability":
            0.60,
        "market_draw_probability":
            0.23,
        "market_away_probability":
            0.17,
        "shadow_home_probability":
            shadow_home,
        "shadow_draw_probability":
            0.25,
        "shadow_away_probability":
            0.25,
        "market_argmax":
            "H",
        "shadow_argmax":
            "H",
        "prediction_source":
            "STRUCTURAL_EDGE_V2_SHADOW",
        "research_only":
            True,
        "snapshot_time_utc":
            "2026-08-24T10:00:00+00:00",
        "market_generated_at_utc":
            "2026-08-24T10:01:00+00:00",
        "recorded_at_utc":
            "2026-08-24T10:02:00+00:00",
        "pre_kickoff_valid":
            True,
        "observation_key":
            key,
    }


def result(
    *,
    home_goals=2,
    away_goals=1,
    match_result="H",
):
    return {
        "season":
            "2026-2027",
        "league":
            "LA_LIGA",
        "match_date":
            "2026-08-24",
        "match_time":
            "20:00",
        "home_team":
            "Barcelona",
        "away_team":
            "Valencia",
        "home_goals":
            home_goals,
        "away_goals":
            away_goals,
        "result":
            match_result,
        "source":
            "FOOTBALL_DATA_CSV",
        "source_competition":
            "SP1",
        "source_updated_at_utc":
            "2026-08-25T00:00:00+00:00",
    }


def test_schema_ready():
    client = FakeClient()

    state = (
        persistence
        .check_schema(
            client
        )
    )

    assert state.status == "PASS"


def test_missing_relation_is_wait():
    client = FakeClient(
        missing=[
            persistence.RESULTS_TABLE
        ]
    )

    state = (
        persistence
        .check_schema(
            client
        )
    )

    assert (
        state.status
        == "WAIT"
    )

    assert (
        state.detail
        == "DATABASE_SCHEMA_NOT_APPLIED"
    )


@pytest.mark.parametrize(
    "error",
    [
        ConnectionError(
            "network unreachable"
        ),
        DatabaseError(
            "permission denied",
            code="42501",
        ),
        DatabaseError(
            "authentication failure",
            code="PGRST301",
        ),
    ],
)
def test_real_database_errors_fail(
    error,
):
    state = (
        persistence
        .classify_database_error(
            error
        )
    )

    assert (
        state.status
        == "FAIL"
    )


def test_observation_insert_and_idempotence():
    client = FakeClient()

    first = (
        persistence
        .insert_observation(
            client,
            observation(),
        )
    )

    second = (
        persistence
        .insert_observation(
            client,
            observation(),
        )
    )

    assert first == "inserted"
    assert second == "unchanged"


def test_observation_conflict_rejected():
    client = FakeClient()

    persistence.insert_observation(
        client,
        observation(),
    )

    conflicting = observation(
        shadow_home=0.49
    )

    with pytest.raises(
        persistence.PersistenceConflictError
    ):
        persistence.insert_observation(
            client,
            conflicting,
        )


def test_observation_duplicate_race_is_idempotent():
    client = FakeClient()

    candidate = (
        persistence
        .observation_record(
            observation()
        )
    )

    client.race[
        persistence.OBSERVATIONS_TABLE
    ] = candidate

    state = (
        persistence
        .insert_observation(
            client,
            observation(),
        )
    )

    assert state == "unchanged"


def test_result_insert_and_idempotence():
    client = FakeClient()

    first = (
        persistence
        .insert_result(
            client,
            result(),
        )
    )

    second = (
        persistence
        .insert_result(
            client,
            result(),
        )
    )

    assert first == "inserted"
    assert second == "unchanged"


def test_result_conflict_rejected():
    client = FakeClient()

    persistence.insert_result(
        client,
        result(),
    )

    with pytest.raises(
        persistence.PersistenceConflictError
    ):
        persistence.insert_result(
            client,
            result(
                home_goals=0,
                away_goals=1,
                match_result="A",
            ),
        )


def test_result_duplicate_race_is_idempotent():
    client = FakeClient()

    candidate = (
        persistence
        .result_record(
            result()
        )
    )

    client.race[
        persistence.RESULTS_TABLE
    ] = candidate

    state = (
        persistence
        .insert_result(
            client,
            result(),
        )
    )

    assert state == "unchanged"


def test_hydrate_writes_authoritative_empty_mirrors(
    tmp_path,
):
    client = FakeClient()

    history = (
        tmp_path
        / "history.csv"
    )

    results = (
        tmp_path
        / "results.csv"
    )

    history.write_text(
        "stale\nvalue\n",
        encoding="utf-8",
    )

    results.write_text(
        "stale\nvalue\n",
        encoding="utf-8",
    )

    report = (
        persistence
        .hydrate_local_mirrors(
            client,
            history,
            results,
        )
    )

    assert report == {
        "observations": 0,
        "results": 0,
    }

    assert list(
        pd.read_csv(
            history
        ).columns
    ) == list(
        persistence
        .OBSERVATION_MIRROR_COLUMNS
    )

    assert list(
        pd.read_csv(
            results
        ).columns
    ) == list(
        persistence
        .RESULT_MIRROR_COLUMNS
    )
