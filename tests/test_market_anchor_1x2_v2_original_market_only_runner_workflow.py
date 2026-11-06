from pathlib import Path


def test_original_market_only_runner_workflow_is_manual_only_and_read_only():
    text = Path(
        ".github/workflows/market-anchor-1x2-v2-original-market-only-secondary-runner.yml"
    ).read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    pull_request = text.split("pull_request:", 1)[1].split("push:", 1)[0]
    assert "- main" in pull_request
    assert "- research/v2-original-market-only-secondary-eval-20261106-run11" in pull_request
    assert "schedule:" not in text
    assert "Serie A Odds Snapshots" not in text
    assert "The Odds API" not in text
    assert "permissions:" in text
    assert "actions: read" in text
    assert "contents: read" in text
    assert "contents: write" not in text
    assert "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'" in text
    assert "SUPABASE_KEY" not in text.split("offline-runner-tests:", 1)[1].split("live-read-only-runner:", 1)[0]
