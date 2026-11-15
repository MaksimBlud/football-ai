"""Supply-chain regressions for the original MARKET_ANCHOR_1X2_V2 core CI."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-1x2-v2-shadow-validation.yml"

CHECKOUT_SHA = "11d5960a326750d5838078e36cf38b85af677262"
SETUP_PYTHON_SHA = "a26af69be951a213d495a4c3e4e4022e16d87065"


def test_original_v2_shadow_validation_pins_actions_to_verified_commits():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert source.count(f"uses: actions/checkout@{CHECKOUT_SHA}") == 1
    assert source.count(f"uses: actions/setup-python@{SETUP_PYTHON_SHA}") == 1
    assert "uses: actions/checkout@v4" not in source
    assert "uses: actions/setup-python@v5" not in source
