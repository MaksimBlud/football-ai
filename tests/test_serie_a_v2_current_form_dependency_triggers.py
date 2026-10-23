"""Regression guard for frozen original V2 current-form workflow dependencies.

A change to a frozen model/feature/source dependency must re-run the read-only
source audit. The source workflow's successful completion then wakes the
existing read-only forward preview; it never starts the paid odds collector.
"""
from pathlib import Path
import re


SOURCE_WORKFLOW = Path(".github/workflows/serie-a-v2-current-form-source-capture.yml")
FORWARD_WORKFLOW = Path(".github/workflows/serie-a-v2-current-form-forward-preview.yml")

REQUIRED_SOURCE_AUDIT_PATHS = {
    "serie_a_v2_current_form_source_capture.py",
    "serie_a_v2_live_diagnostic_report.py",
    "serie_a_v2_frozen_shadow_preview.py",
    "serie_a_v2_asof_feature_manifest.py",
    "historical_football_signal_lab.py",
    "serie_a_runtime_config.py",
    "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
    "experiments/market_anchor_1x2_v2_current_form_policy.json",
    "experiments/market_anchor_1x2_v2_protocol.json",
    "tests/test_serie_a_v2_current_form_source_capture.py",
    "tests/test_serie_a_v2_current_form_forward_capture.py",
    "tests/test_serie_a_v2_live_diagnostic_report.py",
    "tests/test_serie_a_v2_frozen_shadow_preview.py",
    "tests/test_serie_a_v2_asof_feature_manifest.py",
    "tests/test_serie_a_v2_atalanta_alias.py",
    "tests/test_serie_a_v2_manual_quote_trigger_contract.py",
    "tests/test_serie_a_v2_current_form_dependency_triggers.py",
    ".github/workflows/serie-a-v2-current-form-source-capture.yml",
}


def _source_push_paths(workflow_text: str) -> set[str]:
    lines = workflow_text.splitlines()
    push_index = lines.index("  push:")
    end_index = lines.index("concurrency:")
    push_block = lines[push_index + 1:end_index]
    paths_index = push_block.index("    paths:")
    paths = set()
    for line in push_block[paths_index + 1:]:
        match = re.match(r'^\s*- "([^"]+)"\s*$', line)
        if match:
            paths.add(match.group(1))
    assert paths, "source capture workflow must declare an explicit path filter"
    return paths


def test_current_form_source_capture_reaudits_all_frozen_v2_dependencies():
    workflow = SOURCE_WORKFLOW.read_text(encoding="utf-8")
    actual = _source_push_paths(workflow)
    missing = REQUIRED_SOURCE_AUDIT_PATHS - actual
    assert not missing, f"frozen V2 dependency changes would skip source audit: {sorted(missing)}"


def test_source_audit_runs_the_dependency_regressions_and_preserves_schedule():
    workflow = SOURCE_WORKFLOW.read_text(encoding="utf-8")
    assert 'cron: "50 5 * * *"' in workflow
    assert "tests/test_serie_a_v2_current_form_dependency_triggers.py" in workflow
    assert "tests/test_serie_a_v2_frozen_shadow_preview.py" in workflow
    assert "tests/test_serie_a_v2_current_form_forward_capture.py" in workflow
    assert "THE_ODDS_API_KEY" not in workflow
    assert "scheduled_serie_a_odds_snapshot.py" not in workflow
    assert "odds_api_budget_guard.py" not in workflow
    assert "requests.post" not in workflow


def test_successful_source_audit_is_still_the_only_dependency_trigger_for_forward():
    workflow = FORWARD_WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_run:" in workflow
    assert '"Serie A V2 Current-Form Source Capture"' in workflow
    assert "github.event.workflow_run.conclusion == 'success'" in workflow
    assert "github.event.workflow_run.head_branch == 'main'" in workflow
    assert "github.event.workflow_run.event != 'pull_request'" in workflow
    assert "THE_ODDS_API_KEY" not in workflow
    assert "scheduled_serie_a_odds_snapshot.py" not in workflow
    assert "odds_api_budget_guard.py" not in workflow
