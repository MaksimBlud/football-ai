from pathlib import Path


V4 = Path(".github/workflows/research-orchestrator-v4.yml")
V3 = Path(".github/workflows/research-agent-v3-gemini.yml")
V2 = Path(".github/workflows/research-agent-v2-issue-intake.yml")
HEARTBEAT = Path(".github/workflows/research-v4-heartbeat.yml")


def _v4() -> str:
    return V4.read_text(encoding="utf-8")


def _v3() -> str:
    return V3.read_text(encoding="utf-8")


def _v2() -> str:
    return V2.read_text(encoding="utf-8")


def _heartbeat() -> str:
    return HEARTBEAT.read_text(encoding="utf-8")


def test_v4_globally_queues_gemini_workers_fifo():
    text = _v4()
    worker = text.split("  worker:", 1)[1]
    assert "concurrency:" in worker
    assert "group: research-v4-global-gemini" in worker
    assert "queue: max" in worker
    assert "cancel-in-progress: true" not in worker


def test_v4_queue_labels_are_visible_until_worker_starts():
    text = _v4()
    preflight = text.split("  preflight:", 1)[1].split("  worker:", 1)[0]
    worker = text.split("  worker:", 1)[1]
    assert "ensure_label research-v4-queued" in preflight
    assert "--add-label research-v4-running --add-label research-v4-queued" in preflight
    assert "Mark global queue slot active" in worker
    assert "--remove-label research-v4-queued" in worker


def test_v4_scheduler_retries_only_quota_waiting_issues():
    text = _v4()
    sweep = text.split("  sweep:", 1)[1].split("  preflight:", 1)[0]
    assert "--label research-v4-waiting" in sweep
    assert "--label research-v4-running --limit" not in sweep


def test_v4_has_issue_dispatch_schedule_and_pr_contract_triggers():
    text = _v4()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" in on_block
    assert "workflow_dispatch:" in on_block
    assert "schedule:" in on_block
    assert "pull_request:" in on_block


def test_v4_uses_groq_primary_and_one_gemini_emergency_fallback():
    text = _v4()
    assert "Groq primary pass" in text
    assert "research_agent_groq.py" in text
    assert "--model openai/gpt-oss-120b" in text
    assert "GROQ_API_KEY" in text
    assert "Gemini emergency fallback" in text
    assert "gemini_model: gemini-3.6-flash" in text
    assert "gemini_model: gemini-3.5-flash-lite" not in text
    assert "gemini_model: gemini-3.1-flash-lite" not in text
    assert "gemini_model: gemini-2.5-flash-lite" not in text
    assert '"maxSessionTurns": 8' in text


def test_v4_captures_provider_errors_for_transient_classification():
    text = _v4()
    assert "/tmp/groq-primary.err" in text
    assert "gemini-artifacts/stderr.log /tmp/gemini-fallback.err" in text
    assert "--file /tmp/groq-primary.err" in text
    assert "--file /tmp/gemini-fallback.err" in text


def test_v4_persists_per_issue_usage_without_spending_iteration_budget():
    text = _v4()
    assert "usage-update" in text
    assert "USAGE.json" in text
    assert "Research V4 usage #" in text
    assert "grep -c \"^Research V4 issue #" in text
    assert "research_iterations_committed" in text
    assert "model_passes_attempted" in text
    assert "short_retries_scheduled" in text


def test_v4_persists_issue_branch_and_machine_state():
    text = _v4()
    assert "research_orchestrator_v4.py branch-name" in text
    assert "research_orchestrator_v4.py validate-state" in text
    assert "STATE.json" in text
    assert "FINAL_REPORT.md" in text


def test_v4_continues_without_user_and_retries_waiting_work():
    text = _v4()
    assert "source=continuation" in text
    assert "source=quick-retry" in text
    assert "quick_retry_attempt" in text
    assert "retry-delay" in text
    assert 'sleep "$DELAY_SECONDS"' in text
    assert "NEXT_ATTEMPT" in text
    assert "[ \"$ATTEMPT\" -lt 3 ]" in text
    assert "research-v4-running" in text
    assert "research-v4-waiting" in text
    assert "source=schedule" in text


def test_v4_heartbeat_wakes_waiting_issues_from_independent_live_workflows():
    text = _heartbeat()
    on_block = text.split("permissions:", 1)[0]
    assert "workflow_dispatch:" in on_block
    assert "schedule:" in on_block
    assert "workflow_run:" in on_block
    assert "Prospective Market Path Settlement Lag" in on_block
    assert "Product Operational Automation" in on_block
    assert "All Leagues V1.1 Sample Health" in on_block
    assert "Multi-Market Probe Rollover Status" in on_block
    assert "Multi-Market V2 Readiness Status" in on_block
    assert "types: [completed]" in on_block


def test_v4_heartbeat_claims_waiting_issue_before_dispatch_and_restores_on_failure():
    text = _heartbeat()
    assert "--label research-v4-waiting" in text
    claim = '--add-label research-v4-queued \\\n              --remove-label research-v4-waiting'
    assert claim in text
    assert "gh workflow run research-orchestrator-v4.yml" in text
    assert "-f source=schedule" in text
    assert "--add-label research-v4-waiting" in text
    assert "--remove-label research-v4-queued" in text


def test_v4_contract_tracks_heartbeat_workflow_changes():
    text = _v4()
    assert "'.github/workflows/research-v4-heartbeat.yml'" in text


def test_v4_prompt_forbids_unavailable_tools():
    text = _v4()
    prompt = text.split("AGENT_PROMPT: |-", 1)[1].split("    steps:", 1)[0]
    assert "Never call update_topic" in prompt


def test_v4_keeps_model_tools_file_only():
    text = _v4()
    settings = text.split("GEMINI_SETTINGS: |-", 1)[1].split("AGENT_PROMPT: |-", 1)[0]
    assert "run_shell_command" not in settings
    assert '"read_file"' in settings
    assert '"write_file"' in settings
    assert '"replace"' in settings


def test_v4_has_deterministic_safety_gates():
    text = _v4()
    required = [
        "research_agent_gemini.py validate-status",
        "research_agent_gemini.py stage-status",
        "git diff --check",
        "sha256sum *.pkl",
        "pytest -q -p no:cacheprovider",
    ]
    for marker in required:
        assert marker in text


def test_v4_never_auto_merges_or_promotes():
    text = _v4()
    assert "gh pr merge" not in text
    assert "artifact_lifecycle.py promote" not in text


def test_legacy_v2_no_longer_runs_on_issue_events():
    text = _v2()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" not in on_block
    assert "pull_request:" in on_block


def test_v3_no_longer_runs_on_issue_events():
    text = _v3()
    on_block = text.split("permissions:", 1)[0]
    assert "issues:" not in on_block
    assert "pull_request:" in on_block
