from pathlib import Path


def test_runbook_keeps_rpl_market_only():
    source = Path("RPL_RUNBOOK.md").read_text(encoding="utf-8")
    assert "prediction_mode = MARKET_ONLY" in source
    assert "structural_status = CALIBRATION_REQUIRED" in source
    assert "structural_applied = false" in source
    assert "production model used = false" in source
