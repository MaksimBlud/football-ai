from types import SimpleNamespace

import pandas as pd

import scheduled_epl_live_cycle as scheduled
from league_runtime_config import EPL_RUNTIME_CONFIG


def test_partial_first_write_uses_preflight_batch_metrics(monkeypatch):
    events = []
    plan = SimpleNamespace(
        predictions=pd.DataFrame([{"prediction_key": "p1"}]),
        observation_present=0,
        observation_missing=2,
        prediction_present=0,
        prediction_missing=1,
    )

    monkeypatch.setattr(
        scheduled.cycle.observation_mirror,
        "load_market_shadow",
        lambda: pd.DataFrame([{"placeholder": True}]),
    )
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "prepare_dual_write",
        lambda client, shadow, frame, config: plan,
    )

    # Simulate the final retry call reporting only the remaining row.  The
    # scheduled wrapper must ignore that partial-call metric and report the
    # whole preflight batch as inserted after read-after-write verification.
    def persist_observations(client, frame, config, *, persist_fn=None):
        events.append("observation-write")
        return {"inserted": 1, "unchanged": 1, "conflicts": 0}

    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "persist_observations_with_retry",
        persist_observations,
    )
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "preflight_observations",
        lambda client, frame, config: {"present": 2, "missing": 0},
    )
    monkeypatch.setattr(
        scheduled.dual_write_guard,
        "persist_predictions_with_retry",
        lambda client, frame: {"present": 1, "missing": 0},
    )

    ledger_counts = iter((5, 6))
    monkeypatch.setattr(scheduled.cycle, "ledger_count", lambda: next(ledger_counts))

    def fake_run_cycle():
        observation_metrics = scheduled.cycle.persistence.persist_observations(
            object(),
            pd.DataFrame([{"raw": 1}, {"raw": 2}]),
            EPL_RUNTIME_CONFIG,
        )
        assert observation_metrics == {
            "inserted": 2,
            "unchanged": 0,
            "conflicts": 0,
        }
        scheduled.cycle.persist_prediction_ledger()
        return SimpleNamespace(ok=True)

    monkeypatch.setattr(scheduled.cycle, "run_cycle", fake_run_cycle)

    states = iter(((10, 7), (12, 7)))
    result = scheduled.run_scheduled_cycle(counts=lambda: next(states))

    assert result.ok is True
    assert events == ["observation-write"]
