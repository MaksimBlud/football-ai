"""Supply-chain regression for the original frozen V2 test workflow."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "serie-a-frozen-v2-shadow-tests.yml"

CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"


def test_frozen_v2_shadow_workflow_pins_verified_actions():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert source.count(f"uses: actions/checkout@{CHECKOUT_SHA}") == 1
    assert source.count(f"uses: actions/setup-python@{SETUP_PYTHON_SHA}") == 1
    assert "uses: actions/checkout@v4" not in source
    assert "uses: actions/setup-python@v5" not in source
