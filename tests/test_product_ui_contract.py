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
    assert "valueBox(m.value_signal)" in index
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
    assert "state.payload=null;$('mobile-match-list').innerHTML" in html
    assert "if(p.schema_version!=='product-market-view.v1'||!Array.isArray(p.matches)" in html
    assert "Ошибка загрузки. Данные не обновлены." in html
    assert 'role="alert"' in html


def test_live_odds_freshness_not_fabricated_when_api_lacks_timestamp():
    html = read(INDEX_PATH)
    assert 'id="source-note"' in html
    assert 'время его фиксации в публичном API не указано' in html
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
