from pathlib import Path

import pandas as pd

import save_rpl_odds_snapshot as collector


def aggregated():
    return {
        "event_id": "rpl-1",
        "commence_time": "2030-08-30T14:00:00Z",
        "home_team": "Zenit St Petersburg",
        "away_team": "Spartak Moscow",
        "bookmakers_count": 5,
        "home_odds": 1.8,
        "draw_odds": 3.5,
        "away_odds": 4.4,
        "home_probability": 0.55,
        "draw_probability": 0.28,
        "away_probability": 0.17,
    }


def test_rpl_collector_is_explicitly_eu_market_only_foundation(monkeypatch):
    assert collector.LEAGUE == "RPL"
    assert collector.SPORT_KEY == "soccer_russia_premier_league"
    assert collector.REGION == "eu"
    source = Path("save_rpl_odds_snapshot.py").read_text(encoding="utf-8")
    assert "football_model_xgboost_elo.pkl" not in source
    assert "joblib.load" not in source
    assert "Structural V2 used:" in source


def test_build_snapshot_rows_uses_rpl_identity(monkeypatch):
    monkeypatch.setattr(collector, "aggregate_event_h2h", lambda event: aggregated())
    frame = collector.build_snapshot_rows([{"id": "unused"}], "2030-08-29T12:00:00Z")
    assert len(frame) == 1
    assert frame.loc[0, "league"] == "RPL"
    assert frame.loc[0, "event_id"] == "rpl-1"
    assert frame.loc[0, "bookmakers_count"] == 5


def test_empty_or_unusable_events_produce_empty_contract(monkeypatch):
    monkeypatch.setattr(collector, "aggregate_event_h2h", lambda event: None)
    frame = collector.build_snapshot_rows([{"id": "unused"}], "2030-08-29T12:00:00Z")
    assert frame.empty
    assert list(frame.columns) == collector.DB_COLUMNS


def test_local_history_identity_includes_snapshot_and_event():
    old = pd.DataFrame([
        {
            **{column: None for column in collector.DB_COLUMNS},
            "league": "RPL",
            "snapshot_time_utc": "2030-08-29T10:00:00Z",
            "event_id": "rpl-1",
            "commence_time_utc": "2030-08-30T14:00:00Z",
            "home_team": "Zenit St Petersburg",
        }
    ])
    new = old.copy()
    new.loc[0, "home_odds"] = 1.9
    combined = collector.merge_local_history(old, new)
    assert len(combined) == 1
    assert combined.loc[0, "home_odds"] == 1.9


def test_non_rpl_payload_is_rejected():
    frame = pd.DataFrame([{column: None for column in collector.DB_COLUMNS}])
    frame.loc[0, "league"] = "EPL"
    frame.loc[0, "snapshot_time_utc"] = "2030-08-29T10:00:00Z"
    frame.loc[0, "event_id"] = "x"
    try:
        collector.build_db_rows(frame)
    except ValueError as exc:
        assert "non-RPL" in str(exc)
    else:
        raise AssertionError("non-RPL payload was accepted")


def test_supabase_upsert_uses_league_aware_conflict_target(monkeypatch):
    monkeypatch.setattr(collector, "aggregate_event_h2h", lambda event: aggregated())
    frame = collector.build_snapshot_rows([{"id": "unused"}], "2030-08-29T12:00:00Z")

    observed = {}

    class Response:
        data = [{"ok": True}]

    class Query:
        def upsert(self, rows, on_conflict):
            observed["rows"] = rows
            observed["on_conflict"] = on_conflict
            return self

        def execute(self):
            return Response()

    class Client:
        def table(self, name):
            observed["table"] = name
            return Query()

    count = collector.save_supabase(frame, supabase_client=Client())
    assert count == 1
    assert observed["table"] == "odds_snapshots"
    assert observed["on_conflict"] == "league,snapshot_time_utc,event_id"
    assert observed["rows"][0]["league"] == "RPL"
