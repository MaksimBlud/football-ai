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
    ".github/workflows/recover-market-anchor-v2-candidate.yml": {
        "cron": None,
        "live": (
            "Rebuild September candidate from fixed 2016-2026 training input only",
            "Prove frozen checksum, immutable recipe and research-only status",
        ),
        "upload": "Archive recovered frozen V2 research candidate",
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
        if spec["cron"] is None:
            continue
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
    ".github/workflows/recover-market-anchor-v2-candidate.yml": {},
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


def test_candidate_recovery_cannot_download_or_publish_until_source_clearance():
    path = ".github/workflows/recover-market-anchor-v2-candidate.yml"
    text = _workflow(path)
    assert f'env:\n  {FLAG}: "false"' in text
    assert "workflow_dispatch:" in text
    assert "pytest -q tests/test_market_anchor_v2_saved_cohort_replay.py" not in text
    assert "py_compile market_anchor_v2_saved_cohort_replay.py" not in text
    rebuild = _step_block(text, "Rebuild September candidate from fixed 2016-2026 training input only")
    assert f"if: {LIVE_GATE}" in rebuild
    proof = _step_block(text, "Prove frozen checksum, immutable recipe and research-only status")
    assert f"if: {LIVE_GATE}" in proof
    upload = _step_block(text, "Archive recovered frozen V2 research candidate")
    assert f"if: {UPLOAD_GATE}" in upload
    assert "--restore-candidate-only" in rebuild
    assert "--save-research-candidate" in rebuild


EXTERNAL_IO_MARKERS = (
    # GitHub artifact transfers can read or publish research/source archives
    # without binding Supabase credentials or invoking a known V2 script.
    "actions/download-artifact@",
    "actions/upload-artifact@",
    # GitHub API access can discover/download public artifacts directly.
    "secrets.GITHUB_TOKEN",
    "${{ github.token }}",
    "GITHUB_TOKEN:",
    "gh api ",
    # Direct HTTP clients/commands are also external data access paths.
    "requests.get(",
    "requests.post(",
    "httpx.",
    "aiohttp",
    "urllib3.",
    "http.client",
    "urllib.request",
    "curl ",
    "wget ",
    "fetch(",
    "axios.",
    # Alternate runtimes can perform the same network/artifact access without
    # importing a Python HTTP client or spelling curl/wget.
    "node ",
    "nodejs ",
    "npx ",
    "deno ",
    "bun ",
    "ruby ",
    "perl ",
    "pwsh ",
    "powershell ",
    "invoke-webrequest",
    "invoke-restmethod",
    # Common object-store / repository-data transfer commands.
    "aws s3 cp ",
    "gsutil cp ",
    "az storage blob download",
    "rclone copy ",
    "git lfs pull",
)


def _has_external_io(text: str) -> bool:
    return any(marker in text for marker in EXTERNAL_IO_MARKERS)


ORIGINAL_V2_REFERENCE_MARKERS = (
    "serie_a_v2_",
    "market_anchor_v2_",
    # The original model's canonical module family includes the 1X2 token.
    # The hyphenated workflow identity is also used by its validation workflow.
    "market_anchor_1x2_v2_",
    "market-anchor-1x2-v2",
)
ORIGINAL_V2_LIVE_SCRIPT_MARKERS = (
    "python serie_a_v2_current_form_source_capture.py",
    "python serie_a_v2_current_form_forward_capture.py",
    "python serie_a_v2_forward_capture.py",
    "python serie_a_v2_attest_real_source.py",
    "python market_anchor_v2_saved_cohort_replay.py",
    "python market_anchor_1x2_v2_",
    "python -m market_anchor_1x2_v2_",
)


def _has_non_test_python_entrypoint(text: str) -> bool:
    """Treat arbitrary Python execution in an original-V2 workflow as live-capable.

    Only dependency installation, compilation and pytest are offline workflow
    commands. A new helper script can perform network I/O without spelling an
    HTTP client or credential in the YAML, so it must not escape the inventory.
    """
    import re

    for line in text.splitlines():
        command = line.strip()
        if not command or command.startswith("#"):
            continue
        invocation = re.search(r"\bpython(?:3(?:\.\d+)?)?\s+", command)
        if invocation is None:
            continue
        command = command[invocation.start():]
        if re.match(
            r"^python(?:3(?:\.\d+)?)?\s+-m\s+(?:pip|pytest|py_compile)\b",
            command,
        ):
            continue
        return True
    return False


def _is_original_v2_live_workflow(text: str) -> bool:
    has_v2_reference = any(marker in text for marker in ORIGINAL_V2_REFERENCE_MARKERS)
    has_live_access = (
        "secrets.SUPABASE_URL" in text
        or "secrets.SUPABASE_KEY" in text
        or any(marker in text for marker in ORIGINAL_V2_LIVE_SCRIPT_MARKERS)
        or _has_external_io(text)
        or (
            has_v2_reference
            and _has_non_test_python_entrypoint(text)
        )
    )
    return has_v2_reference and has_live_access


def test_external_io_inventory_recognizes_common_artifact_and_network_paths():
    examples = (
        "uses: actions/download-artifact@v4",
        "uses: actions/upload-artifact@v4",
        "GITHUB_TOKEN: ${{ github.token }}",
        "run: gh api repos/MaksimBlud/football-ai/actions/artifacts",
        "run: curl https://example.invalid/source.csv",
        "run: wget https://example.invalid/source.csv",
        "python -c 'requests.get(url)'",
        "python -c 'urllib.request.urlopen(url)'",
    )
    assert all(_has_external_io(example) for example in examples)


def test_external_io_inventory_recognizes_alternate_runtimes_and_http_clients():
    examples = (
        "run: node scripts/capture.js",
        "run: npx tsx scripts/capture.ts",
        "run: deno run scripts/capture.ts",
        "run: bun run scripts/capture.ts",
        "run: pwsh -File capture.ps1",
        "run: Invoke-WebRequest https://example.invalid/source.csv",
        "python -c 'httpx.get(url)'",
        "python -c 'aiohttp.ClientSession()'",
        "python -c 'urllib3.PoolManager()'",
        "python -c 'http.client.HTTPSConnection(host)'",
        "python -c 'fetch(url)'",
        "python -c 'axios.get(url)'",
        "run: aws s3 cp s3://bucket/source.csv .",
        "run: gsutil cp gs://bucket/source.csv .",
        "run: git lfs pull",
    )
    assert all(_has_external_io(example) for example in examples)


def test_live_v2_workflow_inventory_cannot_grow_around_the_hold():
    """New V2 live workflows must be added to the explicit fail-closed inventory."""
    workflow_dir = ROOT / ".github" / "workflows"
    discovered = set()
    for path in sorted(
        [*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]
    ):
        text = path.read_text(encoding="utf-8")
        if _is_original_v2_live_workflow(text):
            discovered.add(path.relative_to(ROOT).as_posix())

    unexpected = discovered - set(WORKFLOWS)
    assert not unexpected, (
        "New V2 live-access workflow(s) bypass the explicit fail-closed "
        f"inventory: {sorted(unexpected)}"
    )



def test_original_market_anchor_1x2_v2_script_cannot_escape_live_workflow_inventory():
    # These original-model entrypoint forms must be recognized even when a new
    # workflow does not mention the older serie_a_v2_ or market_anchor_v2_ names.
    assert _is_original_v2_live_workflow(
        "run: python market_anchor_1x2_v2_forward_capture.py"
    )
    assert _is_original_v2_live_workflow(
        "run: python -m market_anchor_1x2_v2_prospective_runner"
    )


def test_serie_a_v2_workflow_with_unknown_python_helper_is_live_capable():
    # Generic helper names are not exempt just because the workflow only uses
    # the broad serie_a_v2_ family marker rather than the canonical 1X2 token.
    assert _is_original_v2_live_workflow(
        "name: serie_a_v2_source_runner\\nrun: python collect_unlisted_source.py"
    )


def test_original_market_anchor_1x2_v2_offline_validation_remains_allowed():
    # The existing pull-request-only frozen V2 test workflow compiles the
    # module and runs pytest; neither action is a live source/quote entrypoint.
    assert not _is_original_v2_live_workflow(
        "run: python -m py_compile market_anchor_1x2_v2_shadow.py"
    )
    assert not _is_original_v2_live_workflow(
        "run: pytest -q tests/test_market_anchor_1x2_v2_shadow.py"
    )



def test_hyphenated_original_v2_workflow_with_unknown_python_script_is_live_capable():
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\nrun: python collect_source.py"
    )


def test_original_v2_pytest_and_compile_workflows_are_not_live_entrypoints():
    offline = """
name: market-anchor-1x2-v2-shadow-validation
run: |
  python -m py_compile market_anchor_1x2_v2_shadow.py
  python -m pytest -q tests/test_market_anchor_1x2_v2_shadow.py
"""
    assert not _is_original_v2_live_workflow(offline)
