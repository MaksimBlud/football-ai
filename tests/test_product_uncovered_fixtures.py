"""Additional league fixtures are visible even if 1+ AI forecasts exist.

This is a read-only public schedule and can never mint model predictions, priced
markets or partner identities from untrusted fixture rows.
"""
from pathlib import Path
import re
import shutil
import subprocess
import pytest

INDEX = Path("static/index_v2.html")


def test_optional_schedule_is_loaded_even_when_predictions_are_present():
    html = INDEX.read_text(encoding="utf-8")
    assert "render();loadSchedule()" in html
    assert "if(!p.matches.length)loadSchedule()" not in html
    assert "uncoveredFixtures(data,state.payload)" in html
    assert "Другие ближайшие матчи АПЛ · пока без AI-прогноза" in html
    assert "Прогнозы модели и коэффициенты не подставляются из календаря" in html
    assert "source_mode==='espn_public_schedule'" in html
    assert "AI-прогноз отсутствует" in html
    assert "Коэффициенты букмекера отсутствуют" in html
    assert 'data.has_model_forecasts!==false||data.has_bookmaker_odds!==false' in html
    assert "m.league!=='EPL'" in html
    assert "data.fixtures.length>100" in html
    assert "m.model_forecast_status!=='not_available'" in html
    assert "m.bookmaker_odds_status!=='not_available'" in html
    assert "renderSchedule()" in html


def test_uncovered_fixture_dedup_is_by_exact_teams_and_utc_instant(tmp_path):
    if not shutil.which("node"):
        pytest.skip("Node unavailable")
    html=INDEX.read_text(encoding="utf-8")
    helpers=re.search(r"function scheduleMatchIdentity\(.*?(?=function renderSchedule\()",html,re.S)
    assert helpers
    script=helpers.group(0)+r"""
const assert=require('node:assert/strict');
Date.now=()=>Date.parse('2026-10-12T12:00:00Z');
const represented={
    match:{commence_time_utc:'2026-10-19T19:00:00+00:00',
           home_team:'Manchester City',away_team:'Chelsea'}
};
const fixtures=[
    {schedule_id:'espn:DIFFERENT-ID',kickoff_utc:'2026-10-19T20:00:00+01:00',
        home_team:'Manchester City',away_team:'Chelsea'},
    {schedule_id:'espn:NEW-1',kickoff_utc:'2026-10-19T17:00:00Z',
        home_team:'Brighton',away_team:'Arsenal'},
    {schedule_id:'espn:NEW-2',kickoff_utc:'2026-10-19T17:00:00+00:00',
        home_team:'Brighton',away_team:'Arsenal'},
    {schedule_id:'espn:NEW-3',kickoff_utc:'2026-10-19T19:00:00Z',
        home_team:'Chelsea',away_team:'Manchester City'},
    {schedule_id:'espn:OLD',kickoff_utc:'2026-10-11T12:00:00Z',
        home_team:'Everton',away_team:'Wolves'},
    {schedule_id:'espn:INVALID',kickoff_utc:'2026-10-20T20:00:00',
        home_team:'Leeds',away_team:'Villa'},
    {schedule_id:'espn:BAD',kickoff_utc:'2026-10-20T20:00:00Z',
        home_team:'Leeds',away_team:'Leeds'},
];
const data={fixtures};
assert.equal(scheduleMatchIdentity('2026-10-19T19:00:00Z','Man City','Chelsea')===scheduleMatchIdentity('2026-10-19T19:00:00Z','Manchester City','Chelsea'),false);
assert.equal(scheduleMatchIdentity('2026-10-19T20:00:00+01:00','Manchester City','Chelsea'),scheduleMatchIdentity('2026-10-19T19:00:00Z','Manchester City','Chelsea'));
assert.equal(scheduleMatchIdentity('2026-10-19T19:00:00','Manchester City','Chelsea'),null);
let extra=uncoveredFixtures(data,{matches:[represented]});
assert.deepEqual(extra.map(x=>x.schedule_id),['espn:NEW-1','espn:NEW-3']);
assert.deepEqual(uncoveredFixtures(data,{matches:[]}).map(x=>x.schedule_id),
    ['espn:DIFFERENT-ID','espn:NEW-1','espn:NEW-3']);
assert.deepEqual(uncoveredFixtures(data,null).map(x=>x.schedule_id),
    ['espn:DIFFERENT-ID','espn:NEW-1','espn:NEW-3']);
assert.deepEqual(uncoveredFixtures({fixtures:[]},{matches:[represented]}),[]);
assert.deepEqual(uncoveredFixtures({fixtures:null},{matches:[represented]}),[]);
"""
    f=tmp_path/"schedule_uncovered.js"
    f.write_text(script,encoding="utf-8")
    proc=subprocess.run(["node",str(f)],capture_output=True,text=True,timeout=10)
    assert proc.returncode==0,proc.stdout+proc.stderr


def test_schedule_never_becomes_a_fabricated_prediction():
    html=INDEX.read_text(encoding="utf-8")
    fragment=html.split("function renderSchedule(){",1)[1].split("async function loadSchedule()",1)[0]
    assert "state.payload.matches.length" not in fragment
    assert "extra.map(m=>" in fragment
    assert "m.match_date_uk" in fragment
    assert "m.match_time_uk" in fragment
    assert "m.home_team" in fragment and "m.away_team" in fragment
    for forbidden in ["fair_odds","bookmaker_odds", "expected_value","model_forecast","model_probability","main_forecast","value_signal"]:
        assert forbidden not in fragment
