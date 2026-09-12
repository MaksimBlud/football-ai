from pathlib import Path


MATCH_CARD = Path("static/match.html")


def test_match_card_exposes_product_market_contract():
    html = MATCH_CARD.read_text(encoding="utf-8")

    assert "Главный выбор модели" in html
    assert "Исход матча · 1X2" in html
    assert "Тотал голов 2.5" in html
    assert "Фора на матч" in html
    assert "Тотал угловых" in html
    assert "/upcoming-round-match/${matchId}" in html
    assert "/upcoming-matches" in html
    assert "function fairOdds" in html
    assert "probability*odds-1" in html


def test_match_card_keeps_unvalidated_markets_honest():
    html = MATCH_CARD.read_text(encoding="utf-8")

    assert "Нет подходящей ставки" in html
    assert "Непрайсованные рынки в главный выбор не подмешиваются" in html
    assert "не доказанная ставка" in html
    assert "Пока не публикуем вероятность и value" in html
    assert "CORNERS10" in html
    assert "Он не означает подтверждённую доходность" in html
