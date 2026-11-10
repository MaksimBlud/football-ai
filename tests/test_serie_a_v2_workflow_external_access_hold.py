"""Static contract tests for the temporary V2 live-access hold.

The current public main must not keep downloading provider CSVs, reading quote
snapshots, or publishing source archives while provider rights and private
artifact storage are unresolved. The workflows keep their offline tests and
existing schedules; only live access and its artifact upload are held.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAG = "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED"
LIVE_GATE = "${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"
UPLOAD_GATE = "${{ always() && env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"

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
            assert block.count("if:") == 1 and f"if: {LIVE_GATE}" in block, (
                f"{path}: live step must have exactly one fail-closed condition: {name}"
            )
        upload = _step_block(text, spec["upload"])
        assert upload.count("if:") == 1 and f"if: {UPLOAD_GATE}" in upload, (
            f"{path}: artifact publication must have exactly one fail-closed condition"
        )


def test_existing_daily_schedules_are_preserved():
    for path, spec in WORKFLOWS.items():
        text = _workflow(path)
        assert f'cron: "{spec["cron"]}"' in text, (
            f"{path}: existing schedule changed"
        )


def _job_env_block(text: str) -> str:
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line == "    env:"),
        None,
    )
    assert start is not None, "job-level env block missing"
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i] == "    steps:"),
        None,
    )
    assert end is not None, "job-level steps block missing"
    return "\n".join(lines[start:end])


CREDENTIAL_BINDINGS = {
    ".github/workflows/serie-a-v2-free-real-quote-diagnostic.yml": {
        "Fetch and SHA-archive public source, preview original frozen V2 diagnostics": {
            "SUPABASE_URL": "${{ secrets.SUPABASE_URL }}",
            "SUPABASE_KEY": "${{ secrets.SUPABASE_KEY }}",
        },
    },
    ".github/workflows/serie-a-v2-forward-preview.yml": {
        "Attest original historical source ZIP from real GitHub Actions (no quotes read)": {
            "GITHUB_TOKEN": "${{ github.token }}",
        },
        "Generate actual original frozen V2 source-verified read-only preview": {
            "SUPABASE_URL": "${{ secrets.SUPABASE_URL }}",
            "SUPABASE_KEY": "${{ secrets.SUPABASE_KEY }}",
            "GITHUB_TOKEN": "${{ github.token }}",
        },
    },
    ".github/workflows/serie-a-v2-current-form-source-capture.yml": {
        "Capture frozen historical seasons plus gated current-form source": {
            "SUPABASE_URL": "${{ secrets.SUPABASE_URL }}",
            "SUPABASE_KEY": "${{ secrets.SUPABASE_KEY }}",
        },
    },
    ".github/workflows/serie-a-v2-current-form-forward-preview.yml": {
        "Generate read-only current-form V2 shadow from already saved quotes": {
            "SUPABASE_URL": "${{ secrets.SUPABASE_URL }}",
            "SUPABASE_KEY": "${{ secrets.SUPABASE_KEY }}",
            "GITHUB_TOKEN": "${{ github.token }}",
        },
    },
}


def test_live_credentials_are_not_exposed_to_offline_steps():
    forbidden_job_credentials = (
        "SUPABASE_URL:",
        "SUPABASE_KEY:",
        "GITHUB_TOKEN:",
        "API_FOOTBALL_KEY:",
    )
    for path, step_bindings in CREDENTIAL_BINDINGS.items():
        text = _workflow(path)
        job_env = _job_env_block(text)
        for binding in forbidden_job_credentials:
            assert binding not in job_env, (
                f"{path}: credential {binding} must not be present in job-level env"
            )
        for step_name, bindings in step_bindings.items():
            block = _step_block(text, step_name)
            assert f"if: {LIVE_GATE}" in block, (
                f"{path}: credential-bearing step must remain fail-closed: {step_name}"
            )
            assert "        env:" in block, (
                f"{path}: live credentials must be step-scoped: {step_name}"
            )
            for name, value in bindings.items():
                assert f"{name}: {value}" in block, (
                    f"{path}: {name} must be scoped only to {step_name}"
                )


def test_live_access_hold_cannot_be_overridden_at_job_or_step_scope():
    for path in WORKFLOWS:
        text = _workflow(path)
        definitions = [
            line
            for line in text.splitlines()
            if line.lstrip().startswith(f"{FLAG}:")
        ]
        assert definitions == [f'  {FLAG}: "false"'], (
            f"{path}: the fail-closed flag must have exactly one workflow-level "
            "definition and must not be overridden by job/step env"
        )


def test_every_artifact_upload_in_live_workflows_is_gated():
    for path in WORKFLOWS:
        lines = _workflow(path).splitlines()
        upload_indices = [
            index
            for index, line in enumerate(lines)
            if line.strip().startswith("uses: actions/upload-artifact@")
        ]
        assert upload_indices, f"{path}: expected at least one artifact upload"
        for index in upload_indices:
            assert index > 0 and lines[index - 1].strip() == f"if: {UPLOAD_GATE}", (
                f"{path}: every artifact upload must be gated, not only a named upload step"
            )
