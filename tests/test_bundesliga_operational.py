from datetime import datetime,timezone
import pandas as pd
import pytest
from bundesliga_runtime_config import BUNDESLIGA_RUNTIME_CONFIG
from football_data_current_results import PublicResultsSourceUnavailable
import scheduled_bundesliga_odds_snapshot as scheduler
import update_bundesliga_results as results
import persist_bundesliga_market_observations as observations


def test_runtime_contract():
    c=BUNDESLIGA_RUNTIME_CONFIG
    assert c.identity.identifier=="BUNDESLIGA"
    assert c.identity.timezone=="Europe/Berlin"
    assert c.identity.odds_sport_key=="soccer_germany_bundesliga"
    assert c.historical_source.competition_code=="D1"
    assert c.structural_v2.calibration_status=="CALIBRATION_REQUIRED"
    assert c.structural_v2.structural_alpha is None
    assert c.structural_v2.edge_threshold is None

def test_scheduler_intervals():
    assert scheduler.required_interval_hours(100)==12
    assert scheduler.required_interval_hours(48)==6
    assert scheduler.required_interval_hours(12)==4
    assert scheduler.required_interval_hours(2)==2

def test_scheduler_empty_state_collects():
    due,reason=scheduler.should_collect([],datetime(2026,8,29,tzinfo=timezone.utc))
    assert due and "NO_EXISTING" in reason

def test_finished_result_uses_berlin_date():
    event={"completed":True,"commence_time":"2026-08-29T22:30:00Z","home_team":"A","away_team":"B","scores":[{"name":"A","score":"2"},{"name":"B","score":"1"}]}
    row=results.build_finished_row(event)
    assert row["match_date"]=="2026-08-30"
    assert row["result"]=="H"

def test_transient_public_source_outage_is_explicit_and_does_not_persist(monkeypatch):
    def unavailable(_runtime):
        raise PublicResultsSourceUnavailable(
            url="https://www.football-data.co.uk/mmz4281/2627/D1.csv",
            status_code=503,
            attempts=3,
            detail="temporarily unavailable",
        )
    persist_calls=[]
    monkeypatch.setattr(results,"fetch_current_finished_results",unavailable)
    monkeypatch.setattr(results.persistence,"persist_results",lambda *_a,**_k: persist_calls.append(True))
    out=results.sync_results(write=True)
    assert out["league"]=="BUNDESLIGA"
    assert out["status"]=="SOURCE_UNAVAILABLE"
    assert out["http_status"]==503
    assert out["public_http_requests"]==3
    assert out["inserted"]==0
    assert out["conflicts"]==0
    assert out["writes_performed"] is False
    assert out["paid_provider_requests"]==0
    assert persist_calls==[]

def test_non_transient_results_error_still_fails_hard(monkeypatch):
    monkeypatch.setattr(results,"fetch_current_finished_results",lambda _runtime: (_ for _ in ()).throw(RuntimeError("schema drift")))
    with pytest.raises(RuntimeError,match="schema drift"):
        results.sync_results(write=True)

def test_market_observation_stays_market_only():
    frame=pd.DataFrame([{"league":"BUNDESLIGA","event_id":"e1","home_team":"A","away_team":"B","commence_time_utc":"2026-09-01T18:00:00Z","snapshot_time_utc":"2026-09-01T12:00:00Z","market_home_probability":0.5,"market_draw_probability":0.3,"market_away_probability":0.2,"market_argmax":"H","market_shadow_status":"OK","market_only":True}])
    out=observations.build_market_only_observations(frame)
    assert len(out)==1
    assert out.iloc[0]["prediction_source"]=="MARKET_ONLY"
    assert not bool(out.iloc[0]["structural_ready"])
    assert not bool(out.iloc[0]["correction_enabled"])
