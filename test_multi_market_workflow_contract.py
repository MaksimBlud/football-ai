from pathlib import Path


ROOT = Path(__file__).resolve().parent
READINESS = ROOT / ".github" / "workflows" / "multi-market-activation-status.yml"
CYCLE = ROOT / ".github" / "workflows" / "multi-market-cycle.yml"


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_shared_policy_changes_trigger_readiness_and_cycle_workflows():
    assert "- 'multi_market_policy.py'" in _text(READINESS)
    assert "- 'multi_market_policy.py'" in _text(CYCLE)


def test_cycle_remains_fail_closed_entrypoint():
    text = _text(CYCLE)
    assert "python multi_market_cycle.py" in text
    cycle_source = (ROOT / "multi_market_cycle.py").read_text(encoding="utf-8")
    assert "if not schema_ready():" in cycle_source
    assert "schema not applied; provider quota not used" in cycle_source
    assert cycle_source.index("if not schema_ready():") < cycle_source.index("result = collect()")


def test_readiness_live_job_cannot_run_on_pull_request():
    text = _text(READINESS)
    assert "if: github.event_name != 'pull_request'" in text
    assert "paid_provider_requests" in text
    assert "writes_performed" in text


def test_policy_module_is_side_effect_free():
    source = (ROOT / "multi_market_policy.py").read_text(encoding="utf-8")
    forbidden = ("database", "supabase", "requests", "pandas", "os.environ", "dotenv")
    assert not any(token in source for token in forbidden)
