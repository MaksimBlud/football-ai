from pathlib import Path


WORKFLOW_DIR = Path(__file__).parent / ".github" / "workflows"
READINESS = WORKFLOW_DIR / "multi-market-activation-status.yml"
PROBE = WORKFLOW_DIR / "multi-market-corner-capability-probe.yml"

PROBE_RELATED_PATHS = (
    "multi_market_corner_capability_probe.py",
    "test_multi_market_corner_capability_probe.py",
    ".github/workflows/multi-market-corner-capability-probe.yml",
)


def test_readiness_self_proves_probe_changes_on_pr_and_main_push():
    source = READINESS.read_text(encoding="utf-8")
    assert "pull_request:" in source
    assert "push:" in source
    for path in PROBE_RELATED_PATHS:
        assert source.count(f"- '{path}'") == 2, path


def test_paid_probe_remains_manual_only():
    source = PROBE.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "push:" not in source
    assert "cron:" not in source
    assert "python odds_api_budget_guard.py --max-cost 2" in source
