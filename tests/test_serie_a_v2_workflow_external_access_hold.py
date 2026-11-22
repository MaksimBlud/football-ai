"""Static contract tests for the temporary V2 live-access hold.

The current public main must not keep downloading provider CSVs, reading quote
snapshots, or publishing source archives while provider rights and private
artifact storage are unresolved. The workflows keep their offline tests and
existing schedules; live access is held and artifacts publish only after successful runs.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FLAG = "MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED"
LIVE_GATE = "${{ env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"
UPLOAD_GATE = "${{ success() && env.MARKET_ANCHOR_V2_LIVE_ACCESS_ALLOWED == 'true' }}"

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


def _step_condition(block: str) -> str:
    conditions = [
        line.strip()[len("if: "):]
        for line in block.splitlines()
        if line.strip().startswith("if: ")
    ]
    assert len(conditions) == 1, "each live/upload step must have exactly one condition"
    return conditions[0]


def _assert_live_condition(block: str, path: str, step_name: str) -> None:
    condition = _step_condition(block)
    assert f"env.{FLAG} == 'true'" in condition, (
        f"{path}: {step_name} must retain the workflow-level default-deny gate"
    )
    assert "steps.private-storage.outputs.is_private == 'true'" in condition, (
        f"{path}: {step_name} must also require verified private artifact storage"
    )


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
            _assert_live_condition(block, path, name)
        upload = _step_block(text, spec["upload"])
        condition = _step_condition(upload)
        assert "success()" in condition, (
            f"{path}: artifact publication must require successful preceding steps"
        )
        assert f"env.{FLAG} == 'true'" in condition, (
            f"{path}: artifact publication must retain the default-deny gate"
        )
        assert "steps.private-storage.outputs.is_private == 'true'" in condition, (
            f"{path}: artifact publication must require verified private storage"
        )


def test_failed_live_steps_cannot_publish_partial_artifacts():
    for path, spec in WORKFLOWS.items():
        upload = _step_block(_workflow(path), spec["upload"])
        assert "success()" in upload, (
            f"{path}: artifact upload must require successful preceding live steps"
        )
        assert "always()" not in upload, (
            f"{path}: failed live steps must never publish partial source/report artifacts"
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
            _assert_live_condition(block, path, step_name)
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
            assert index > 0, f"{path}: upload condition missing"
            condition_line = lines[index - 1].strip()
            assert condition_line.startswith("if: "), (
                f"{path}: every artifact upload must have an immediately preceding condition"
            )
            condition = condition_line[len("if: "):]
            assert "success()" in condition and f"env.{FLAG} == 'true'" in condition, (
                f"{path}: every artifact upload must require success and the default-deny gate"
            )
            assert "steps.private-storage.outputs.is_private == 'true'" in condition, (
                f"{path}: every artifact upload must require verified private storage"
            )


def test_candidate_recovery_cannot_download_or_publish_until_source_clearance():
    path = ".github/workflows/recover-market-anchor-v2-candidate.yml"
    text = _workflow(path)
    assert f'env:\n  {FLAG}: "false"' in text
    assert "workflow_dispatch:" in text
    assert "pytest -q tests/test_market_anchor_v2_saved_cohort_replay.py" not in text
    assert "py_compile market_anchor_v2_saved_cohort_replay.py" not in text
    rebuild = _step_block(text, "Rebuild September candidate from fixed 2016-2026 training input only")
    _assert_live_condition(rebuild, path, "candidate rebuild")
    proof = _step_block(text, "Prove frozen checksum, immutable recipe and research-only status")
    _assert_live_condition(proof, path, "candidate checksum proof")
    upload = _step_block(text, "Archive recovered frozen V2 research candidate")
    upload_condition = _step_condition(upload)
    assert "success()" in upload_condition
    assert f"env.{FLAG} == 'true'" in upload_condition
    assert "steps.private-storage.outputs.is_private == 'true'" in upload_condition
    assert "--restore-candidate-only" in rebuild
    assert "--save-research-candidate" in rebuild


EXTERNAL_IO_MARKERS = (
    # GitHub artifact transfers can read or publish research/source archives
    # without binding Supabase credentials or invoking a known V2 script.
    "actions/download-artifact@",
    "actions/upload-artifact@",
    # GitHub cache and Pages artifacts are also persistent repository storage.
    "actions/cache@",
    "actions/cache/restore@",
    "actions/cache/save@",
    "actions/upload-pages-artifact@",
    "actions/deploy-pages@",
    # Inline Octokit scripts and gh CLI artifact/release commands can access GitHub data
    # without spelling a token binding or invoking a known V2 Python script.
    "actions/github-script@",
    "gh run download",
    "gh release download",
    "gh release upload ",
    "gh api -x post ",
    "gh api --method post ",
    "gh api -x put ",
    "gh api --method put ",
    "gh api -x patch ",
    "gh api --method patch ",
    "git clone ",
    "git push ",
    "git lfs push",
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
    "curl -t ",
    "curl --upload-file ",
    "curl -x put ",
    "curl -x post ",
    "curl -x patch ",
    "curl --request put ",
    "curl --request post ",
    "curl --request patch ",
    "wget ",
    "wget --method=put ",
    "wget --method=post ",
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
    "aws s3 sync ",
    "aws s3api put-object",
    "gsutil cp ",
    "gsutil rsync ",
    "az storage blob download",
    "az storage blob upload",
    "az storage blob upload-batch",
    "rclone copy ",
    "rclone copyto ",
    "rclone sync ",
    "git lfs pull",
    "docker push ",
    "twine upload ",
    "npm publish",
    # Raw socket and remote-copy tools can transfer source data without HTTP clients.
    "nc ",
    "netcat ",
    "ncat ",
    "socat ",
    "telnet ",
    "openssl s_client",
    "ssh ",
    "scp ",
    "sftp ",
    "rsync ",
    "ftp ",
    "/dev/tcp/",
    "/dev/udp/",
    "git fetch https://",
    "git fetch git://",
    "git fetch ssh://",
    "git fetch git@",
    "git pull https://",
    "git pull git://",
    "git pull ssh://",
    "git pull git@",
    "git archive --remote",
    "docker pull ",
    "podman pull ",
    "azcopy copy ",
    "s3cmd get ",
    "s3cmd put ",
    "oras pull ",
    "crane pull ",
    # Compiled-language runtimes and explicit shell/container launchers can
    # perform network I/O without using the already-covered HTTP/socket CLIs.
    "go run ",
    "go test ",
    "cargo run ",
    "cargo test ",
    "rustc ",
    "java -jar ",
    "jshell ",
    "php ",
    "Rscript ",
    "julia ",
    "swift ",
    "dotnet ",
    "lua ",
    "luajit ",
    "bash ",
    "sh ",
    "zsh ",
    "fish ",
    "docker run ",
    "podman run ",
    "nerdctl run ",
    "ctr run ",
    "buildah run ",
)


def _has_external_io(text: str) -> bool:
    normalized = text.lower()
    return any(marker.lower() in normalized for marker in EXTERNAL_IO_MARKERS)


TRUSTED_OFFLINE_ACTIONS = frozenset({"actions/checkout", "actions/setup-python"})


def _has_unreviewed_action(text: str) -> bool:
    """Reject local, container, and third-party workflow actions in V2 workflows.

    A composite or marketplace action can perform network I/O without spelling
    a client, URL, credential, or Python entrypoint in the workflow YAML.
    Only the two narrowly used setup actions are treated as offline bootstrap.
    Artifact, cache, script, and all other actions remain external-access paths.
    """
    import re

    for line in text.splitlines():
        match = re.match(r"^\s*(?:-\s*)?uses:\s*([^\s]+)", line, re.IGNORECASE)
        if match is None:
            continue
        action = match.group(1).split("@", 1)[0].lower()
        if action not in TRUSTED_OFFLINE_ACTIONS:
            return True
    return False


UNREVIEWED_LAUNCHER_PATTERNS = (
    # Build/package runners can invoke local scripts with arbitrary network access.
    r"^\\s*(?:npm|yarn|pnpm)\\s+(?:run|exec|install|ci|start|build|test)\\b",
    r"^\\s*(?:make|gmake|just|task|gradle|mvn|bazel|buck)\\b",
    r"^\\s*(?:composer|bundle)\\s+exec\\b",
    r"^\\s*rake\\b",
    r"^\\s*mix\\s+(?:run|test)\\b",
    # Direct local launchers and sourced scripts are otherwise invisible to
    # the HTTP/socket marker inventory.
    r"^\\s*(?:\\./|source\\s+|\\.\\s+)\\S+",
)


def _has_unreviewed_launcher(text: str) -> bool:
    """Fail closed on build runners or local scripts in original-V2 workflows."""
    import re

    return any(
        re.search(pattern, line.strip(), re.IGNORECASE)
        for line in text.splitlines()
        for pattern in UNREVIEWED_LAUNCHER_PATTERNS
    )


ORIGINAL_V2_REFERENCE_MARKERS = (
    "serie_a_v2_",
    "serie-a-v2",
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


def _is_original_v2_live_workflow(text: str, workflow_path: str = "") -> bool:
    reference_surface = f"{text} {workflow_path}".lower()
    has_v2_reference = any(
        marker in reference_surface for marker in ORIGINAL_V2_REFERENCE_MARKERS
    )
    workflow_name = next(
        (
            line.split(":", 1)[1].strip().strip("\\\"'").lower()
            for line in text.splitlines()
            if line.strip().lower().startswith("name:")
        ),
        "",
    )
    identity = f"{workflow_name} {workflow_path.lower()}"
    has_v2_workflow_identity = any(
        marker in identity
        for marker in (
            "serie a v2",
            "serie-a-v2",
            "serie_a_v2",
            "market-anchor-v2",
            "market_anchor_v2",
            "market-anchor-1x2-v2",
            "market_anchor_1x2_v2",
        )
    )
    has_live_access = (
        "secrets.SUPABASE_URL" in text
        or "secrets.SUPABASE_KEY" in text
        or any(marker in text for marker in ORIGINAL_V2_LIVE_SCRIPT_MARKERS)
        or (
            has_v2_reference
            and has_v2_workflow_identity
            and (
                _has_external_io(text)
                or _has_non_test_python_entrypoint(text)
                or _has_unreviewed_action(text)
                or _has_unreviewed_launcher(text)
            )
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
    assert _has_external_io(
        "secrets.GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}"
    )


def test_external_io_inventory_recognizes_github_script_and_cli_download_paths():
    examples = (
        "uses: actions/github-script@v7\\nwith:\\n  script: await github.rest.actions.listArtifactsForRepo(...)",
        "run: gh run download 123456789",
        "run: gh release download v2.0.0",
        "run: git clone https://example.invalid/source.git",
    )
    assert all(_has_external_io(example) for example in examples)
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\\nuses: actions/github-script@v7"
    )


def test_external_io_inventory_recognizes_repository_storage_and_upload_paths():
    examples = (
        "uses: actions/cache@v4",
        "uses: actions/cache/restore@v4",
        "uses: actions/cache/save@v4",
        "uses: actions/upload-pages-artifact@v3",
        "uses: actions/deploy-pages@v4",
        "run: gh release upload v2.0.0 source.zip",
        "run: gh api -X POST repos/owner/repo/actions/artifacts",
        "run: gh api --method PUT repos/owner/repo/contents/source.csv",
        "run: git push origin main",
        "run: git lfs push origin main",
        "run: curl -T source.csv https://example.invalid/upload",
        "run: curl --upload-file source.csv https://example.invalid/upload",
        "run: curl -X PUT https://example.invalid/upload",
        "run: wget --method=POST https://example.invalid/upload",
        "run: aws s3 sync artifacts/ s3://bucket/",
        "run: aws s3api put-object --bucket bucket --key source.csv",
        "run: gsutil rsync artifacts/ gs://bucket/",
        "run: az storage blob upload --file source.csv",
        "run: rclone copyto source.csv remote:source.csv",
        "run: docker push registry.example.invalid/model:latest",
        "run: twine upload dist/*",
        "run: npm publish",
    )
    assert all(_has_external_io(example) for example in examples)
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\\nuses: actions/cache@v4"
    )


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


def test_external_io_inventory_recognizes_raw_socket_and_remote_transfer_paths():
    examples = (
        "run: nc -w 5 example.invalid 443",
        "run: netcat -zv example.invalid 443",
        "run: ncat example.invalid 443",
        "run: socat - TCP:example.invalid:443",
        "run: telnet example.invalid 443",
        "run: openssl s_client -connect example.invalid:443",
        "run: bash -c 'exec 3<>/dev/tcp/example.invalid/443'",
        "run: sh -c 'exec 3<>/dev/udp/example.invalid/443'",
        "run: ssh user@example.invalid",
        "run: scp source.csv user@example.invalid:/tmp/",
        "run: sftp user@example.invalid",
        "run: rsync source.csv user@example.invalid:/tmp/",
        "run: ftp example.invalid",
        "run: git fetch https://example.invalid/source.git",
        "run: git pull git://example.invalid/source.git main",
        "run: git fetch ssh://example.invalid/source.git",
        "run: git pull git@example.invalid:source.git main",
        "run: git archive --remote=https://example.invalid/source.git HEAD",
        "run: docker pull registry.example.invalid/source:latest",
        "run: podman pull registry.example.invalid/source:latest",
        "run: azcopy copy source.csv https://example.invalid/container",
        "run: s3cmd get s3://bucket/source.csv .",
        "run: s3cmd put source.csv s3://bucket/source.csv",
        "run: oras pull registry.example.invalid/source:latest",
        "run: crane pull registry.example.invalid/source:latest source.tar",
    )
    assert all(_has_external_io(example) for example in examples)
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\\nrun: nc -w 5 example.invalid 443"
    )
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\\nrun: bash -c 'exec 3<>/dev/tcp/example.invalid/443'"
    )


def test_external_io_inventory_recognizes_compiled_runtimes_shells_and_containers():
    examples = (
        "run: go run cmd/capture.go",
        "run: go test ./internal/source",
        "run: cargo run --bin source_capture",
        "run: cargo test --all",
        "run: rustc capture.rs && ./capture",
        "run: java -jar source-capture.jar",
        "run: jshell capture.jsh",
        "run: php capture.php",
        "run: Rscript capture.R",
        "run: julia capture.jl",
        "run: swift run SourceCapture",
        "run: dotnet run --project SourceCapture",
        "run: lua capture.lua",
        "run: luajit capture.lua",
        "run: bash capture.sh",
        "run: sh capture.sh",
        "run: zsh capture.zsh",
        "run: fish capture.fish",
        "run: docker run --network host source-capture:latest",
        "run: podman run source-capture:latest",
        "run: nerdctl run source-capture:latest",
        "run: ctr run source-capture:latest capture",
        "run: buildah run source-capture",
    )
    assert all(_has_external_io(example) for example in examples)
    assert _is_original_v2_live_workflow(
        "name: market-anchor-1x2-v2 source capture\\nrun: go run cmd/capture.go"
    )
    assert _is_original_v2_live_workflow(
        "name: serie-a-v2 source capture\\nrun: docker run source-capture:latest"
    )


def test_repository_metadata_fetch_for_pickle_diff_guard_is_not_provider_io():
    offline_validation = """
name: Market Anchor 1X2 V2 Shadow Validation
run: |
  git fetch origin main
  git diff --name-only origin/main...HEAD -- '*.pkl'
  python -m py_compile market_anchor_1x2_v2_shadow.py
  pytest -q tests/test_market_anchor_1x2_v2_shadow.py
"""
    assert not _has_external_io(offline_validation)
    assert not _is_original_v2_live_workflow(
        offline_validation,
        workflow_path=".github/workflows/market-anchor-1x2-v2-shadow-validation.yml",
    )


def test_live_v2_workflow_inventory_cannot_grow_around_the_hold():
    """New V2 live workflows must be added to the explicit fail-closed inventory."""
    workflow_dir = ROOT / ".github" / "workflows"
    discovered = set()
    for path in sorted(
        [*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]
    ):
        text = path.read_text(encoding="utf-8")
        relative_path = path.relative_to(ROOT).as_posix()
        if _is_original_v2_live_workflow(text, workflow_path=relative_path):
            discovered.add(relative_path)

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
    assert _is_original_v2_live_workflow(
        "name: Offline Helper\\nrun: python collect_unlisted_source.py",
        workflow_path=".github/workflows/serie-a-v2-source-capture.yml",
    )


def test_product_validation_with_v2_test_path_is_not_misclassified():
    product = """
name: Product PR Validation
run: |
  python -m pytest -q tests/test_serie_a_v2_dependency_lock_contract.py
"""
    assert not _is_original_v2_live_workflow(
        product,
        workflow_path=".github/workflows/product-pr-validation.yml",
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



def test_external_io_inventory_rejects_unreviewed_composite_and_marketplace_actions():
    examples = (
        "uses: ./.github/actions/source-capture",
        "uses: vendor/source-fetch@v1",
        "uses: docker://ghcr.io/vendor/source-capture:latest",
        "uses: actions/github-script@v7",
        "      - uses: ./.github/actions/source-capture",
        "      - uses: vendor/source-fetch@v1",
        "      - uses: docker://ghcr.io/vendor/source-capture:latest",
        "      - uses: actions/github-script@v7",
    )
    assert all(_has_unreviewed_action(example) for example in examples)
    assert all(
        _is_original_v2_live_workflow(
            f"name: serie-a-v2 source capture\n{example}"
        )
        for example in examples
    )


def test_offline_v2_bootstrap_actions_remain_allowed():
    offline = """
name: serie-a-v2 offline validation
steps:
  - uses: actions/checkout@11d5960a326750d5838078e36cf38b85af677262
  - uses: actions/setup-python@a26af69be951a213d495a4c3e4e4022e16d87065
  - run: python -m pytest -q tests/test_serie_a_v2_frozen_shadow_preview.py
"""
    assert not _has_unreviewed_action(offline)
    assert not _is_original_v2_live_workflow(offline)


def test_private_repository_preflight_is_present_read_only_and_precedes_live_steps():
    """Keep the private-storage preflight itself covered, not just its output reference."""
    guard_name = "Verify private repository storage before live V2 access"
    for path, spec in WORKFLOWS.items():
        source = _workflow(path)
        guard = _step_block(source, guard_name)

        assert guard.count("if:") == 1
        assert f"if: ${{{{ env.{FLAG} == 'true' }}}}" in guard
        assert "id: private-storage" in guard
        assert "GH_TOKEN: ${{ github.token }}" in guard
        assert 'private="$(gh api "repos/${GITHUB_REPOSITORY}" --jq \'.private\')"' in guard
        assert 'if [[ "$private" == "true" ]]; then' in guard
        assert 'gh api "repos/${GITHUB_REPOSITORY}" --jq \'.private\'' in guard
        assert 'echo "is_private=true" >> "$GITHUB_OUTPUT"' in guard
        assert 'echo "is_private=false" >> "$GITHUB_OUTPUT"' in guard

        guard_position = source.index(f"      - name: {guard_name}")
        first_live_position = min(
            source.index(f"      - name: {name}") for name in spec["live"]
        )
        assert guard_position < first_live_position, (
            f"{path}: private-storage preflight must precede every live source/quote step"
        )

        for name in spec["live"]:
            block = _step_block(source, name)
            assert "steps.private-storage.outputs.is_private == 'true'" in _step_condition(block)

        upload = _step_block(source, spec["upload"])
        assert "steps.private-storage.outputs.is_private == 'true'" in _step_condition(upload)



def test_unreviewed_build_and_local_script_launchers_are_live_capable():
    examples = (
        "run: npm run capture",
        "run: npm exec capture",
        "run: yarn run capture",
        "run: pnpm run capture",
        "run: make capture",
        "run: gmake capture",
        "run: just capture",
        "run: task capture",
        "run: gradle run",
        "run: mvn exec:java",
        "run: bazel run //:capture",
        "run: composer exec capture",
        "run: bundle exec ruby capture.rb",
        "run: rake capture",
        "run: mix run capture.exs",
        "run: ./scripts/capture.sh",
        "run: source scripts/capture.sh",
        "run: . scripts/capture.sh",
        """run: |
  npm run capture""",
        """run: |
  ./scripts/capture.sh""",
    )
    for example in examples:
        workflow = f"name: market-anchor-1x2-v2 source capture\\n{example}"
        assert _has_unreviewed_launcher(example)
        assert _is_original_v2_live_workflow(workflow)


def test_unreviewed_launcher_guard_preserves_offline_python_validation():
    offline = """name: market-anchor-1x2-v2 offline validation
run: |
  python -m py_compile market_anchor_1x2_v2_shadow.py
  python -m pytest -q tests/test_market_anchor_1x2_v2_shadow.py
"""
    assert not _has_unreviewed_launcher(offline)
    assert not _is_original_v2_live_workflow(offline)
