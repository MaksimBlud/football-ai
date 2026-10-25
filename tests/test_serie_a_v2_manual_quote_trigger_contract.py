"""Prevent event wiring from accidentally turning V2 into paid automated odds calls.

These are static safety regressions complementing the existing paid workflow
budget contract. The V2 trigger observes a successful *already manual* run;
it MUST NOT schedule or dispatch a new paid odds workflow.
"""
from pathlib import Path

PAID = Path(".github/workflows/serie-a-odds-snapshots.yml")
FREE = Path(".github/workflows/serie-a-v2-forward-preview.yml")


def test_original_paid_serie_a_collector_remains_dispatch_only():
    paid = PAID.read_text(encoding="utf-8")
    header = paid.split("concurrency:", 1)[0]
    assert "name: Serie A Odds Snapshots" in header
    assert "workflow_dispatch:" in header
    assert "schedule:" not in header
    assert "workflow_run:" not in header
    assert "push:" not in header
    assert "repository_dispatch:" not in header
    assert "odds_api_budget_guard.py --max-cost 1" in paid
    assert "THE_ODDS_API_KEY:" in paid


def test_free_original_v2_observes_manual_paid_result_without_starting_provider():
    free = FREE.read_text(encoding="utf-8")
    assert 'name: Serie A V2 Original Forward-Only Preview' in free
    assert 'workflow_run:' in free
    assert '"Serie A Odds Snapshots"' in free
    assert 'completed' in free
    assert "github.event.workflow_run.conclusion == 'success'" in free
    assert "github.event.workflow_run.head_branch == 'main'" in free
    assert "github.event.workflow_run.event == 'workflow_dispatch'" in free
    assert "github.event_name != 'workflow_run'" in free
    assert 'schedule:' in free
    assert 'actions: read' in free
    assert 'contents: read' in free
    assert 'THE_ODDS_API_KEY' not in free
    assert 'scheduled_serie_a_odds_snapshot.py' not in free
    assert 'odds_api_budget_guard.py' not in free
    assert 'requests.post' not in free


def test_free_original_v2_still_preserves_archive_proof_and_no_bet():
    free = FREE.read_text(encoding="utf-8")
    runner = Path("serie_a_v2_forward_capture.py").read_text(encoding="utf-8")
    assert "tests/test_serie_a_v2_forward_capture.py" in free
    assert "serie_a_v2_asof_feature_manifest.py" in free
    assert "tests/test_serie_a_v2_asof_feature_manifest.py" in free
    assert "serie_a_v2_forward_capture.py" in free
    assert "--sources-output-dir" in free
    assert "actions/upload-artifact@v4" in free
    assert "verify_archive(" in runner
    assert "github_artifact_sha256=" in runner
    assert '"eligible_for_frozen_prospective_cohort": False' in runner
    assert '"no_bet": True' in runner
    assert '"paid_provider_calls": 0' in runner
    assert '"supabase_writes": 0' in runner


def test_current_form_v2_is_a_separate_predeclared_forward_only_cohort():
    import json

    policy = json.loads(Path("experiments/market_anchor_1x2_v2_current_form_policy.json").read_text(encoding="utf-8"))
    assert policy["experiment_id"] == "MARKET_ANCHOR_1X2_V2_CURRENT_FORM_FORWARD_ONLY"
    assert policy["frozen_original_candidate"]["artifact_sha256"] == "a9d5abc2eee762991a5272d8bb530f76cd008b4b4a3eb48ff2072f374626ade6"
    assert policy["feature_source"]["current_season_results_allowed_only_as_lagged_inputs"] is True
    assert policy["feature_source"]["same_calendar_day_matches_excluded"] is True
    assert policy["feature_source"]["must_be_archived_before_quote"] is True
    assert policy["feature_input_gate"]["count_query_reads_score_or_result_fields"] is False
    assert policy["feature_input_gate"]["does_not_open_target_outcome_evaluation_gate"] is True
    assert policy["target_outcome_evaluation_gate"]["minimum_completed_eligible_prospective_forecasts"] == 30
    assert policy["target_outcome_evaluation_gate"]["target_outcomes_read_before_gate"] is False
    assert policy["target_outcome_evaluation_gate"]["review_signal_requires"].startswith("After 30 eligible forward forecasts")
    assert policy["safety"]["production_writes"] is False
    assert policy["safety"]["supabase_writes"] is False
    assert policy["safety"]["paid_provider_calls"] == 0


def test_current_form_source_capture_and_forward_preview_never_trigger_paid_odds():
    source = Path(".github/workflows/serie-a-v2-current-form-source-capture.yml").read_text(encoding="utf-8")
    forward = Path(".github/workflows/serie-a-v2-current-form-forward-preview.yml").read_text(encoding="utf-8")
    for workflow in (source, forward):
        assert "THE_ODDS_API_KEY" not in workflow
        assert "scheduled_serie_a_odds_snapshot.py" not in workflow
        assert "odds_api_budget_guard.py" not in workflow
        assert "requests.post" not in workflow
        assert "contents: read" in workflow
    assert "workflow_run:" in forward
    assert '"Serie A V2 Current-Form Source Capture"' in forward
    assert '"Serie A Odds Snapshots"' in forward
    assert "github.event.workflow_run.event == 'workflow_dispatch'" in forward
    assert 'schedule:' in source
    assert 'workflow_dispatch:' in source
    assert 'workflow_dispatch:' in forward
    assert 'push:' in forward
    assert '"serie_a_v2_current_form_forward_capture.py"' in forward


def test_current_form_forward_preview_reaudits_frozen_runtime_dependencies():
    """Changes to any frozen/runtime input must re-run the free forward-only audit."""
    import re

    workflow_path = Path(".github/workflows/serie-a-v2-current-form-forward-preview.yml")
    workflow = workflow_path.read_text(encoding="utf-8")
    push = workflow.split("  push:\\n", 1)[1].split("\\n  workflow_run:", 1)[0]
    paths_block = push.split("    paths:\\n", 1)[1]
    declared_paths = set(re.findall(r'^      - "([^"]+)"$', paths_block, flags=re.MULTILINE))
    required_paths = {
        "serie_a_v2_current_form_forward_capture.py",
        "serie_a_v2_current_form_source_capture.py",
        "serie_a_v2_asof_feature_manifest.py",
        "serie_a_v2_frozen_shadow_preview.py",
        "serie_a_v2_live_diagnostic_report.py",
        "serie_a_v2_prequote_source_archive_gate.py",
        "serie_a_runtime_config.py",
        "historical_football_signal_lab.py",
        "experiments/market_anchor_1x2_v2_current_form_policy.json",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "tests/test_serie_a_v2_current_form_source_capture.py",
        "tests/test_serie_a_v2_current_form_forward_capture.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_serie_a_v2_prequote_source_archive_gate.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_historical_football_signal_lab.py",
        "tests/test_serie_a_v2_manual_quote_trigger_contract.py",
        ".github/workflows/serie-a-v2-current-form-forward-preview.yml",
    }
    assert required_paths <= declared_paths

    test_step = workflow.split("name: Test frozen model, current-form source integrity, and no-outcome capture", 1)[1].split("      - name:", 1)[0]
    for required_test in (
        "tests/test_serie_a_v2_prequote_source_archive_gate.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_historical_football_signal_lab.py",
    ):
        assert required_test in test_step
