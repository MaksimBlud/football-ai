from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = ROOT / "TURKEY_PORTUGAL_COMPLETE.marker"


def test_turkey_portugal_complete_marker_exists_and_is_truthful():
    text = MARKER.read_text(encoding="utf-8")
    assert "MARKET_ONLY" in text
    assert "live-verified" in text
    assert "viewer-integrated" in text
    assert "CI-hardened" in text
    assert "quota-gated" in text
    assert "production" not in text.lower()
