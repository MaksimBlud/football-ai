from types import SimpleNamespace

import pandas as pd
import pytest

import persist_la_liga_prediction_ledger as ledger


class FakeQuery:
    def __init__(self, client, table_name):
        self.client = client
        self.table_name = table_name
        self.filters = {}
        self.insert_row = None
        self.want_count = False

    def select(self, *args, **kwargs):
        self.want_count = kwargs.get("count") == "exact"
        return self

    def eq(self, key, value):
        self.filters[key] = value
        return self

    def limit(self, value):
        return self

    def insert(self, row):
        self.insert_row = dict(row)
        return self

    def execute(self):
        if self.table_name == ledger.OBSERVATION_TABLE:
            rows = [
                row
                for row in self.client.observations
                if all(row.get(k) == v for k, v in self.filters.items())
            ]
            return SimpleNamespace(data=rows, count=len(rows))

        if self.table_name == ledger.TABLE:
            if self.insert_row is not None:
                self.client.ledger_rows.append(self.insert_row)
                return SimpleNamespace(data=[self.insert_row], count=None)

            rows = [
                row
                for row in self.client.ledger_rows
                if all(str(row.get(k)) == str(v) for k, v in self.filters.items())
            ]
            return SimpleNamespace(
                data=rows,
                count=len(rows) if self.want_count else None,
            )

        raise AssertionError(f"Unexpected table: {self.table_name}")


class FakeClient:
    def __init__(self, observations):
        self.observations = observations
        self.ledger_rows = []

    def table(self, name):
        return FakeQuery(self, name)


def _shadow(
    *,
    league="LA_LIGA",
    snapshot="2026-08-30T12:00:00+00:00",
    kickoff="2026-08-30T15:00:00+00:00",
):
    return pd.DataFrame(
        [
            {
                "league": league,
                "event_id": "laliga-event-1",
                "home_team": "Home",
                "away_team": "Away",
                "commence_time_utc": kickoff,
                "snapshot_time_utc": snapshot,
                "market_home_probability": 0.50,
                "market_draw_probability": 0.30,
                "market_away_probability": 0.20,
                "market_argmax": "H",
                "market_shadow_status": "OK",
                "market_only": True,
            }
        ]
    )


def _client(*, linked=True):
    observations = []
    if linked:
        observations.append(
            {
                "observation_key": "LA_LIGA:observation-1",
                "league": "LA_LIGA",
                "event_id": "laliga-event-1",
                "snapshot_time_utc": "2026-08-30T12:00:00+00:00",
            }
        )
    return FakeClient(observations)


def test_builds_linked_market_only_prediction():
    frame = ledger.build_current_predictions(
        _client(),
        shadow=_shadow(),
    )

    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["league"] == "LA_LIGA"
    assert row["prediction_mode"] == "MARKET_ONLY"
    assert row["structural_applied"] == False
    assert row["structural_status"] == "CALIBRATION_REQUIRED"
    assert row["observation_key"] == "LA_LIGA:observation-1"


def test_rejects_foreign_league_shadow():
    with pytest.raises(ValueError, match="Foreign league"):
        ledger.build_current_predictions(
            _client(),
            shadow=_shadow(league="EPL"),
        )


def test_rejects_post_kickoff_prediction():
    with pytest.raises(ValueError, match="pre-kickoff"):
        ledger.build_current_predictions(
            _client(),
            shadow=_shadow(
                snapshot="2026-08-30T16:00:00+00:00",
            ),
        )


def test_requires_link_to_immutable_la_liga_observation():
    with pytest.raises(RuntimeError, match="Unlinked"):
        ledger.build_current_predictions(
            _client(linked=False),
            shadow=_shadow(),
        )


def test_persistence_is_idempotent_and_immutable():
    client = _client()

    first = ledger.persist_current_predictions(
        client,
        shadow=_shadow(),
    )
    second = ledger.persist_current_predictions(
        client,
        shadow=_shadow(),
    )

    assert first == {
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert second == {
        "inserted": 0,
        "unchanged": 1,
        "conflicts": 0,
    }
    assert len(client.ledger_rows) == 1
    assert ledger.ledger_count(client) == 1
