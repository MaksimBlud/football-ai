from pathlib import Path


WORKFLOW = Path('.github/workflows/multi-market-backfill.yml')


def _text() -> str:
    return WORKFLOW.read_text(encoding='utf-8')


def test_backfill_outcome_jobs_are_manual_dispatch_only():
    text = _text()
    assert "manual-dry-run:" in text
    assert "manual-write:" in text
    assert "if: github.event_name == 'workflow_dispatch' && inputs.write == false" in text
    assert "if: github.event_name == 'workflow_dispatch' && inputs.write == true" in text
    assert "live-dry-run:" not in text
    assert "if: github.event_name == 'push'" not in text


def test_push_path_only_keeps_validation_contract():
    text = _text()
    push_block = text.split("  push:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "branches: [main]" in push_block
    assert "multi_market_backfill.py" in push_block
    assert "validate:" in text
    assert "python multi_market_backfill.py\n" in text  # manual dry-run command still exists
    assert "python multi_market_backfill.py --write" in text
