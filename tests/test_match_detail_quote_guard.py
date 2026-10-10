"""Fail-closed match detail bookmaker quote contract for issue #582."""
from pathlib import Path
import re
import shutil
import subprocess

import pytest

MATCH = Path("static/match.html")


def test_match_detail_quotes_are_gated_by_verified_snapshot():
    html = MATCH.read_text(encoding="utf-8")
    assert "function marketVerified(m)" in html
    assert "const quoteVerified=marketVerified(m)" in html
    assert "valueHtml(item.value_signal,quoteVerified)" in html
    assert "selectionCard(s,one.readiness,one.display_selection&&s.code===one.display_selection.code,quoteVerified)" in html
    assert "selectionCard(s,goals.readiness,goals.display_selection&&s.code===goals.display_selection.code,quoteVerified)" in html
    assert "marketOk?dec(s.bookmaker_odds):'—'" in html
    assert "marketOk?ev(s.raw_expected_value):'—'" in html


def test_match_detail_quote_guard_runtime(tmp_path):
    if shutil.which("node") is None:
        pytest.skip("Node is unavailable")
    html = MATCH.read_text(encoding="utf-8")
    script = re.search(r"<script>(.*?)</script>", html, re.S)
    assert script, "Missing inline match script"
    helpers = script.group(1).split("async function load(){", 1)[0]
    source = helpers + """
const assert=require('node:assert/strict');
Date.now=()=>Date.parse('2026-10-10T12:00:00Z');
const valid={market_snapshot_status:'verified_prekickoff',market_snapshot_time_utc:'2026-10-10T10:00:00Z',commence_time_utc:'2026-10-11T15:00:00Z'};
assert.equal(marketVerified(valid),true);
for(const invalid of [
  {...valid,market_snapshot_status:'ambiguous_fixture'},
  {...valid,market_snapshot_time_utc:null},
  {...valid,market_snapshot_time_utc:'garbage'},
  {...valid,market_snapshot_time_utc:'2026-10-11T15:00:00Z'},
  {...valid,market_snapshot_time_utc:'2026-10-10T13:00:00Z'},
  {...valid,commence_time_utc:'2026-10-11T15:00:00'}
])assert.equal(marketVerified(invalid),false);
const s={label:'П1',probability:0.55,fair_odds:1.82,bookmaker_odds:2.1,raw_expected_value:0.155};
const v={status:'positive_raw_ev',selection:s};
assert.match(selectionCard(s,{status:'ready'},false,true),/2\\.10/);
assert.match(selectionCard(s,{status:'ready'},false,true),/\\+15\\.5%/);
assert.doesNotMatch(selectionCard(s,{status:'ready'},false,false),/2\\.10|15\\.5%/);
assert.match(selectionCard(s,{status:'ready'},false,false),/55\\.0%/);
assert.match(valueHtml(v,false),/Недоступен/);
assert.doesNotMatch(valueHtml(v,false),/2\\.10|15\\.5%/);
assert.match(valueHtml(v,true),/2\\.10/);
"""
    js = tmp_path / "match_quote_guard.js"
    js.write_text(source, encoding="utf-8")
    result = subprocess.run(["node", str(js)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
