"""Browser-visible freshness regression: archived prices cannot imply an active value signal.

The threshold protects website presentation only, not model evaluation or
preregistered betting research. Saved odds remain labeled historical.
"""
from pathlib import Path
import re
import shutil
import subprocess
import pytest

ROOT = Path(__file__).resolve().parents[1]
INDEX = (ROOT / "static/index_v2.html").read_text(encoding="utf-8")
MATCH = (ROOT / "static/match.html").read_text(encoding="utf-8")


def node_run(source, tmp_path, name):
    if not shutil.which("node"):
        pytest.skip("Node unavailable")
    path = tmp_path / name
    path.write_text(source, encoding="utf-8")
    proc = subprocess.run(["node", str(path)], capture_output=True, text=True, timeout=15)
    assert proc.returncode == 0, proc.stdout + "\n" + proc.stderr


def test_list_prominently_marks_aged_odds_and_excludes_stale_value():
    assert "MAX_QUOTE_AGE_MS=24*60*60*1000" in INDEX
    assert "function marketQuoteFresh(m)" in INDEX
    assert "function quoteAgeHours(m)" in INDEX
    assert "function marketVerified(m)" in INDEX
    assert "function hasValue(m){return marketQuoteFresh(m.match)" in INDEX
    assert "const ok=marketQuoteFresh(m)" in INDEX
    assert "valueBox(marketQuoteFresh(meta)?m.value_signal:null)" in INDEX
    assert "if(!marketVerified(m))return false;" in INDEX
    assert "УСТАРЕВШИЙ архивный" in INDEX
    assert "АРХИВ · EV СКРЫТ" in INDEX
    assert "ВНИМАНИЕ: " in INDEX
    assert "Value / EV по ним скрыт" in INDEX
    assert "stale-warning" in INDEX
    assert "note.setAttribute('role',stale>0?'alert':'status')" in INDEX
    assert "marketVerified(m.match)" in INDEX  # historical paired/quoted provenance still works
    assert "function safeQuote(s,m){return marketVerified(m)?" in INDEX
    assert "24 часов" in INDEX


def test_match_detail_keeps_historical_odds_but_hides_raw_ev_for_stale():
    assert "MAX_QUOTE_AGE_MS=24*60*60*1000" in MATCH
    assert "function marketQuoteFresh(m)" in MATCH
    assert "if(marketVerified(m)&&!marketQuoteFresh(m))" in MATCH
    assert "Снимок БК устарел" in MATCH
    assert "АРХИВ · НЕТ VALUE" in MATCH
    assert "const valueFresh=priced&&marketQuoteFresh(m)" in MATCH
    assert "${valueFresh&&num(s.bookmaker_odds)" in MATCH
    assert "АРХИВ · EV СКРЫТ" in MATCH
    assert "ВНИМАНИЕ: букмекерские коэффициенты сохранены более 24 часов назад" in MATCH
    assert "verified?utcTimestamp(m.market_snapshot_time_utc):'Нет проверенного снимка'" in MATCH


def test_list_age_threshold_guards_value_runtime(tmp_path):
    source = re.search(r"const num=.*?(?=function forecastBox\()", INDEX, re.S)
    assert source
    script = source.group(0) + """
const assert=require('node:assert/strict');
Date.now=()=>Date.parse('2026-10-12T12:00:00Z');
const base={
 market_snapshot_status:'verified_prekickoff',
 market_snapshot_time_utc:'2026-10-09T15:25:57Z',
 commence_time_utc:'2026-10-19T19:00:00Z'
};
const fresh={...base,market_snapshot_time_utc:'2026-10-12T11:00:00Z'};
const future={...base,market_snapshot_time_utc:'2026-10-12T13:00:00Z'};
const boundary={...base,market_snapshot_time_utc:'2026-10-11T12:00:00Z'};
const stale={...base,market_snapshot_time_utc:'2026-10-11T11:59:59Z'};
assert.equal(marketVerified(base),true);       // historical pre-kickoff evidence remains
assert.equal(marketQuoteFresh(base),false);    // cannot use it for current EV
assert.equal(quoteAgeHours(base)>24,true);
assert.match(marketSourceLabel(base),/УСТАРЕВШИЙ архивный/);
assert.equal(safeQuote({bookmaker_odds:1.85},base),'1.85');
assert.equal(marketQuoteFresh(fresh),true);
assert.equal(marketQuoteFresh(boundary),true);
assert.equal(marketQuoteFresh(stale),false);
assert.equal(marketQuoteFresh(future),false);
assert.equal(marketQuoteFresh({...fresh, market_snapshot_status:'ambiguous_fixture'}),false);
assert.equal(marketQuoteFresh({...fresh, commence_time_utc:'not-a-time'}),false);
assert.equal(marketQuoteFresh({...fresh, market_snapshot_time_utc:null}),false);
const signal={status:'positive_raw_ev',selection:{bookmaker_odds:2,raw_expected_value:.12}};
const wrap=(m)=>({match:m,value_signal:signal,markets:{'1x2':{selections:[{bookmaker_odds:2}]}}});
assert.equal(hasValue(wrap(base)),false);
assert.equal(Boolean(hasValue(wrap(fresh))),true);
assert.equal(priced(wrap(base)),true); // still valid as historical quote
"""
    node_run(script, tmp_path, "list_freshness.js")


def test_detail_stale_value_is_hidden_but_probability_and_archive_remain(tmp_path):
    source = re.search(r"const \$=id=>.*?(?=function localKickoff\()", MATCH, re.S)
    assert source
    script = source.group(0) + """
const assert=require('node:assert/strict');
Date.now=()=>Date.parse('2026-10-12T12:00:00Z');
const stale={market_snapshot_status:'verified_prekickoff',market_snapshot_time_utc:'2026-10-09T15:25:57Z',commence_time_utc:'2026-10-19T19:00:00Z'};
const fresh={...stale,market_snapshot_time_utc:'2026-10-12T11:00:00Z'};
const quote={code:'HOME',label:'П1',probability:.51,fair_odds:1.96,bookmaker_odds:2.15,raw_expected_value:.0965};
const decision={status:'comparison_ready'};
const value={status:'positive_raw_ev',selection:quote,reason:'positive price'};
assert.equal(marketVerified(stale),true);
assert.equal(marketQuoteFresh(stale),false);
assert.match(valueHtml(value,stale),/Снимок БК устарел/);
assert.doesNotMatch(valueHtml(value,stale),/\\b9\\.65%\\b/);
const card=selectionCard(quote,decision,true,stale);
assert.match(card,/Букмекер · снимок/);
assert.match(card,/2.15/);  // the historical quote is displayed, explicitly flagged
assert.match(card,/АРХИВ · EV СКРЫТ/);
assert.match(card,/Raw EV · справочно<\\/span><span class="">—/);
const liveCard=selectionCard(quote,decision,true,fresh);
assert.doesNotMatch(liveCard,/АРХИВ · EV СКРЫТ/);
assert.match(liveCard,/\\+9.7%/);
assert.match(valueHtml(value,fresh),/VALUE · ДОП. СИГНАЛ/);
"""
    node_run(script, tmp_path, "detail_freshness.js")
