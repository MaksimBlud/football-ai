from pathlib import Path


INDEX_PATH = Path("static/index_v2.html")
MATCH_PATH = Path("static/match.html")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_match_list_consumes_unified_server_contract():
    html = read(INDEX_PATH)

    assert "fetch('/product-market-view'" in html
    assert "/upcoming-round-predictions" not in html
    assert "/upcoming-matches" not in html
    assert "product-market-view.v1" in html


def test_match_detail_consumes_same_unified_contract():
    html = read(MATCH_PATH)

    assert "fetch(`/product-market-view/${encodeURIComponent(id)}`" in html
    assert "/upcoming-round-match/" not in html
    assert "/upcoming-matches" not in html
    assert "product-market-view.v1" in html


def test_browser_does_not_recalculate_fair_odds_or_expected_value():
    combined = read(INDEX_PATH) + read(MATCH_PATH)

    forbidden = (
        "function fairOdds",
        "const fairOdds",
        "function expectedValue",
        "const expectedValue",
        "probability * bookmaker",
        "probability*bookmaker",
        "p * odds - 1",
        "p*odds-1",
    )

    for fragment in forbidden:
        assert fragment not in combined


def test_forecast_and_value_are_visibly_separate():
    index = read(INDEX_PATH)
    detail = read(MATCH_PATH)

    assert "Главный прогноз модели" in index
    assert "Value / EV (доп.)" in index
    assert "m.main_forecast" in index
    assert "m.value_signal" in index
    assert "forecastBox(m.main_forecast)" in index
    assert "valueBox(marketVerified(meta)?m.value_signal:null)" in index
    assert "Главный выбор модели" not in index

    assert "Главный прогноз модели" in detail
    assert "Value / EV · дополнительный показатель" in detail
    assert "item.main_forecast" in detail
    assert "item.value_signal" in detail
    assert "никогда не переопределяет" in detail


def test_value_filter_is_not_named_as_forecast():
    html = read(INDEX_PATH)

    assert "Есть value-сигнал" in html
    assert "Расчётных кандидатов" not in html
    assert "Value-сигналов" in html


def test_list_links_to_stable_server_match_card():
    html = read(INDEX_PATH)

    assert 'data-match-id="${esc(meta.product_match_id)}"' in html
    assert "/match?id=${encodeURIComponent(row.dataset.matchId)}" in html
    assert "row.dataset.index" not in html


def test_ui_copy_uses_decision_tier_before_cross_market_probability():
    index = read(INDEX_PATH)
    detail = read(MATCH_PATH)
    combined = index + detail

    assert "decision tier" in index
    assert "decision tier" in detail
    assert "Главный прогноз определяется только вероятностью модели" not in combined
    assert "Value / raw EV" in combined


def test_mobile_layout_has_real_cards_not_horizontal_1580px_table():
    html = read(INDEX_PATH)
    assert 'id="mobile-match-list"' in html
    assert 'class="mobile-match-card" role="listitem"' in html
    assert '@media(max-width:900px)' in html
    assert '.table-wrap{display:none}' in html
    assert '.mobile-match-list{display:grid' in html
    assert 'rows.map(mobileCardHtml)' in html


def test_mobile_market_prices_and_probabilities_use_server_selections_only():
    html = read(INDEX_PATH)
    assert "const one=m.markets['1x2'];" in html
    assert "f.status==='model_forecast'" in html
    assert "pct(f.selection.probability)" in html
    assert "pct(s.probability)" in html
    assert "dec(s.bookmaker_odds)" in html
    assert "bookmaker_odds)||1" not in html
    assert 'Raw EV не доказывает прибыльность.' in html


def test_mobile_navigation_is_keyboard_accessible_and_uses_stable_match_id():
    html = read(INDEX_PATH)
    assert 'const url=' in html
    assert "encodeURIComponent(String(meta.product_match_id||''))" in html
    assert '<a class="mobile-card-link" href="' in html
    assert '.mobile-card-link:focus-visible' in html
    assert 'role="list"' in html


def test_mobile_and_desktop_fail_closed_together_on_http_error():
    html = read(INDEX_PATH)
    assert "state.payload=null;state.fixtures=null;$('public-fixtures').hidden=true;$('mobile-match-list').innerHTML" in html
    assert "if(p.schema_version!=='product-market-view.v1'||!Array.isArray(p.matches)" in html
    assert "Ошибка загрузки. Данные не обновлены." in html
    assert 'role="alert"' in html


def test_list_uses_backend_verified_market_timestamps_not_invented_live_prices():
    html = read(INDEX_PATH)
    assert 'id="source-note"' in html
    assert "function marketVerified(m)" in html
    assert "m.market_snapshot_status!=='verified_prekickoff'" in html
    assert "function marketSourceLabel(m)" in html
    assert "function safeQuote(s,m)" in html
    assert "marketVerified(m.match)" in html
    assert 'safeQuote(s,meta)' in html
    assert "marketBox(one.display_selection,one.readiness,meta)" in html
    assert "valueBox(marketVerified(meta)?m.value_signal:null)" in html
    assert "время каждого снимка — в карточке матча" in html
    assert 'Коэффициенты — сохранённый снимок, не live-линия' in html
    assert 'Время матчей — Великобритания (UK)' in html


def test_match_list_inline_js_is_syntactically_valid_when_node_available(tmp_path):
    import re
    import shutil
    import subprocess
    import pytest

    if shutil.which("node") is None:
        pytest.skip("Node is not installed in this local environment")
    html = read(INDEX_PATH)
    match = re.search(r"<script>(.*?)</script>", html, re.S)
    assert match, "Missing inline script"
    script = tmp_path / "product_index_v2.js"
    script.write_text(match.group(1), encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_match_page_displays_server_verified_snapshot_provenance():
    html = read(MATCH_PATH)
    assert 'id="sources-heading"' in html
    assert 'id="source-status"' in html
    assert 'id="model-snapshot-time"' in html
    assert 'id="market-snapshot-time"' in html
    assert 'role="status"' in html
    assert "m.prediction_generated_at_utc" in html
    assert "m.market_snapshot_time_utc" in html
    assert "m.market_snapshot_status==='verified_prekickoff'" in html
    assert "m.market_snapshot_status==='ambiguous_fixture'" in html
    assert 'function renderSources(m)' in html
    assert "renderSources(m);$('forecast')" in html


def test_match_page_never_fabricates_a_live_quote_or_missing_timestamp():
    html = read(MATCH_PATH)
    assert "verified?utcTimestamp(m.market_snapshot_time_utc):'Нет проверенного снимка'" in html
    assert "function utcTimestamp(raw)" in html
    assert "return 'Время не указано'" in html
    assert "timeZone:'UTC'" in html
    assert "Коэффициенты — сохранённый снимок, не live-линия" in html
    assert "положительный Raw EV не гарантирует прибыль" in html
    assert "Нет проверенной предматчевой линии" in html
    assert "Время не указано" in html


def test_match_page_snapshot_display_is_responsive():
    html = read(MATCH_PATH)
    assert '.source-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr))' in html
    assert '.hero-grid,.grid,.source-grid{grid-template-columns:1fr}' in html
    assert 'overflow-wrap:anywhere' in html


def test_match_page_inline_js_is_syntactically_valid_when_node_available(tmp_path):
    import re
    import shutil
    import subprocess
    import pytest

    if shutil.which("node") is None:
        pytest.skip("Node is not installed in this local environment")
    match = re.search(r"<script>(.*?)</script>", read(MATCH_PATH), re.S)
    assert match, "Missing match page inline script"
    script = tmp_path / "match_detail.js"
    script.write_text(match.group(1), encoding="utf-8")
    result = subprocess.run(["node", "--check", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_list_market_quote_guards_are_runtime_verified_with_node(tmp_path):
    import re
    import shutil
    import subprocess

    import pytest

    if shutil.which("node") is None:
        pytest.skip("Node is not installed in this environment")
    html = read(INDEX_PATH)
    helper = re.search(r"const num=.*?(?=function forecastBox\()", html, re.S)
    assert helper, "Missing market display helpers"
    check = helper.group(0) + """
const assert = require('node:assert/strict');
const originalNow = Date.now;
Date.now = () => Date.parse('2026-10-10T12:00:00Z');
const verified = {
  market_snapshot_status:'verified_prekickoff',
  market_snapshot_time_utc:'2026-10-10T10:00:00+00:00',
  commence_time_utc:'2026-10-11T15:00:00+00:00'
};
assert.equal(marketVerified(verified), true);
assert.equal(safeQuote({bookmaker_odds:1.85}, verified), '1.85');
assert.equal(safeQuote({bookmaker_odds:'1.85'}, verified), '—');
assert.match(marketSourceLabel(verified), /UTC.*не live/);
assert.equal(marketVerified({...verified, market_snapshot_status:'ambiguous_fixture'}), false);
assert.equal(marketVerified({...verified, market_snapshot_time_utc:null}), false);
assert.equal(marketVerified({...verified, market_snapshot_time_utc:'garbage'}), false);
assert.equal(marketVerified({...verified, market_snapshot_time_utc:'2026-10-11T15:00:00+00:00'}), false);
assert.equal(marketVerified({...verified, market_snapshot_time_utc:'2026-10-10T13:00:00+00:00'}), false);
assert.equal(marketVerified({...verified, commence_time_utc:'2026-10-11T15:00:00'}), false);
assert.equal(safeQuote({bookmaker_odds:1.85}, {...verified,market_snapshot_status:'unverified'}), '—');
assert.equal(priced({match:verified,markets:{'1x2':{selections:[{bookmaker_odds:1.85}]}}}), true);
assert.equal(priced({match:{...verified,market_snapshot_status:'unverified'},markets:{'1x2':{selections:[{bookmaker_odds:1.85}]}}}), false);
assert.equal(hasValue({match:{...verified,market_snapshot_status:'unverified'},value_signal:{status:'positive_raw_ev',selection:{}}}), false);
assert.equal(pct('0.4'), '—');
Date.now = originalNow;
"""
    source = tmp_path / "list_market_guards.js"
    source.write_text(check, encoding="utf-8")
    result = subprocess.run(["node", str(source)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_list_provenance_is_consistent_on_mobile_and_desktop():
    html = read(INDEX_PATH)
    assert 'market-provenance' in html
    assert 'marketSourceLabel(meta)' in html
    assert 'utcStamp(meta.prediction_generated_at_utc)' in html
    assert ".market-provenance{font-size:" in html
    assert "время не указано" in html
    assert "нет проверенной предматчевой линии" in html
    assert "неоднозначная привязка события" in html
    assert "function marketVerified(m)" in html
    assert "const num=v=>typeof v==='number'&&Number.isFinite(v);" in html


def test_schedule_only_fallback_is_visible_without_inventing_model_or_odds():
    html = read(INDEX_PATH)
    assert 'id="public-fixtures"' in html
    assert 'id="fixtures-grid"' in html
    assert 'aria-label="Расписание АПЛ без прогнозов"' in html
    assert "function renderSchedule()" in html
    assert "async function loadSchedule()" in html
    assert "fetch('/upcoming-fixtures'" in html
    assert "if(!p.matches.length)loadSchedule()" in html
    assert "state.payload&&state.payload.matches.length" in html
    assert "Прогнозы модели и коэффициенты не подставляются из календаря" in html
    assert "AI-прогноз отсутствует" in html
    assert "Коэффициенты букмекера отсутствуют" in html
    assert "публичный календарь ESPN" in html
    assert "опубликованное расписание Премьер-лиги" in html


def test_schedule_only_frontend_refuses_unsupported_ai_or_market_fields():
    html = read(INDEX_PATH)
    assert "data.schema_version!=='public-fixtures.v1'" in html
    assert "data.has_model_forecasts!==false" in html
    assert "data.has_bookmaker_odds!==false" in html
    assert "m.model_forecast_status!=='not_available'" in html
    assert "m.bookmaker_odds_status!=='not_available'" in html
    assert "m.league!=='EPL'" in html
    assert "data.fixtures.length>100" in html
    assert "state.fixtures=null;renderSchedule()" in html
    assert "const box=$('public-fixtures'),data=state.fixtures;" in html
    assert "esc(m.home_team)" in html and "esc(m.away_team)" in html


def test_match_detail_accessibility_and_explicit_local_time_contract():
    html = read(MATCH_PATH)
    assert 'id="error" class="error" role="alert"' in html
    assert 'id="loading" class="loading" role="status"' in html
    assert '.back:focus-visible{outline:3px' in html
    assert '.panel-head{flex-wrap:wrap}' in html
    assert 'function localKickoff(m)' in html
    assert 'местное время устройства' in html
    assert 'часовой пояс не подтверждён' in html
    assert "const num=v=>typeof v==='number'&&Number.isFinite(v);" in html


def test_match_detail_market_quote_guards_execute_in_node(tmp_path):
    import re
    import shutil
    import subprocess

    import pytest

    if shutil.which("node") is None:
        pytest.skip("Node is not available")

    html = read(MATCH_PATH)
    match = re.search(r"<script>(.*?)</script>", html, re.S)
    assert match, "Missing match detail inline script"
    # The page calls load() on startup; evaluate only the helper definitions.
    helpers, separator, startup = match.group(1).rpartition("load();")
    assert separator and not startup.strip(), "Unexpected script startup"
    cases = r"""
const assert = require('node:assert/strict');
const originalNow = Date.now;
Date.now = () => Date.parse('2026-10-10T12:00:00Z');
const verified = {
    market_snapshot_status: 'verified_prekickoff',
    market_snapshot_time_utc: '2026-10-10T10:00:00+00:00',
    commence_time_utc: '2026-10-11T15:00:00+00:00'
};
const readiness = {status:'comparison_ready'};
const selection = {label:'Home',probability:0.60,fair_odds:1.67,
    bookmaker_odds:1.85,raw_expected_value:0.11};
const signal = {status:'positive_raw_ev',selection};
assert.equal(num(1.85), true);
assert.equal(num('1.85'), false);
assert.equal(num(NaN), false);
assert.equal(marketVerified(verified), true);
assert.match(selectionCard(selection,readiness,false,verified), />1\.85</);
assert.match(valueHtml(signal,verified), />1\.85</);
assert.equal(utcTimestamp('2026-10-10T10:00:00'), 'Время не указано');
assert.match(utcTimestamp(verified.market_snapshot_time_utc), /UTC/);
assert.match(localKickoff(verified), /местное время устройства/);
assert.match(localKickoff({match_date:'2026-10-11',match_time:'15:00'}),
    /часовой пояс не подтверждён/);
const unsafe = [
    {...verified,market_snapshot_status:'ambiguous_fixture'},
    {...verified,market_snapshot_status:'unverified'},
    {...verified,market_snapshot_time_utc:'2026-10-11T15:00:00+00:00'},
    {...verified,market_snapshot_time_utc:'2026-10-10T13:00:00+00:00'},
    {...verified,market_snapshot_time_utc:null},
    {...verified,commence_time_utc:'2026-10-11T15:00:00'},
];
for (const meta of unsafe) {
    assert.equal(marketVerified(meta), false);
    assert.doesNotMatch(selectionCard(selection,readiness,false,meta), />1\.85</);
    assert.doesNotMatch(valueHtml(signal,meta), />1\.85</);
}
const invalidPrice = {...selection,bookmaker_odds:'1.85'};
assert.doesNotMatch(selectionCard(invalidPrice,readiness,false,verified), />1\.85</);
assert.doesNotMatch(valueHtml({status:'positive_raw_ev',selection:invalidPrice},verified), />1\.85</);
Date.now = originalNow;
"""
    script = tmp_path / "match_detail_quote_guards.js"
    script.write_text(helpers + "\n" + cases, encoding="utf-8")
    result = subprocess.run(["node", str(script)], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
