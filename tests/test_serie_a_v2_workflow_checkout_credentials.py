"""Ensure original V2 workflows do not persist checkout credentials.

These workflows use explicit, step-scoped GitHub API tokens where required.
Persisting checkout credentials in .git/config is unnecessary and increases
the impact of later scripts or dependencies running in the same job.
"""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CHECKOUT_SHA = "d23441a48e516b6c34aea4fa41551a30e30af803"
WORKFLOWS = (
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml",
    ".github/workflows/serie-a-v2-forward-preview.yml",
    ".github/workflows/serie-a-v2-current-form-source-capture.yml",
    ".github/workflows/serie-a-v2-current-form-forward-preview.yml",
    ".github/workflows/recover-market-anchor-v2-candidate.yml",
    ".github/workflows/serie-a-frozen-v2-shadow-tests.yml",
)


def _checkout_step(text: str) -> str:
    lines = text.splitlines()
    starts = [
        i for i, line in enumerate(lines)
        if re.match(r"^\s*-\s*uses:\s*actions/checkout@", line)
    ]
    assert len(starts) == 1, f"expected exactly one checkout step, found {len(starts)}"
    start = starts[0]
    end = next(
        (i for i in range(start + 1, len(lines)) if re.match(r"^\s*-\s+", lines[i])),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_every_held_original_v2_workflow_disables_persisted_checkout_credentials():
    for relative in WORKFLOWS:
        text = (ROOT / relative).read_text(encoding="utf-8")
        step = _checkout_step(text)
        assert f"actions/checkout@{CHECKOUT_SHA}" in step, relative
        assert re.search(r"^\s*with:\s*$", step, flags=re.MULTILINE), relative
        assert re.search(
            r"^\s*persist-credentials:\s*false\s*$",
            step,
            flags=re.MULTILINE,
        ), f"{relative}: checkout token must not be persisted in local git config"


def test_validator_checks_runtime_git_config_after_checkout():
    workflow = (ROOT / ".github/workflows/market-anchor-v2-checkout-credential-isolation.yml").read_text(encoding="utf-8")
    assert "persist-credentials: false" in workflow
    assert "git config --local --get-all http.https://github.com/.extraheader" in workflow
    assert "git config --local --get-regexp '^includeIf\\.gitdir:'" in workflow
    assert "secrets." not in workflow
    assert "GITHUB_TOKEN" not in workflow
