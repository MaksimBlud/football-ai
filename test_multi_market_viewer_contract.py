from pathlib import Path


def test_multi_market_viewer_contains_requested_sections():
    html = Path("static/multi_market_viewer.html").read_text(encoding="utf-8")
    for text in (
        "Исход матча · 1X2",
        "Исход с форой",
        "Тотал голов",
        "Тотал угловых",
        "Индивидуальный тотал угловых",
        "Нет данных",
    ):
        assert text in html


def test_multi_market_viewer_defaults_to_upcoming_and_never_calls_provider():
    html = Path("static/multi_market_viewer.html").read_text(encoding="utf-8")
    assert '<option value="UPCOMING" selected>' in html
    assert "/api/research-viewer" in html
    assert "api.the-odds-api.com" not in html
