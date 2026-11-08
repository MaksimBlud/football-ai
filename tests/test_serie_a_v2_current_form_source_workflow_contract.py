"""Regression checks for the free original/current-form V2 workflow contracts."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SOURCE_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-current-form-source-capture.yml"
ORIGINAL_FORWARD_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-forward-preview.yml"
CURRENT_FORWARD_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-current-form-forward-preview.yml"
FREE_DIAGNOSTIC_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-free-real-quote-diagnostic.yml"
FROZEN_SHADOW_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-frozen-v2-shadow-tests.yml"
BUDGET_TEST_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-public-source-download-budget-tests.yml"


def _push_paths(workflow: Path) -> set[str]:
    text = workflow.read_text(encoding="utf-8")
    push_block = text.split("  push:\n", 1)[1].split("\n\nconcurrency:", 1)[0]
    return set(re.findall(r'^\s+- "([^"]+)"\s*$', push_block, flags=re.MULTILINE))


def test_current_form_push_filter_covers_frozen_source_dependencies():
    paths = _push_paths(CURRENT_SOURCE_WORKFLOW)
    required = {
        "serie_a_v2_current_form_source_capture.py",
        "experiments/market_anchor_1x2_v2_current_form_policy.json",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "historical_football_signal_lab.py",
        "serie_a_runtime_config.py",
        "serie_a_v2_frozen_shadow_preview.py",
        "market_anchor_1x2_v2_shadow.py",
        "market_anchor_1x2_v1.py",
        "serie_a_v2_live_diagnostic_report.py",
        "serie_a_v2_asof_feature_manifest.py",
        "tests/test_historical_football_signal_lab.py",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "tests/test_serie_a_v2_current_form_source_capture.py",
        "tests/test_serie_a_v2_current_form_source_workflow_contract.py",
        ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
        ".github/workflows/serie-a-v2-current-form-source-capture.yml",
    }
    assert required <= paths, (
        f"current-form source workflow misses push triggers: {sorted(required - paths)}"
    )


def test_current_form_source_workflow_runs_frozen_feature_regressions():
    text = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    validation = text.split("      - name: Validate feature-input gate and source integrity rules", 1)[1]
    validation = validation.split("      - name: Capture frozen historical seasons plus gated current-form source", 1)[0]
    required_tests = {
        "tests/test_serie_a_v2_current_form_source_capture.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_historical_football_signal_lab.py",
        "tests/test_serie_a_v2_current_form_source_workflow_contract.py",
    }
    assert all(name in validation for name in required_tests), (
        f"current-form source workflow omits regression tests: "
        f"{sorted(name for name in required_tests if name not in validation)}"
    )

    compile_line = next(line for line in validation.splitlines() if "python -m py_compile " in line)
    assert "market_anchor_1x2_v2_shadow.py" in compile_line
    assert "market_anchor_1x2_v1.py" in compile_line


def test_original_forward_push_filter_covers_frozen_v2_dependencies():
    paths = _push_paths(ORIGINAL_FORWARD_WORKFLOW)
    required = {
        "serie_a_v2_forward_capture.py",
        "serie_a_v2_prequote_source_archive_gate.py",
        "tests/test_serie_a_v2_prequote_source_archive_gate.py",
        "serie_a_v2_live_diagnostic_report.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "serie_a_v2_attest_real_source.py",
        "tests/test_serie_a_v2_attest_real_source.py",
        "tests/test_serie_a_v2_forward_capture.py",
        "tests/test_serie_a_v2_manual_quote_trigger_contract.py",
        "serie_a_v2_frozen_shadow_preview.py",
        "market_anchor_1x2_v2_shadow.py",
        "market_anchor_1x2_v1.py",
        "historical_football_signal_lab.py",
        "serie_a_runtime_config.py",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "experiments/market_anchor_1x2_v2_protocol.json",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_historical_football_signal_lab.py",
        "tests/test_serie_a_v2_current_form_source_workflow_contract.py",
        ".github/workflows/serie-a-v2-forward-preview.yml",
    }
    assert required <= paths, (
        f"original forward workflow misses frozen V2 triggers: {sorted(required - paths)}"
    )


def test_original_forward_workflow_runs_frozen_dependency_regressions():
    text = ORIGINAL_FORWARD_WORKFLOW.read_text(encoding="utf-8")
    validation = text.split("      - name: Test original V2, old-season embargo, and source-before-quote rules", 1)[1]
    validation = validation.split("      - name: Attest original historical source ZIP from real GitHub Actions", 1)[0]
    required_tests = {
        "tests/test_serie_a_v2_forward_capture.py",
        "tests/test_serie_a_v2_attest_real_source.py",
        "tests/test_serie_a_v2_manual_quote_trigger_contract.py",
        "tests/test_serie_a_v2_prequote_source_archive_gate.py",
        "tests/test_serie_a_v2_live_diagnostic_report.py",
        "tests/test_serie_a_v2_asof_feature_manifest.py",
        "tests/test_serie_a_v2_atalanta_alias.py",
        "tests/test_serie_a_v2_frozen_shadow_preview.py",
        "tests/test_historical_football_signal_lab.py",
        "tests/test_serie_a_v2_current_form_source_workflow_contract.py",
    }
    assert all(name in validation for name in required_tests), (
        f"original forward workflow omits regression tests: "
        f"{sorted(name for name in required_tests if name not in validation)}"
    )


def test_frozen_shadow_ci_runs_this_contract_and_tracks_original_forward_workflow():
    text = FROZEN_SHADOW_WORKFLOW.read_text(encoding="utf-8")
    paths_block = text.split("    paths:\n", 1)[1].split("\n\npermissions:", 1)[0]
    assert '"tests/test_serie_a_v2_current_form_source_workflow_contract.py"' in paths_block
    assert '".github/workflows/serie-a-v2-forward-preview.yml"' in paths_block
    assert '"market_anchor_1x2_v2_shadow.py"' in paths_block
    assert '"market_anchor_1x2_v1.py"' in paths_block
    assert "tests/test_serie_a_v2_current_form_source_workflow_contract.py" in text
    compile_line = next(line for line in text.splitlines() if "python -m py_compile " in line)
    assert "market_anchor_1x2_v2_shadow.py" in compile_line
    assert "market_anchor_1x2_v1.py" in compile_line


def test_secret_bearing_v2_workflows_only_run_on_main_ref():
    """Manual dispatch from a feature ref must not receive Supabase secrets."""
    expected_jobs = {
        CURRENT_SOURCE_WORKFLOW: ("capture-current-form", "if: ${{ github.ref == 'refs/heads/main' &&"),
        ORIGINAL_FORWARD_WORKFLOW: ("original-v2-forward-preview", "if: ${{ github.ref == 'refs/heads/main' && github.event_name != 'push' && ("),
        CURRENT_FORWARD_WORKFLOW: ("current-form-forward-preview", "if: ${{ github.ref == 'refs/heads/main' && ("),
    }
    for workflow_path, (job_name, guard) in expected_jobs.items():
        text = workflow_path.read_text(encoding="utf-8")
        job_block = text.split(f"  {job_name}:\n", 1)[1].split("\n    steps:", 1)[0]
        assert guard in job_block, (
            f"{workflow_path.name} must fail closed outside refs/heads/main before "
            "its secret-bearing job can run"
        )
        assert "SUPABASE_KEY: ${{ secrets.SUPABASE_KEY }}" in job_block
        assert job_block.index(guard) < job_block.index("env:")


def test_current_form_source_refreshes_after_free_diagnostic_without_changing_cron():
    text = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    assert '- cron: "50 5 * * *"' in text

    trigger = text.split("  workflow_run:\n", 1)[1].split("\n\npush:", 1)[0]
    assert '      - "Serie A V2 Free Real-Quote Diagnostic"' in trigger
    assert "    types:\n      - completed" in trigger
    assert "Serie A Odds Snapshots" not in trigger

    job = text.split("  capture-current-form:\n", 1)[1].split("\n    runs-on:", 1)[0]
    assert "github.event.workflow_run.conclusion == 'success'" in job
    assert "github.event.workflow_run.head_branch == 'main'" in job
    assert "github.event.workflow_run.name == 'Serie A V2 Free Real-Quote Diagnostic'" in job
    assert "github.event.workflow_run.event == 'schedule'" in job
    assert "github.event.workflow_run.event == 'workflow_dispatch'" in job

    assert "  actions: read" in text
    assert "GITHUB_TOKEN: ${{ github.token }}" in text
    assert "verify_latest_source_archive" in text
    assert "fresh_for_new_quote" in text
    assert "fresh_for_current_feature_gate" in text
    assert "steps.source_refresh.outputs.capture != 'false'" in text


def test_source_rights_changes_reaudit_every_live_v2_workflow():
    required = {
        "market_anchor_v2_source_rights.py",
        "research/source_rights/football_data_co_uk.json",
    }
    workflows = (
        CURRENT_SOURCE_WORKFLOW,
        CURRENT_FORWARD_WORKFLOW,
        ORIGINAL_FORWARD_WORKFLOW,
        FREE_DIAGNOSTIC_WORKFLOW,
    )
    for workflow in workflows:
        missing = required - _push_paths(workflow)
        assert not missing, (
            f"{workflow.name} would skip V2 rights re-audit for: {sorted(missing)}"
        )

def test_diagnostic_trigger_source_preflight_checks_rights_before_any_data_access():
    """The workflow_run freshness preflight must not bypass the source-rights gate."""
    text = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    preflight = text.split(
        "      - name: Check existing verified source before diagnostic-triggered refresh",
        1,
    )[1].split(
        "      - name: Capture frozen historical seasons plus gated current-form source",
        1,
    )[0]

    assert "from market_anchor_v2_source_rights import require_personal_research_inference_scope" in preflight
    rights_check = preflight.index("rights_scope = require_personal_research_inference_scope()")
    for access in (
        "create_client(",
        "read_completed_primary_event_identities(",
        "discover_archives(",
        "get_archive(",
    ):
        assert rights_check < preflight.index(access), (
            f"source-rights check must precede {access}"
        )
    assert '"provider_issued_ai_inference_license": rights_scope.get("provider_issued_ai_inference_license")' in preflight


def test_current_form_rights_preflight_blocks_metadata_budget_and_artifact_when_scope_is_denied():
    """A denied rights gate must stop before Supabase metadata, budget markers, or source artifacts."""
    text = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    rights = text.index(
        "Preflight frozen V2 source rights before metadata or download budget"
    )
    source_refresh = text.index(
        "Check existing verified source before diagnostic-triggered refresh"
    )
    budget = text.index("Check shared public-source download budget")
    marker = text.index("Upload shared public-source download attempt marker")
    capture = text.index("Capture frozen historical seasons plus gated current-form source")
    archive = text.index("Archive source bytes and gate manifest for future quotes only")
    assert rights < source_refresh < budget < marker < capture < archive

    rights_block = text.split(
        "      - name: Preflight frozen V2 source rights before metadata or download budget",
        1,
    )[1].split(
        "      - name: Check existing verified source before diagnostic-triggered refresh",
        1,
    )[0]
    assert "require_personal_research_inference_scope()" in rights_block
    assert "except PermissionError" in rights_block
    assert 'output.write(f"allowed={allowed}' in rights_block
    assert "create_client(" not in rights_block
    assert "from supabase" not in rights_block
    assert "import requests" not in rights_block
    assert "requests.get" not in rights_block

    guarded_steps = (
        "Check existing verified source before diagnostic-triggered refresh",
        "Check shared public-source download budget",
        "Upload shared public-source download attempt marker",
        "Capture frozen historical seasons plus gated current-form source",
        "Archive source bytes and gate manifest for future quotes only",
    )
    for step_name in guarded_steps:
        block = text.split(f"      - name: {step_name}", 1)[1].split(
            "      - name:", 1
        )[0]
        assert "steps.rights_preflight.outputs.allowed == 'true'" in block, (
            f"{step_name} must be skipped when frozen inference rights are denied"
        )

    assert '- cron: "50 5 * * *"' in text


def test_current_form_rights_preflight_is_local_only_and_does_not_consume_download_budget():
    text = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    block = text.split(
        "      - name: Preflight frozen V2 source rights before metadata or download budget",
        1,
    )[1].split(
        "      - name: Check existing verified source before diagnostic-triggered refresh",
        1,
    )[0]
    assert "market_anchor_v2_source_rights" in block
    assert "GITHUB_OUTPUT" in block
    assert "download_budget_markers" in block
    assert "source_archive_artifacts" in block
    assert "serie_a_v2_public_source_download_budget.py" not in block
    assert "actions/upload-artifact" not in block


def test_stacked_rights_preflight_pr_receives_exact_v2_ci_on_its_base_branch():
    """The stacked #721 branch must receive the same offline V2/budget checks as a main PR."""
    source = CURRENT_SOURCE_WORKFLOW.read_text(encoding="utf-8")
    source_push_branches = source.split("  push:\n", 1)[1].split("    paths:\n", 1)[0]
    assert "research/v2-block-blocked-source-capture-*" in source_push_branches

    frozen = FROZEN_SHADOW_WORKFLOW.read_text(encoding="utf-8")
    frozen_pr_branches = frozen.split("  pull_request:\n", 1)[1].split("    paths:\n", 1)[0]
    assert "research/v2-provider-ai-inference-rights-block-*" in frozen_pr_branches

    budget = BUDGET_TEST_WORKFLOW.read_text(encoding="utf-8")
    budget_pr_branches = budget.split("  pull_request:\n", 1)[1].split("    paths:\n", 1)[0]
    assert "research/v2-provider-ai-inference-rights-block-*" in budget_pr_branches

    # These are validation triggers only: no schedule, paid collector, or secret-bearing
    # live job is added to the stacked branch.
    assert '- cron: "50 5 * * *"' in source
    assert "  schedule:" in source
    assert "The Odds API" not in source_push_branches


def test_all_live_v2_entrypoints_block_rights_denied_source_quote_reads_and_artifacts():
    """Every live original/current-form V2 workflow must stop before external reads and archive upload."""
    expectations = (
        (
            ORIGINAL_FORWARD_WORKFLOW,
            (
                "Attest original historical source ZIP from real GitHub Actions (no quotes read)",
                "Generate actual original frozen V2 source-verified read-only preview",
                "Save immutable original V2 predictions and exact older source bytes",
            ),
            '- cron: "8 8 * * *"',
        ),
        (
            FREE_DIAGNOSTIC_WORKFLOW,
            (
                "Check shared public-source download budget",
                "Upload shared public-source download attempt marker",
                "Fetch and SHA-archive public source, preview original frozen V2 diagnostics",
                "Archive diagnostic and exact public CSV bytes for provenance",
            ),
            '- cron: "13 6 * * *"',
        ),
        (
            CURRENT_FORWARD_WORKFLOW,
            (
                "Generate read-only current-form V2 shadow from already saved quotes",
                "Archive pre-kickoff V2 shadow and exact source ZIPs",
            ),
            '- cron: "18 8 * * *"',
        ),
    )
    for workflow_path, downstream_steps, frozen_cron in expectations:
        text = workflow_path.read_text(encoding="utf-8")
        assert frozen_cron in text
        if workflow_path == FREE_DIAGNOSTIC_WORKFLOW:
            quote_preflight_name = "Preflight saved future pre-kickoff quotes (metadata only)"
            quote_preflight = text.index(f"      - name: {quote_preflight_name}")
            preflight_name = "Preflight frozen V2 source rights before source access"
            preflight = text.index(f"      - name: {preflight_name}")
            assert preflight < quote_preflight
            quote_block = text.split(
                f"      - name: {quote_preflight_name}", 1
            )[1].split("\n      - name:", 1)[0]
            assert "--preflight-only" in quote_block
        else:
            preflight_name = "Preflight frozen V2 source rights before source/quote access"
            preflight = text.index(f"      - name: {preflight_name}")
        block = text.split(
            f"      - name: {preflight_name}", 1
        )[1].split("\n      - name:", 1)[0]
        assert "require_personal_research_inference_scope()" in block
        assert "except PermissionError" in block
        assert "from supabase" not in block
        assert "import requests" not in block
        assert "create_client(" not in block
        for step_name in downstream_steps:
            step_index = text.index(f"      - name: {step_name}")
            assert preflight < step_index, f"{workflow_path.name}: rights preflight must precede {step_name}"
            step_block = text.split(f"      - name: {step_name}", 1)[1].split("\n      - name:", 1)[0]
            assert "steps.rights_preflight.outputs.allowed == 'true'" in step_block, (
                f"{workflow_path.name}: {step_name} must be skipped when rights are denied"
            )


def test_free_diagnostic_rechecks_quote_freshness_before_budget_and_marker():
    """A quote that expires between preflights must not consume a download marker."""
    text = FREE_DIAGNOSTIC_WORKFLOW.read_text(encoding="utf-8")
    initial = text.index("Preflight saved future pre-kickoff quotes (metadata only)")
    rights = text.index("Preflight frozen V2 source rights before source access")
    budget = text.index("Check shared public-source download budget")
    final = text.index(
        "Recheck saved future pre-kickoff quotes immediately before budget reservation"
    )
    marker = text.index("Upload shared public-source download attempt marker")
    fetch = text.index("Fetch and SHA-archive public source, preview original frozen V2 diagnostics")
    archive = text.index("Archive diagnostic and exact public CSV bytes for provenance")

    assert rights < initial < final < budget < marker < fetch < archive

    budget_block = text.split(
        "      - name: Check shared public-source download budget",
        1,
    )[1].split("\n      - name:", 1)[0]
    assert "steps.final_quote_preflight.outputs.eligible_quote_rows != '0'" in budget_block

    final_block = text.split(
        "      - name: Recheck saved future pre-kickoff quotes immediately before budget reservation",
        1,
    )[1].split("\n      - name:", 1)[0]
    assert "id: final_quote_preflight" in final_block
    assert "--preflight-only" in final_block
    assert "steps.rights_preflight.outputs.allowed == 'true'" in final_block
    assert "steps.quote_preflight.outputs.eligible_quote_rows != '0'" in final_block

    for step_name in (
        "Upload shared public-source download attempt marker",
        "Fetch and SHA-archive public source, preview original frozen V2 diagnostics",
        "Archive diagnostic and exact public CSV bytes for provenance",
    ):
        block = text.split(f"      - name: {step_name}", 1)[1].split("\n      - name:", 1)[0]
        assert "steps.final_quote_preflight.outputs.eligible_quote_rows != '0'" in block
