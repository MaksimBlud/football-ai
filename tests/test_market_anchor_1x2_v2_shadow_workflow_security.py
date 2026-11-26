"""Static security contracts for the original V2 shadow and recovery workflows."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHADOW = ROOT / ".github/workflows/market-anchor-1x2-v2-shadow-validation.yml"
RECOVERY = ROOT / ".github/workflows/recover-market-anchor-v2-candidate.yml"


def _action_refs(text: str) -> list[str]:
    return [
        line.strip().split("uses:", 1)[1].strip()
        for line in text.splitlines()
        if "uses:" in line
    ]


def test_original_v2_shadow_validation_pins_actions_and_does_not_persist_checkout_credentials():
    workflow = SHADOW.read_text(encoding="utf-8")
    assert _action_refs(workflow) == [
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
        "actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548",
    ]
    checkout = workflow.split("      - uses: actions/checkout@", 1)[1].split(
        "      - uses: actions/setup-python@", 1
    )[0]
    assert "persist-credentials: false" in checkout
    assert "fetch-depth: 0" in checkout
    assert "permissions:\n  contents: read" in workflow
    assert "secrets." not in workflow
    assert "GITHUB_TOKEN" not in workflow
    assert "SUPABASE_URL" not in workflow
    assert "SUPABASE_KEY" not in workflow
    assert "schedule:" not in workflow


def test_recovery_workflow_keeps_candidate_rebuild_default_denied_and_all_actions_pinned():
    workflow = RECOVERY.read_text(encoding="utf-8")
    assert _action_refs(workflow) == [
        "actions/checkout@de0fac2e4500dabe0009e67214ff5f5447ce83dd",
        "actions/setup-python@83679a892e2d95755f2dac6acb0bfd1e9ac5d548",
        "actions/upload-artifact@b7c566a772e6b6bfb58ed0dc250532a479d7789f",
    ]
    checkout = workflow.split("      - uses: actions/checkout@", 1)[1].split(
        "      - uses: actions/setup-python@", 1
    )[0]
    assert "persist-credentials: false" in checkout
    assert "fetch-depth: 0" in checkout
    assert 'MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED: "false"' in workflow
    assert "permissions:\n  contents: read" in workflow
    assert "schedule:" not in workflow
    assert "secrets." not in workflow
    assert "GITHUB_TOKEN" not in workflow
    assert "SUPABASE_URL" not in workflow
    assert "SUPABASE_KEY" not in workflow
    assert "ODDS_API_KEY" not in workflow

    rebuild_start = workflow.index("      - name: Rebuild September candidate")
    proof_start = workflow.index("      - name: Prove frozen checksum", rebuild_start)
    rebuild_block = workflow[rebuild_start:proof_start]
    required_gate = "if: ${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' && steps.private-storage.outputs.is_private == 'true' }}"
    assert required_gate in rebuild_block
    archive_start = workflow.index("      - name: Archive recovered frozen V2 research candidate")
    archive_block = workflow[archive_start:]
    assert "if: ${{ success() && env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' && steps.private-storage.outputs.is_private == 'true' }}" in archive_block



def test_shadow_validation_uses_fetched_origin_main_without_post_checkout_network_access():
    workflow = SHADOW.read_text(encoding="utf-8")
    checkout = workflow.split("      - uses: actions/checkout@", 1)[1].split(
        "      - uses: actions/setup-python@", 1
    )[0]
    assert "fetch-depth: 0" in checkout
    assert "persist-credentials: false" in checkout
    assert "git fetch origin main" not in workflow
    assert "git diff --name-only origin/main...HEAD -- '*.pkl'" in workflow


def test_continuity_updates_trigger_frozen_shadow_validation():
    workflow = SHADOW.read_text(encoding="utf-8")
    pull_request_paths = workflow.split("  pull_request:", 1)[1].split("\npermissions:", 1)[0]
    assert '"PROJECT_CONTINUITY.md"' in pull_request_paths
