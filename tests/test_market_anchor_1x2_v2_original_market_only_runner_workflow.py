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
    push = text.split("push:", 1)[1].split("permissions:", 1)[0]
    required_dependency_paths = (
        "market_anchor_1x2_v2_original_market_only_evaluator.py",
        "tests/test_market_anchor_1x2_v2_original_market_only_evaluator.py",
        "experiments/market_anchor_1x2_v2_original_market_only_secondary_policy.json",
        "market_anchor_v2_source_rights.py",
        "research/source_rights/football_data_co_uk.json",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "serie_a_v2_forward_capture.py",
        "serie_a_v2_prequote_source_archive_gate.py",
        "serie_a_v2_live_diagnostic_report.py",
        "serie_a_v2_frozen_shadow_preview.py",
        "serie_a_v2_asof_feature_manifest.py",
        "historical_football_signal_lab.py",
        "market_anchor_1x2_v2_shadow.py",
        "serie_a_v2_attest_real_source.py",
        "serie_a_runtime_config.py",
        ".github/workflows/serie-a-v2-forward-preview.yml",
    )
    for dependency in required_dependency_paths:
        assert f'"{dependency}"' in pull_request
        assert f'"{dependency}"' in push
    assert "github.event_name == 'workflow_dispatch' && github.ref == 'refs/heads/main'" in text
    assert "SUPABASE_KEY" not in text.split("offline-runner-tests:", 1)[1].split("live-read-only-runner:", 1)[0]
