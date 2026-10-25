"""Regression checks for the free current-form source-capture workflow contract."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-v2-current-form-source-capture.yml"


def test_push_path_filter_covers_frozen_source_dependencies():
    text = WORKFLOW.read_text(encoding="utf-8")
    push_block = text.split("  push:\n", 1)[1].split("\n\nconcurrency:", 1)[0]
    paths = set(re.findall(r'^\s+- "([^"]+)"\s*$', push_block, flags=re.MULTILINE))
    required = {
        "serie_a_v2_current_form_source_capture.py",
        "experiments/market_anchor_1x2_v2_current_form_policy.json",
        "research/models/market_anchor_v2_serie_a_frozen_candidate.json",
        "historical_football_signal_lab.py",
        "serie_a_runtime_config.py",
        "serie_a_v2_frozen_shadow_preview.py",
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
    assert required <= paths, f"current-form source workflow misses push triggers: {sorted(required - paths)}"


def test_workflow_runs_the_frozen_feature_and_capture_regressions():
    text = WORKFLOW.read_text(encoding="utf-8")
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
        f"workflow does not run required source/feature regression tests: "
        f"{sorted(name for name in required_tests if name not in validation)}"
    )
