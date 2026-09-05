from datetime import datetime,timezone
import pandas as pd
from eredivisie_runtime_config import EREDIVISIE_RUNTIME_CONFIG
import scheduled_eredivisie_odds_snapshot as scheduler
import update_eredivisie_results as results
import persist_eredivisie_market_observations as observations


def test_runtime_contract():
    c=EREDIVISIE_RUNTIME_CONFIG
    assert c.identity.identifier=="EREDIVISIE"
    assert c.identity.timezone=="Europe/Amsterdam"
    assert c.identity.odds_sport_key=="soccer_netherlands_eredivisie"
    assert c.historical_source.competition_code=="N1"
    assert c.historical_source.season_codes["2627"]=="2026-2027"
    assert c.finished_results_source.provider=="FOOTBALL_DATA_CSV"
    assert c.finished_results_source.competition_code=="N1"
    assert c.finished_results_source.season_code=="2627"
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

def test_finished_result_uses_amsterdam_date():
    event={"completed":True,"commence_time":"2026-08-29T22:30:00Z","home_team":"A","away_team":"B","scores":[{"name":"A","score":"2"},{"name":"B","score":"1"}]}
    row=results.build_finished_row(event)
    assert row["match_date"]=="2026-08-30"
    assert row["result"]=="H"

def test_market_observation_stays_market_only():
    frame=pd.DataFrame([{"league":"EREDIVISIE","event_id":"e1","home_team":"A","away_team":"B","commence_time_utc":"2026-09-01T18:00:00Z","snapshot_time_utc":"2026-09-01T12:00:00Z","market_home_probability":0.5,"market_draw_probability":0.3,"market_away_probability":0.2,"market_argmax":"H","market_shadow_status":"OK","market_only":True}])
    out=observations.build_market_only_observations(frame)
    assert len(out)==1
    assert out.iloc[0]["prediction_source"]=="MARKET_ONLY"
    assert not bool(out.iloc[0]["structural_ready"])
    assert not bool(out.iloc[0]["correction_enabled"])
