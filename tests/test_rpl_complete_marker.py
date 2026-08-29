from pathlib import Path


def test_rpl_completion_marker_is_market_only():
    value = Path("RPL_COMPLETE.marker").read_text(encoding="utf-8")
    assert "MARKET_ONLY" in value
