from pathlib import Path


def test_rpl_automation_docs_match_workflows():
    docs = Path("RPL_AUTOMATION.md").read_text(encoding="utf-8")
    assert "07 */2 * * *" in docs
    assert "32 */2 * * *" in docs
    assert "52 */12 * * *" in docs
