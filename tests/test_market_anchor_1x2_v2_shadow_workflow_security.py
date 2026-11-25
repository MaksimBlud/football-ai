"""Static security contract for the original V2 shadow validation workflow."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/market-anchor-1x2-v2-shadow-validation.yml"


def test_original_v2_shadow_validation_uses_pinned_actions_without_checkout_credentials():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803" in text
    assert "persist-credentials: false" in text
    assert "uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" in text
    assert "actions/checkout@v4" not in text
    assert "actions/setup-python@v5" not in text
    assert "permissions:\n  contents: read" in text
    assert "secrets." not in text
    assert "GITHUB_TOKEN" not in text
    assert "SUPABASE_URL" not in text
    assert "SUPABASE_KEY" not in text
    assert "schedule:" not in text

def test_recovery_workflow_pins_all_actions_and_disables_checkout_credentials():
    workflow = (ROOT / ".github/workflows/recover-market-anchor-v2-candidate.yml").read_text(
        encoding="utf-8"
    )
    action_refs = [
        line.strip().split("uses:", 1)[1].strip()
        for line in workflow.splitlines()
        if "uses:" in line
    ]
    assert action_refs == [
        "actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065",
        "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
    ]
    checkout_step = workflow.split(
        "      - uses: actions/checkout@11bd71901bbe5b1630ceea73d27597364c9af683",
        1,
    )[1].split("      - uses: actions/setup-python@", 1)[0]
    assert "persist-credentials: false" in checkout_step
    assert "fetch-depth: 0" in checkout_step
    assert "permissions:\\n  contents: read" in workflow
    assert "schedule:" not in workflow
    for forbidden in (
        "secrets.",
        "GITHUB_TOKEN",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "ODDS_API_KEY",
    ):
        assert forbidden not in workflow
