from types import SimpleNamespace

import pandas as pd
import pytest

import persist_la_liga_finished_results as bridge


def _frame(league="LA_LIGA"):
    return pd.DataFrame(
        [
            {
                "season": "2026-2027",
                "league": league,
                "match_date": "2026-08-29",
                "match_time": "20:00",
                "home_team": "Barcelona",
                "away_team": "Valencia",
                "home_goals": 2,
                "away_goals": 1,
                "result": "H",
                "source": "FOOTBALL_DATA_CSV",
                "source_competition": "SP1",
                "source_updated_at_utc": "2026-08-29T22:00:00+00:00",
            }
        ]
    )


def test_load_authoritative_results_accepts_la_liga(monkeypatch):
    monkeypatch.setattr(
        bridge.legacy,
        "fetch_results",
        lambda client: _frame(),
    )

    result = bridge.load_authoritative_results(SimpleNamespace())

    assert len(result) == 1
    assert set(result["league"]) == {"LA_LIGA"}


def test_load_authoritative_results_rejects_foreign_league(monkeypatch):
    monkeypatch.setattr(
        bridge.legacy,
        "fetch_results",
        lambda client: _frame("EPL"),
    )

    with pytest.raises(ValueError, match="foreign league"):
        bridge.load_authoritative_results(SimpleNamespace())


def test_bridge_uses_generic_immutable_persistence(monkeypatch):
    source = _frame()
    client = SimpleNamespace()
    seen = {}

    monkeypatch.setattr(
        bridge.legacy,
        "fetch_results",
        lambda supplied: source.copy(),
    )

    def persist(supplied_client, frame, config):
        seen["client"] = supplied_client
        seen["frame"] = frame.copy()
        seen["config"] = config
        return {"inserted": 1, "unchanged": 0, "conflicts": 0}

    monkeypatch.setattr(bridge.canonical, "persist_results", persist)

    metrics = bridge.persist_authoritative_results(client)

    assert metrics == {
        "input": 1,
        "inserted": 1,
        "unchanged": 0,
        "conflicts": 0,
    }
    assert seen["client"] is client
    assert seen["config"] is bridge.LA_LIGA_RUNTIME_CONFIG
    pd.testing.assert_frame_equal(seen["frame"], source)


def test_empty_authoritative_state_is_safe(monkeypatch):
    empty = _frame().iloc[0:0].copy()

    monkeypatch.setattr(
        bridge.legacy,
        "fetch_results",
        lambda client: empty.copy(),
    )
    monkeypatch.setattr(
        bridge.canonical,
        "persist_results",
        lambda client, frame, config: {
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
        },
    )

    assert bridge.persist_authoritative_results(SimpleNamespace()) == {
        "input": 0,
        "inserted": 0,
        "unchanged": 0,
        "conflicts": 0,
    }


def test_uncovered_input_metrics_are_rejected(monkeypatch):
    monkeypatch.setattr(
        bridge.legacy,
        "fetch_results",
        lambda client: _frame(),
    )
    monkeypatch.setattr(
        bridge.canonical,
        "persist_results",
        lambda client, frame, config: {
            "inserted": 0,
            "unchanged": 0,
            "conflicts": 0,
        },
    )

    with pytest.raises(RuntimeError, match="do not cover input"):
        bridge.persist_authoritative_results(SimpleNamespace())
