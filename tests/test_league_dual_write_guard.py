from dataclasses import replace

import pandas as pd
import pytest

import league_dual_write_guard as guard
import persist_rpl_market_observations as rpl_observations
from league_live_persistence import PersistenceConflictError
from league_prediction_ledger import PredictionLedgerConflictError
from league_runtime_config import RPL_RUNTIME_CONFIG


def shadow_frame():
    return pd.DataFrame([
        {
            "league": "RPL",
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
    ])


def test_prepare_plan_links_deterministic_observation_key(monkeypatch):
    shadow = shadow_frame()
    observations = rpl_observations.build_market_only_observations(shadow)
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
        object(), shadow, observations, RPL_RUNTIME_CONFIG
    )

    assert len(plan.observations) == len(plan.predictions) == 1
    assert plan.predictions.iloc[0]["observation_key"] == plan.observations.iloc[0]["observation_key"]
    assert plan.predictions.iloc[0]["prediction_mode"] == "MARKET_ONLY"
    assert bool(plan.predictions.iloc[0]["structural_applied"]) is False


def test_prepare_plan_uses_configured_league(monkeypatch):
    shadow = shadow_frame()
    observations = rpl_observations.build_market_only_observations(shadow)
    foreign = replace(
        RPL_RUNTIME_CONFIG,
        identity=replace(RPL_RUNTIME_CONFIG.identity, identifier="OTHER"),
    )
    with pytest.raises(ValueError):
        guard.prepare_dual_write(object(), shadow, observations, foreign)


def test_execute_retries_partial_observation_and_returns_whole_batch_metrics(monkeypatch):
    plan = guard.DualWritePlan(
        observations=pd.DataFrame([{"observation_key": "o1"}, {"observation_key": "o2"}]),
        predictions=pd.DataFrame([{"prediction_key": "p1"}]),
        observation_present=0,
        observation_missing=2,
        prediction_present=0,
        prediction_missing=1,
    )
    monkeypatch.setattr(guard, "prepare_dual_write", lambda *args, **kwargs: plan)

    observation_states = iter([
        {"present": 2, "missing": 0},
    ])
    prediction_states = iter([
        {"present": 1, "missing": 0},
    ])
    monkeypatch.setattr(guard, "preflight_observations", lambda *args: next(observation_states))
    monkeypatch.setattr(guard, "preflight_predictions", lambda *args: next(prediction_states))

    observation_calls = []
    prediction_calls = []

    def observation_writer(client, frame, config):
        observation_calls.append(1)
        if len(observation_calls) == 1:
            raise RuntimeError("transport after partial commit")
        return {"inserted": 1, "unchanged": 1, "conflicts": 0}

    def prediction_writer(client, frame):
        prediction_calls.append(1)
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    result = guard.execute_dual_write(
        object(),
        pd.DataFrame([{"shadow": True}]),
        pd.DataFrame([{"raw": 1}, {"raw": 2}]),
        RPL_RUNTIME_CONFIG,
        observation_writer=observation_writer,
        prediction_writer=prediction_writer,
    )

    assert len(observation_calls) == 2
    assert len(prediction_calls) == 1
    assert result.observation_metrics == {"inserted": 2, "unchanged": 0, "conflicts": 0}
    assert result.ledger_metrics == {"inserted": 1, "unchanged": 0, "conflicts": 0}


def test_execute_never_retries_immutable_conflicts(monkeypatch):
    plan = guard.DualWritePlan(
        observations=pd.DataFrame([{"observation_key": "o1"}]),
        predictions=pd.DataFrame([{"prediction_key": "p1"}]),
        observation_present=0,
        observation_missing=1,
        prediction_present=0,
        prediction_missing=1,
    )
    monkeypatch.setattr(guard, "prepare_dual_write", lambda *args, **kwargs: plan)
    calls = []

    def observation_writer(client, frame, config):
        calls.append(1)
        raise PersistenceConflictError("immutable")

    with pytest.raises(PersistenceConflictError):
        guard.execute_dual_write(
            object(), pd.DataFrame(), pd.DataFrame(), RPL_RUNTIME_CONFIG,
            observation_writer=observation_writer,
        )
    assert len(calls) == 1


def test_prediction_conflict_never_retries(monkeypatch):
    plan = guard.DualWritePlan(
        observations=pd.DataFrame([{"observation_key": "o1"}]),
        predictions=pd.DataFrame([{"prediction_key": "p1"}]),
        observation_present=1,
        observation_missing=0,
        prediction_present=0,
        prediction_missing=1,
    )
    monkeypatch.setattr(guard, "prepare_dual_write", lambda *args, **kwargs: plan)
    monkeypatch.setattr(guard, "preflight_observations", lambda *args: {"present": 1, "missing": 0})
    calls = []

    def prediction_writer(client, frame):
        calls.append(1)
        raise PredictionLedgerConflictError("immutable")

    with pytest.raises(PredictionLedgerConflictError):
        guard.execute_dual_write(
            object(), pd.DataFrame(), pd.DataFrame(), RPL_RUNTIME_CONFIG,
            observation_writer=lambda *args: {"inserted": 0, "unchanged": 1, "conflicts": 0},
            prediction_writer=prediction_writer,
        )
    assert len(calls) == 1
