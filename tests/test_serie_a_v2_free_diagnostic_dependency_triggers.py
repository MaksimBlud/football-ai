"""Keep the free original-V2 diagnostic wired to every frozen runtime dependency."""

from pathlib import Path


WORKFLOW = Path(".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml")


def test_free_diagnostic_push_paths_cover_frozen_transitive_dependencies():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    push = workflow.split("  push:\n", 1)[1].split("\n\nconcurrency:", 1)[0]

    required_paths = (
        "serie_a_v2_live_diagnostic_report.py",
        "serie_a_v2_asof_feature_manifest.py",
        "serie_a_v2_frozen_shadow_preview.py",
        "serie_a_v2_prequote_source_archive_gate.py",
        "market_anchor_1x2_v2_shadow.py",
        "historical_football_signal_lab.py",
        "serie_a_runtime_config.py",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "experiments/market_anchor_1x2_v2_protocol.json",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_serie_a_v2_prequote_source_archive_gate.py",
        "tests/test_serie_a_v2_free_diagnostic_dependency_triggers.py",
        ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
    )

    for path in required_paths:
        assert f'"{path}"' in push, f"missing push trigger for frozen dependency: {path}"


def test_dependency_trigger_regression_runs_in_free_diagnostic_workflow():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    step = workflow.split("- name: Offline regression tests", 1)[1].split(
        "- name: Verify source access", 1
    )[0]
    assert "tests/test_serie_a_v2_free_diagnostic_dependency_triggers.py" in step


def test_free_diagnostic_workflow_never_dispatches_paid_quote_collection():
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "THE_ODDS_API_KEY" not in workflow
    assert "scheduled_serie_a_odds_snapshot.py" not in workflow
    assert "odds_api_budget_guard.py" not in workflow
    assert "requests.post" not in workflow
