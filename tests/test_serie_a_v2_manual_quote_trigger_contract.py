"""Prevent event wiring from accidentally turning V2 into paid automated odds calls.

These static regressions complement the existing paid-workflow budget contract.
The V2 trigger may observe an already-manual run, but it must not create paid
provider calls or a scheduled odds workflow.
"""
from pathlib import Path

PAID = Path(".github/workflows/serie-a-odds-snapshots.yml")
FREE = Path(".github/workflows/serie-a-v2-forward-preview.yml")
HOLD_CI = Path(".github/workflows/market-anchor-v2-paid-odds-workflow-hold.yml")


def _step_block(workflow: str, name: str) -> str:
    marker = f"      - name: {name}\n"
    start = workflow.index(marker)
    tail = workflow[start + len(marker) :]
    next_step = tail.find("\n      - name:")
    return tail if next_step < 0 else tail[:next_step]


def _checkout_step(workflow: str) -> str:
    lines = workflow.splitlines()
    starts = [
        i for i, line in enumerate(lines)
        if line.lstrip().startswith("- uses: actions/checkout@")
    ]
    assert len(starts) == 1, f"expected one pinned checkout step, found {len(starts)}"
    start = starts[0]
    indent = len(lines[start]) - len(lines[start].lstrip())
    end = next(
        (
            i for i in range(start + 1, len(lines))
            if len(lines[i]) - len(lines[i].lstrip()) == indent
            and lines[i].lstrip().startswith("- ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_original_paid_serie_a_collector_remains_dispatch_only():
    paid = PAID.read_text(encoding="utf-8")
    header = paid.split("concurrency:", 1)[0]
    assert "name: Serie A Odds Snapshots" in header
    assert "workflow_dispatch:" in header
    assert "schedule:" not in header
    assert "pull_request:" not in header
    assert "workflow_run:" not in header
    assert "push:" not in header
    assert "repository_dispatch:" not in header
    assert "odds_api_budget_guard.py --max-cost 1" in paid
    assert "THE_ODDS_API_KEY:" in paid


def test_paid_snapshot_workflow_is_default_denied_and_secrets_are_step_scoped():
    paid = PAID.read_text(encoding="utf-8")
    header = paid.split("concurrency:", 1)[0]
    job_before_steps = paid.split("jobs:", 1)[1].split("steps:", 1)[0]

    assert 'THE_ODDS_API_ACCESS_ALLOWED: "false"' in header
    # The workflow-level false default must be the only definition; a later
    # job/step env override could otherwise re-enable paid calls.
    assert paid.count("THE_ODDS_API_ACCESS_ALLOWED:") == 1
    assert paid.count('THE_ODDS_API_ACCESS_ALLOWED: "false"') == 1
    assert 'THE_ODDS_API_ACCESS_ALLOWED: "true"' not in paid
    assert "THE_ODDS_API_KEY" not in job_before_steps
    assert "SUPABASE_URL" not in job_before_steps
    assert "SUPABASE_KEY" not in job_before_steps

    paid_step_names = (
        "Check required secrets",
        "Protect provider hard reserve",
        "Run adaptive Serie A snapshot check",
    )
    for name in paid_step_names:
        block = _step_block(paid, name)
        assert "if: ${{ env.THE_ODDS_API_ACCESS_ALLOWED == 'true' }}" in block

    assert "if: ${{ env.THE_ODDS_API_ACCESS_ALLOWED != 'true' }}" in _step_block(
        paid, "Confirm paid provider access is held"
    )
    assert "secrets.THE_ODDS_API_KEY" in _step_block(paid, "Protect provider hard reserve")
    assert "secrets.SUPABASE_URL" in _step_block(paid, "Run adaptive Serie A snapshot check")
    assert "python odds_api_budget_guard.py --max-cost 1" in _step_block(
        paid, "Protect provider hard reserve"
    )
    assert "python scheduled_serie_a_odds_snapshot.py" in _step_block(
        paid, "Run adaptive Serie A snapshot check"
    )


def test_paid_odds_hold_ci_is_secret_free_never_scheduled_and_does_not_persist_checkout_token():
    workflow = HOLD_CI.read_text(encoding="utf-8")
    header = workflow.split("jobs:", 1)[0]
    checkout = _checkout_step(workflow)
    assert "push:" in header
    assert "pull_request:" in header
    assert "research/v2-paid-odds-hold-checkout-token-isolation-on-960-20261125-run11" in header
    assert "schedule:" not in header
    assert "workflow_dispatch:" not in header
    assert "secrets." not in workflow
    assert "THE_ODDS_API_KEY" not in workflow
    assert "GITHUB_TOKEN" not in workflow
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" in checkout
    assert "persist-credentials: false" in checkout
    assert "scheduled_serie_a_odds_snapshot.py" not in workflow
    assert "pytest -q tests/test_serie_a_v2_manual_quote_trigger_contract.py" in workflow


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

    policy = json.loads(
        Path("experiments/market_anchor_1x2_v2_current_form_policy.json").read_text(encoding="utf-8")
    )
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
    assert "schedule:" in source
    assert "workflow_dispatch:" in source
    assert "workflow_dispatch:" in forward
    assert "push:" in forward
    assert '"serie_a_v2_current_form_forward_capture.py"' in forward
