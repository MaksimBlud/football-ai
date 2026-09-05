from datetime import datetime, timezone
import pandas as pd
import pytest

import scheduled_turkey_portugal_odds as sched
from persist_turkey_portugal_prediction_ledger import snapshots_to_market_shadow
from turkey_portugal_market_only import build_snapshot_rows, build_finished_row


def event(event_id="e1"):
    return {"id":event_id,"commence_time":"2026-09-10T18:00:00Z","home_team":"Home","away_team":"Away","bookmakers":[{"key":"b","title":"B","markets":[{"key":"h2h","outcomes":[{"name":"Home","price":2.0},{"name":"Draw","price":3.0},{"name":"Away","price":4.0}]}]}]}

@pytest.mark.parametrize("league",["TURKEY_SUPER_LIG","PRIMEIRA_LIGA"])
def test_snapshot_rows_are_market_only_ready(league):
    frame=build_snapshot_rows(league,[event()],"2026-09-05T10:00:00+00:00")
    assert len(frame)==1
    assert frame.iloc[0]["league"]==league
    shadow=snapshots_to_market_shadow(league,frame)
    assert shadow.iloc[0]["market_only"] in (True,"True")
    assert shadow.iloc[0]["market_shadow_status"]=="OK"
    assert shadow.iloc[0]["market_argmax"]=="H"


def test_cross_league_snapshot_rejected():
    frame=build_snapshot_rows("TURKEY_SUPER_LIG",[event()],"2026-09-05T10:00:00+00:00")
    with pytest.raises(ValueError):
        snapshots_to_market_shadow("PRIMEIRA_LIGA",frame)

@pytest.mark.parametrize("league",["TURKEY_SUPER_LIG","PRIMEIRA_LIGA"])
def test_finished_result_localizes_and_settles(league):
    e={"completed":True,"commence_time":"2026-09-05T18:00:00Z","home_team":"Home","away_team":"Away","scores":[{"name":"Home","score":"2"},{"name":"Away","score":"1"}]}
    row=build_finished_row(league,e)
    assert row["league"]==league
    assert row["result"]=="H"
    assert row["home_goals"]==2 and row["away_goals"]==1


def test_scheduler_blocks_paid_call_below_floor(monkeypatch):
    monkeypatch.setattr(sched,"zero_cost_quota",lambda:{"remaining":215,"last_cost":0})
    called=[]
    monkeypatch.setattr(sched,"collect_snapshot",lambda *a,**k:called.append(True))
    out=sched.run("TURKEY_SUPER_LIG")
    assert out["status"]=="BLOCKED_LOW_QUOTA"
    assert called==[]


def test_adaptive_intervals():
    assert sched.required_interval_hours(100)==12
    assert sched.required_interval_hours(50)==6
    assert sched.required_interval_hours(12)==4
    assert sched.required_interval_hours(2)==2
