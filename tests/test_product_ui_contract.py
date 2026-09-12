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

    assert "fetch(`/product-market-view/${matchId}`" in html
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


def test_product_semantics_remain_explicit_in_ui():
    index = read(INDEX_PATH)
    detail = read(MATCH_PATH)

    assert "Нет подходящей ставки" in index
    assert "Расчётный кандидат" in index
    assert "research" in index.lower()
    assert "Нет подходящей ставки" in detail
    assert "Расчётный кандидат" in detail
    assert "raw EV" in detail


def test_list_links_to_server_indexed_match_card():
    html = read(INDEX_PATH)

    assert "/match?id=${row.dataset.index}" in html
