from pathlib import Path


DASHBOARD = Path("static/index_v2.html")


def test_product_market_dashboard_contract():
    html = DASHBOARD.read_text(encoding="utf-8")

    for heading in (
        "Главный выбор модели",
        "Исход матча",
        "Фора",
        "Тотал голов",
        "Тотал угловых",
    ):
        assert heading in html

    assert "/upcoming-round-predictions" in html
    assert "/upcoming-matches" in html
    assert "/refresh-predictions" in html
    assert "function fairOdds" in html
    assert "probability*odds-1" in html


def test_unvalidated_markets_are_not_presented_as_ready_bets():
    html = DASHBOARD.read_text(encoding="utf-8")

    assert "не подтверждён OOS" in html
    assert "Пока не рассчитывается" in html
    assert "CORNERS10" in html
    assert "Это не утверждение о подтверждённой прибыльности" in html
