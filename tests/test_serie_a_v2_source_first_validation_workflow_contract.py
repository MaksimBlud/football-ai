"""Static supply-chain contract for the original V2 source-first validation workflow.

The exact action commits below are the upstream-verified Node 24 commits already
used by the held V2 workflow chain. This test is offline and never contacts a
provider, reads quotes, accesses Supabase, or invokes the model.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/market-anchor-v2-original-forward-source-first-validation.yml"
TEST_PATH = 'tests/test_serie_a_v2_source_first_validation_workflow_contract.py'
BRANCH = "research/v2-source-first-validator-node24-pins-on-949-20261124-run11"

EXPECTED_USES = [
    "actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803",
    "actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1",
]


def test_source_first_validation_uses_only_exact_upstream_verified_node24_actions():
    text = WORKFLOW.read_text(encoding="utf-8")
    actual = re.findall(r"^\s*uses:\s*([^\s]+)\s*$", text, flags=re.MULTILINE)
    assert actual == EXPECTED_USES
    assert "actions/checkout@11d5960a326750d5838078e36cf38b85af677262" not in text
    assert "actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065" not in text
    assert not re.search(r"^\s*uses:\s*actions/(?:checkout|setup-python)@v\d+\s*$", text, re.MULTILINE)


def test_source_first_validator_runs_this_contract_test_on_push_and_pull_request():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert text.count(f'      - "{TEST_PATH}"') == 2
    assert f"            {TEST_PATH}" in text
    assert f"      - {BRANCH}" in text


def test_source_first_validator_is_read_only_and_cannot_access_live_data_or_publish_artifacts():
    text = WORKFLOW.read_text(encoding="utf-8")
    permissions = re.search(
        r"(?ms)^permissions:\\n((?:[ \\t]+[^\\n]*\\n)+)", text
    )
    assert permissions is not None
    assert permissions.group(1).splitlines() == ["  contents: read"]

    # This isolated validator must remain offline with no provider/database token scope.
    for forbidden in (
        "secrets.",
        "SUPABASE_",
        "THE_ODDS_API",
        "GITHUB_TOKEN",
        "${{ github.token }}",
    ):
        assert forbidden not in text

    # Only push and pull_request are permitted; no scheduled or manually
    # dispatched entrypoint may turn this validator into a live workflow.
    assert not re.search(
        r"(?m)^\\s+(?:schedule|workflow_dispatch|workflow_run):", text
    )
    assert not re.search(
        r"(?m)^\\s*uses:\\s*actions/(?:upload|download)-artifact@", text
    )

    checkout = re.search(
        r"(?ms)^      - name: Checkout exact research branch\\n"
        r"(?P<body>.*?)(?=^      - name:|\\Z)",
        text,
    )
    assert checkout is not None
    assert "persist-credentials: false" in checkout.group("body")
