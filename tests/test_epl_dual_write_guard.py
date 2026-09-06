from types import SimpleNamespace

import pandas as pd
import pytest

import epl_dual_write_guard as guard
import persist_epl_market_observations as observation_mirror
import scheduled_epl_live_cycle as scheduled
from league_live_persistence import PersistenceConflictError
from league_prediction_ledger import PredictionLedgerConflictError
from league_runtime_config import EPL_RUNTIME_CONFIG


def shadow_frame():
    return pd.DataFrame(
        [
            {
                "league": "EPL",
                "event_id": "e1",
                "home_team": "Home",
                "away_team": "Away",
                "commence_time_utc": "2030-01-01T15:00:00Z",
                "snapshot_time_utc": "2030-01-01T10:00:00Z",
                "market_home_probability": 0.50,
                "market_draw_probability": 0.30,
                "market_away_probability": 0.20,
                "market_argmax": "H",
                "market_shadow_status": "OK",
                "market_only": True,
            }
        ]
    )


def test_prepare_dual_write_links_deterministic_observation_key(monkeypatch):
    shadow = shadow_frame()
    observations = observation_mirror.build_market_only_observations(shadow)

    monkeypatch.setattr(
        guard,
        "preflight_observations",
        lambda client, frame, config: {"present": 0, "missing": 1},
    )
    monkeypatch.setattr(
        guard,
        "preflight_predictions",
        lambda client, frame: {"present": 0, "missing": 1},
    )

    plan = guard.prepare_dual_write(
        object(),
        shadow,
        observations,
        EPL_RUNTIME_CONFIG,
    )

    assert len(plan.observations) == 1
    assert len(plan.predictions) == 1
    assert plan.observations.iloc[0]["observation_key"]
    assert (
        plan.predictions.iloc[0]["observation_key"]
        == plan.observations.iloc[0]["observation_key"]
    )
    assert plan.predictions.iloc[0]["prediction_mode"] == "MARKET_ONLY"
    assert bool(plan.predictions.iloc[0]["structural_applied"]) is False


def test_transient_observation_write_retries_once():
    calls = []

    def writer(client, frame, config):
        calls.append("call")
        if len(calls) == 1:
            raise RuntimeError("temporary transport failure")
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    result = guard.persist_observations_with_retry(
        object(),
        pd.DataFrame([{"x": 1}]),
        EPL_RUNTIME_CONFIG,
        persist_fn=writer,
    )

    assert len(calls) == 2
    assert result["inserted"] == 1


def test_observation_conflict_never_retries():
    calls = []

    def writer(client, frame, config):
        calls.append("call")
        raise PersistenceConflictError("immutable conflict")

    with pytest.raises(PersistenceConflictError):
        guard.persist_observations_with_retry(
            object(),
            pd.DataFrame([{"x": 1}]),
            EPL_RUNTIME_CONFIG,
            persist_fn=writer,
        )

    assert len(calls) == 1


def test_transient_prediction_write_retries_and_verifies(monkeypatch):
    calls = []
    predictions = pd.DataFrame([{"prediction_key": "p1"}])

    def writer(client, frame):
        calls.append("call")
        if len(calls) == 1:
            raise RuntimeError("temporary transport failure")
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    monkeypatch.setattr(
        guard,
        "preflight_predictions",
        lambda client, frame: {"present": len(frame), "missing": 0},
    )

    verified = guard.persist_predictions_with_retry(
        object(),
        predictions,
        persist_fn=writer,
    )

    assert len(calls) == 2
    assert verified == {"present": 1, "missing": 0}


def test_prediction_conflict_never_retries(monkeypatch):
    calls = []

    def writer(client, frame):
        calls.append("call")
        raise PredictionLedgerConflictError("immutable conflict")

    monkeypatch.setattr(
        guard,
        "preflight_predictions",
        lambda client, frame: pytest.fail("verification must not run"),
    )

    with pytest.raises(PredictionLedgerConflictError):
        guard.persist_predictions_with_retry(
            object(),
            pd.DataFrame([{"prediction_key": "p1"}]),
            persist_fn=writer,
        )

    assert len(calls) == 1


def test_scheduled_cycle_preflights_before_writes_and_restores(monkeypatch):
    events = []
    plan = SimpleNamespace(
        predictions=pd.DataFrame([{"prediction_key": "p1"}]),
        observation_present=0,
        observation_missing=1,
        prediction_present=0,
        prediction_missing=1,
    )

    original_observation_persist = scheduled.cycle.persistence.persist_observations
    original_ledger_persist = scheduled.cycle.persist_prediction_ledger

    monkeypatch.setattr(
        scheduled.cycle.observation_mirror,
        "load_market_shadow",
        lambda: shadow_frame(),
    )

    def prepare(client, shadow, frame, config):
        events.append("preflight")
        return plan

    def persist_observations(client, frame, config, *, persist_fn=None):
        events.append("observations")
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    def persist_predictions(client, frame, *, persist_fn=None):
        events.append("ledger")
        return {"present": 1, "missing": 0}

    monkeypatch.setattr(scheduled.dual_write_guard, "prepare_dual_write", prepare)
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "persist_observations_with_retry",
        persist_observations,
    )
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "preflight_observations",
        lambda client, frame, config: {"present": 1, "missing": 0},
    )
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "persist_predictions_with_retry",
        persist_predictions,
    )

    ledger_counts = iter((5, 6))
    monkeypatch.setattr(scheduled.cycle, "ledger_count", lambda: next(ledger_counts))

    def fake_run_cycle():
        scheduled.cycle.persistence.persist_observations(
            object(),
            pd.DataFrame([{"raw": True}]),
            EPL_RUNTIME_CONFIG,
        )
        before, after, metrics = scheduled.cycle.persist_prediction_ledger()
        assert (before, after) == (5, 6)
        assert metrics == {"inserted": 1, "unchanged": 0, "conflicts": 0}
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(scheduled.cycle, "run_cycle", fake_run_cycle)

    states = iter(((10, 7), (11, 7)))
    result = scheduled.run_scheduled_cycle(counts=lambda: next(states))

    assert result.ok is True
    assert events == ["preflight", "observations", "ledger"]
    assert scheduled.cycle.persistence.persist_observations is original_observation_persist
    assert scheduled.cycle.persist_prediction_ledger is original_ledger_persist
