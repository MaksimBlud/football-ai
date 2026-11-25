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
