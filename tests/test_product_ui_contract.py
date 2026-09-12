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

    assert "fetch(`/product-market-view/${id}`" in html
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


def test_list_links_to_server_indexed_match_card():
    html = read(INDEX_PATH)

    assert "/match?id=${row.dataset.index}" in html
