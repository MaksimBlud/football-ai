"""Regression checks for the free original/current-form V2 workflow contracts."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SOURCE_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-current-form-source-capture.yml"
ORIGINAL_FORWARD_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-forward-preview.yml"
FROZEN_SHADOW_WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-frozen-v2-shadow-tests.yml"


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
