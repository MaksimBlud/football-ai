from pathlib import Path


def test_rpl_notes_do_not_claim_structural_calibration():
    text = Path("RPL_NOTES.md").read_text(encoding="utf-8")
    assert "Structural V2 calibration remain a separate research phase" in text
