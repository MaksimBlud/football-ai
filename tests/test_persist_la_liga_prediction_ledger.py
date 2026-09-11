from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

import catch_up_la_liga_prediction_ledger as catchup
import persist_la_liga_prediction_ledger as ledger
from la_liga_temporal_identity import TemporalObservationConflictError


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


def _temporal_observation(
    observation_key,
    persisted_at_utc,
    *,
    snapshot="2026-08-30T12:00:00+00:00",
    kickoff="2026-08-30T15:00:00+00:00",
    home_probability=0.50,
    structural_score=0.3,
):
    return {
        "observation_key": observation_key,
        "league": "LA_LIGA",
        "event_id": "laliga-event-1",
        "snapshot_time_utc": snapshot,
        "commence_time_utc": kickoff,
        "persisted_at_utc": persisted_at_utc,
        "payload": {
            "league": "LA_LIGA",
            "event_id": "laliga-event-1",
            "home_team": "Home",
            "away_team": "Away",
            "snapshot_time_utc": snapshot,
            "commence_time_utc": kickoff,
            "pre_kickoff_valid": True,
            "research_only": True,
            "market_home_probability": home_probability,
            "market_draw_probability": 0.30,
            "market_away_probability": 0.20,
            "market_argmax": "H",
            "structural_score": structural_score,
        },
    }


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


def test_transient_bridge_failure_retries_once_and_verifies(monkeypatch):
    client = _client()
    original = ledger.persist_predictions
    calls = []

    def flaky(client_arg, predictions):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("temporary transport failure")
        return original(client_arg, predictions)

    monkeypatch.setattr(ledger, "persist_predictions", flaky)

    result = ledger.persist_current_predictions(
        client,
        shadow=_shadow(),
    )

    assert len(calls) == 2
    assert result == {
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert ledger.ledger_count(client) == 1


def test_immutable_bridge_conflict_never_retries(monkeypatch):
    client = _client()
    calls = []

    def conflict(client_arg, predictions):
        calls.append(1)
        raise ledger.PredictionLedgerConflictError("immutable conflict")

    monkeypatch.setattr(ledger, "persist_predictions", conflict)

    with pytest.raises(ledger.PredictionLedgerConflictError):
        ledger.persist_current_predictions(
            client,
            shadow=_shadow(),
        )

    assert len(calls) == 1


def test_temporal_structural_drift_keeps_first_durable_observation():
    client = FakeClient(
        [
            _temporal_observation(
                "LA_LIGA:later-reconstruction",
                "2026-09-11T15:45:20+00:00",
                structural_score=0.826,
            ),
            _temporal_observation(
                "LA_LIGA:first-prospective",
                "2026-08-30T12:01:00+00:00",
                structural_score=0.326,
            ),
        ]
    )

    mapping = ledger.observation_key_map(client)

    assert mapping[("laliga-event-1", "2026-08-30T12:00:00+00:00")] == (
        "LA_LIGA:first-prospective"
    )


def test_temporal_market_drift_fails_closed():
    client = FakeClient(
        [
            _temporal_observation(
                "LA_LIGA:first-prospective",
                "2026-08-30T12:01:00+00:00",
                home_probability=0.50,
            ),
            _temporal_observation(
                "LA_LIGA:later-conflict",
                "2026-09-11T15:45:20+00:00",
                home_probability=0.51,
            ),
        ]
    )

    with pytest.raises(TemporalObservationConflictError, match="market payload"):
        ledger.observation_key_map(client)


def test_zero_cost_catchup_uses_latest_future_durable_snapshot_idempotently():
    client = FakeClient(
        [
            _temporal_observation(
                "LA_LIGA:older",
                "2026-08-30T11:01:00+00:00",
                snapshot="2026-08-30T11:00:00+00:00",
                kickoff="2026-08-30T15:00:00+00:00",
            ),
            _temporal_observation(
                "LA_LIGA:latest",
                "2026-08-30T12:01:00+00:00",
                snapshot="2026-08-30T12:00:00+00:00",
                kickoff="2026-08-30T15:00:00+00:00",
            ),
        ]
    )

    first = catchup.catch_up(
        client,
        as_of_utc="2026-08-30T10:00:00+00:00",
    )
    second = catchup.catch_up(
        client,
        as_of_utc="2026-08-30T10:00:00+00:00",
    )

    assert first == {
        "eligible": 1,
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert second == {
        "eligible": 1,
        "inserted": 0,
        "unchanged": 1,
        "conflicts": 0,
    }
    assert len(client.ledger_rows) == 1
    assert client.ledger_rows[0]["snapshot_time_utc"] == (
        "2026-08-30T12:00:00+00:00"
    )
    assert client.ledger_rows[0]["observation_key"] == "LA_LIGA:latest"


def test_zero_cost_catchup_ignores_finished_fixtures():
    client = FakeClient(
        [
            _temporal_observation(
                "LA_LIGA:finished",
                "2026-08-30T12:01:00+00:00",
                kickoff="2026-08-30T15:00:00+00:00",
            )
        ]
    )

    assert catchup.catch_up(
        client,
        as_of_utc="2026-08-30T16:00:00+00:00",
    ) == {
        "eligible": 0,
        "inserted": 0,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert client.ledger_rows == []


def test_catchup_workflow_cannot_access_odds_provider():
    text = Path(
        ".github/workflows/la-liga-prediction-ledger-catchup.yml"
    ).read_text(encoding="utf-8")

    assert "THE_ODDS_API_KEY" not in text
    assert "scheduled_la_liga_live_cycle.py" not in text
    assert "save_la_liga_odds" not in text
    assert "catch_up_la_liga_prediction_ledger.py" in text
    assert "SUPABASE_URL" in text
    assert "SUPABASE_KEY" in text
