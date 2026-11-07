from pathlib import Path
import os
import subprocess
import textwrap


WORKFLOWS = (
    "eredivisie-odds-snapshots.yml",
    "eredivisie-live-cycle.yml",
    "eredivisie-results.yml",
)


def _read(name: str) -> str:
    return (Path(__file__).parents[1] / ".github" / "workflows" / name).read_text()


def test_operational_workflows_enforce_market_only_safety():
    for name in WORKFLOWS:
        source = _read(name)
        assert 'CALIBRATION_REQUIRED' in source
        assert 'structural_alpha is None' in source
        assert 'edge_threshold is None' in source
        assert 'Eredivisie remains MARKET_ONLY' in source


def test_operational_workflows_do_not_load_or_train_production_models():
    forbidden = (
        "football_model_xgboost_elo.pkl",
        "joblib.load",
        "train_model",
        "--production",
    )
    for name in WORKFLOWS:
        source = _read(name)
        for token in forbidden:
            assert token not in source


def test_paid_eredivisie_odds_is_manual_only_and_guarded():
    odds = _read("eredivisie-odds-snapshots.yml")
    assert "workflow_dispatch:" in odds
    assert "cron:" not in odds
    assert "push:" not in odds
    assert "python odds_api_budget_guard.py --max-cost 1" in odds


def test_eredivisie_results_are_provider_free_and_scheduled():
    results = _read("eredivisie-results.yml")
    assert "workflow_dispatch:" in results
    assert 'cron: "23 */12 * * *"' in results
    assert "THE_ODDS_API_KEY" not in results
    assert "odds_api_budget_guard.py" not in results
    assert 'source.provider == "FOOTBALL_DATA_CSV"' in results
    assert 'source.competition_code == "N1"' in results
    assert 'source.season_code == "2627"' in results

    # The downstream live cycle works from already persisted state and remains scheduled.
    assert 'cron: "58 */2 * * *"' in _read("eredivisie-live-cycle.yml")


def test_eredivisie_odds_does_not_collide_with_ligue1_live_cycle():
    ligue1_live = _read("ligue1-live-cycle.yml")
    assert 'cron: "33 */2 * * *"' in ligue1_live
    assert 'cron: "33 */2 * * *"' not in _read("eredivisie-odds-snapshots.yml")



def test_v2_research_and_serie_a_pickle_guards_fail_closed():
    for name in ("research-pr-validation.yml", "serie-a-pr-validation.yml"):
        source = _read(name)
        assert "fetch-depth: 0" in source
        assert "BASE_REF: ${{ github.base_ref || 'main' }}" in source
        assert 'git fetch --no-tags origin "+refs/heads/${BASE_REF}:refs/remotes/origin/${BASE_REF}"' in source
        assert 'git merge-base "refs/remotes/origin/${BASE_REF}" HEAD' in source
        assert "FAIL_CLOSED: unable to determine merge base for production artifact diff" in source
        assert 'git diff --name-only "$BASE_COMMIT" HEAD' in source
        assert "FAIL_CLOSED: unable to inspect changed files for production artifact diff" in source
        assert "origin/main...HEAD" not in source
        assert 'git diff --name-only "origin/' not in source
        assert "grep -F '.pkl'" in source


def test_v2_pickle_guard_shell_blocks_are_valid_bash():
    for name in ("research-pr-validation.yml", "serie-a-pr-validation.yml"):
        source = _read(name)
        marker = "      - name: Enforce no production artifact changes" + chr(10)
        assert marker in source
        step = source.split(marker, 1)[1]
        run_marker = "        run: |" + chr(10)
        assert run_marker in step
        script = textwrap.dedent(step.split(run_marker, 1)[1])
        parsed = subprocess.run(
            ["bash", "-n"],
            input=script,
            text=True,
            capture_output=True,
            check=False,
        )
        assert parsed.returncode == 0, parsed.stderr


def _extract_v2_pickle_guard_script(name: str) -> str:
    source = _read(name)
    marker = "      - name: Enforce no production artifact changes" + chr(10)
    assert marker in source
    step = source.split(marker, 1)[1]
    run_marker = "        run: |" + chr(10)
    assert run_marker in step
    script = textwrap.dedent(step.split(run_marker, 1)[1])
    return script


def _run_v2_pickle_guard(script: str, tmp_path: Path, *, mode: str, changed_files: str = "safe.py"):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir(parents=True, exist_ok=True)
    fake_git = fake_bin / "git"
    fake_git.write_text(
        "#!/bin/sh\n"
        + textwrap.dedent("""
            case "$1" in
              fetch)
                [ "$FAKE_GIT_MODE" != "fetch-error" ] || exit 9
                exit 0
                ;;
              merge-base)
                if [ "$FAKE_GIT_MODE" = "merge-base-error" ]; then
                  printf '%s\n' "simulated missing merge base" >&2
                  exit 1
                fi
                if [ "$FAKE_GIT_MODE" = "merge-base-empty" ]; then
                  exit 0
                fi
                printf '%s\n' "deadbeef"
                exit 0
                ;;
              diff)
                [ "$FAKE_GIT_MODE" != "diff-error" ] || exit 8
                printf '%s\n' "$FAKE_CHANGED_FILES"
                exit 0
                ;;
              *)
                exit 90
                ;;
            esac
        """).lstrip("\n")
    )
    fake_git.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")
    env["BASE_REF"] = "main"
    env["FAKE_GIT_MODE"] = mode
    env["FAKE_CHANGED_FILES"] = changed_files
    return subprocess.run(
        ["bash", "-e", "-o", "pipefail", "-c", script],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_v2_pickle_guard_executes_fail_closed_cases(tmp_path):
    cases = (
        ("fetch-error", "safe.py", None),
        ("merge-base-error", "safe.py", "FAIL_CLOSED: unable to determine merge base for production artifact diff"),
        ("merge-base-empty", "safe.py", "FAIL_CLOSED: unable to determine merge base for production artifact diff"),
        ("diff-error", "safe.py", "FAIL_CLOSED: unable to inspect changed files for production artifact diff"),
        ("pkl", "models/production.pkl", "Production model artifact change detected"),
    )
    for workflow in ("research-pr-validation.yml", "serie-a-pr-validation.yml"):
        script = _extract_v2_pickle_guard_script(workflow)
        for index, (mode, changed_files, expected) in enumerate(cases):
            result = _run_v2_pickle_guard(
                script, tmp_path / workflow.replace("/", "_") / str(index),
                mode=mode, changed_files=changed_files,
            )
            assert result.returncode != 0, (workflow, mode, result.stdout, result.stderr)
            if expected:
                assert expected in result.stdout + result.stderr, (
                    workflow, mode, result.stdout, result.stderr
                )
            assert "PASS: no .pkl changes in PR" not in result.stdout
        success = _run_v2_pickle_guard(
            script, tmp_path / workflow.replace("/", "_") / "success",
            mode="success", changed_files="safe.py",
        )
        assert success.returncode == 0, (workflow, success.stdout, success.stderr)
        assert "PASS: no .pkl changes in PR" in success.stdout
