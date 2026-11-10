"""Static contract tests for the temporary V2 live-access hold.

The current public main must not keep downloading provider CSVs, reading quote
snapshots, or publishing source archives while provider rights and private
artifact storage are unresolved. The workflows keep their offline tests and
existing schedules; only live access and its artifact upload are held.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAG = "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED"
LIVE_GATE = "\${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"
UPLOAD_GATE = "\${{ always() && env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"

WORKFLOWS = {
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml": {
        "cron": "13 6 * * *",
        "live": (
            "Fetch and SHA-archive public source, preview original frozen V2 diagnostics",
        ),
        "upload": "Archive diagnostic and exact public CSV bytes for provenance",
    },
    ".github/workflows/serie-a-v2-forward-preview.yml": {
        "cron": "8 8 * * *",
        "live": (
            "Attest original historical source ZIP from real GitHub Actions (no quotes read)",
            "Generate actual original frozen V2 source-verified read-only preview",
        ),
        "upload": "Save immutable original V2 predictions and exact older source bytes",
    },
    ".github/workflows/serie-a-v2-current-form-source-capture.yml": {
        "cron": "50 5 * * *",
        "live": (
            "Capture frozen historical seasons plus gated current-form source",
        ),
        "upload": "Archive source bytes and gate manifest for future quotes only",
    },
    ".github/workflows/serie-a-v2-current-form-forward-preview.yml": {
        "cron": "18 8 * * *",
        "live": (
            "Generate read-only current-form V2 shadow from already saved quotes",
        ),
        "upload": "Archive pre-kickoff V2 shadow and exact source ZIPs",
    },
}


def _workflow(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _step_block(text: str, name: str) -> str:
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line == f"      - name: {name}"),
        None,
    )
    assert start is not None, f"workflow step missing: {name}"
    end = next(
        (
            i
            for i in range(start + 1, len(lines))
            if lines[i].startswith("      - name: ")
            or lines[i].startswith("      - uses: ")
        ),
        len(lines),
    )
    return "\n".join(lines[start:end])


def test_all_live_v2_workflows_default_to_external_access_disabled():
    for path in WORKFLOWS:
        text = _workflow(path)
        assert f'env:\n  {FLAG}: "false"' in text, (
            f"{path} must default to a workflow-level fail-closed flag"
        )


def test_live_steps_and_public_artifact_uploads_are_gated():
    for path, spec in WORKFLOWS.items():
        text = _workflow(path)
        for name in spec["live"]:
            block = _step_block(text, name)
            assert f"if: {LIVE_GATE}" in block, (
                f"{path}: live step is not held: {name}"
            )
        upload = _step_block(text, spec["upload"])
        assert f"if: {UPLOAD_GATE}" in upload, (
            f"{path}: artifact publication is not held"
        )


def test_existing_daily_schedules_are_preserved():
    for path, spec in WORKFLOWS.items():
        text = _workflow(path)
        assert f'cron: "{spec["cron"]}"' in text, (
            f"{path}: existing schedule changed"
        )
