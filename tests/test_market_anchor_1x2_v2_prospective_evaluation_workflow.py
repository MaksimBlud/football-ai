from datetime import datetime
from pathlib import Path

import ast
from types import SimpleNamespace
from typing import Any

import pytest

from market_anchor_v2_source_rights import DEFAULT_RIGHTS_MANIFEST_PATH, require_personal_research_inference_scope

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "market-anchor-1x2-v2-prospective-evaluation.yml"

PROSPECTIVE_GITHUB_API = "https://api.github.com/repos/MaksimBlud/football-ai"


def _load_prospective_github_json():
    source_path = ROOT / "market_anchor_1x2_v2_prospective_evaluation.py"
    tree = ast.parse(source_path.read_text(encoding="utf-8"))
    function = next(
        node for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_github_json"
    )
    isolated = ast.Module(body=[function], type_ignores=[])
    namespace = {
        "GITHUB_API": PROSPECTIVE_GITHUB_API,
        "requests": SimpleNamespace(get=lambda *_args, **_kwargs: None),
        "Any": Any,
    }
    exec(compile(ast.fix_missing_locations(isolated), str(source_path), "exec"), namespace)
    return namespace["_github_json"]



def test_prospective_evaluation_workflow_is_main_only_and_has_no_schedule_or_paid_provider():
    text = WORKFLOW.read_text(encoding="utf-8")
    trigger = text.split("concurrency:", 1)[0]
    assert "workflow_dispatch:" in trigger
    assert "workflow_run:" in trigger
    assert "Serie A V2 Current-Form Forward-Only Preview" in trigger
    assert "schedule:" not in trigger
    assert "pull_request:" not in trigger
    assert "push:" not in trigger
    assert "The Odds API" not in text
    assert "odds-api" not in text.lower()
    assert "  actions: read" in text and "  contents: read" in text
    job = text.split("  evaluate-market-only:", 1)[1]
    guard = "if: " + "$" + "{{ github.ref == 'refs/heads/main' &&"
    assert guard in job and job.index(guard) < job.index("    env:")
    assert "github.event_name == 'workflow_dispatch'" in job
    assert "github.event_name == 'workflow_run'" in job
    assert "github.event.workflow_run.event == 'schedule'" in job
    assert "github.event.workflow_run.event == 'workflow_dispatch'" in job
    assert "github.event.workflow_run.event == 'workflow_run'" in job
    assert "github.event_name != 'workflow_run'" not in job
    assert "github.event.workflow_run.event != 'pull_request'" not in job
    assert "SUPABASE_KEY: " + "$" + "{{ secrets.SUPABASE_KEY }}" in job
    assert "GITHUB_TOKEN: " + "$" + "{{ github.token }}" in job
    assert "GITHUB_REPOSITORY: " + "$" + "{{ github.repository }}" in job
    assert "market_anchor_v2_artifact_privacy.py" in job
    assert "market_anchor_1x2_v2_prospective_evaluation.py" in job
    assert "actions/upload-artifact@v4" in job
    assert "retention-days: 90" in job



def test_live_runner_owns_source_sha_verification_before_outcome_evaluation():
    runner_source = (ROOT / "market_anchor_1x2_v2_prospective_runner.py").read_text(encoding="utf-8")
    bridge_source = (ROOT / "market_anchor_1x2_v2_prospective_evaluation.py").read_text(encoding="utf-8")
    assert "from market_anchor_1x2_v2_prospective_evaluation import verify_source_artifacts_for_candidates" in runner_source
    assert "preflight:" not in runner_source
    assert "preflight=verify_source_preflight" not in bridge_source
    assert "token=token" in bridge_source



def test_live_evaluation_checks_ai_usage_rights_before_external_reads():
    script = (ROOT / "market_anchor_1x2_v2_prospective_evaluation.py").read_text(encoding="utf-8")
    main = script[script.index("def main()"):]
    guard = main.find("require_personal_research_inference_scope()")
    assert guard >= 0
    for side_effect in ("from supabase import create_client", "run_live_evaluation("):
        position = main.find(side_effect)
        assert position >= 0
        assert guard < position


def test_current_policy_blocks_frozen_inference_until_provider_issued_scope_is_granted():
    with pytest.raises(PermissionError, match="frozen-inference scope remains unresolved"):
        require_personal_research_inference_scope(DEFAULT_RIGHTS_MANIFEST_PATH)


class _ProspectiveGithubJsonResponse:
    def __init__(self, url, status_code, payload=None):
        self.url = url
        self.status_code = status_code
        self.payload = payload
        self.json_called = False

    def json(self):
        self.json_called = True
        return self.payload


def test_push_triggered_forward_run_is_rejected_by_artifact_verifier():
    from market_anchor_1x2_v2_prospective_evaluation import verify_forward_run
    from market_anchor_1x2_v2_forward_artifact_adapter import FORWARD_WORKFLOW_NAME, FORWARD_WORKFLOW_PATH

    url = PROSPECTIVE_GITHUB_API + "/actions/runs/789"
    response = _ProspectiveGithubJsonResponse(url, 200, {
        "id": 789,
        "path": FORWARD_WORKFLOW_PATH + "@refs/heads/main",
        "name": FORWARD_WORKFLOW_NAME,
        "head_branch": "main",
        "head_sha": "c" * 40,
        "status": "completed",
        "conclusion": "success",
        "event": "push",
        "created_at": "2026-10-19T05:20:00Z",
        "updated_at": "2026-10-19T05:32:00Z",
    })
    artifact = {
        "run_id": 789,
        "head_sha": "c" * 40,
        "created_at": datetime.fromisoformat("2026-10-19T05:31:30+00:00"),
    }

    with pytest.raises(ValueError, match="exact successful main V2 forward workflow"):
        verify_forward_run(artifact, "read-only-test-token", get=lambda _url, **_kwargs: response)


def test_prospective_github_api_json_disables_redirects_and_rejects_302_before_body_read():
    github_json = _load_prospective_github_json()
    url = PROSPECTIVE_GITHUB_API + "/actions/artifacts?per_page=1"
    response = _ProspectiveGithubJsonResponse(url, 302, {"artifacts": []})
    request = {}

    def fake_get(request_url, **kwargs):
        request["url"] = request_url
        request.update(kwargs)
        return response

    with pytest.raises(RuntimeError, match="HTTP 302"):
        github_json(url, "read-only-test-token", get=fake_get)

    assert request["url"] == url
    assert request["allow_redirects"] is False
    assert response.json_called is False


def test_prospective_github_api_json_rejects_unexpected_response_url():
    github_json = _load_prospective_github_json()
    url = PROSPECTIVE_GITHUB_API + "/actions/runs/123"
    response = _ProspectiveGithubJsonResponse("https://attacker.example/forged", 200, {"id": 123})
    request = {}

    def fake_get(request_url, **kwargs):
        request["allow_redirects"] = kwargs.get("allow_redirects")
        return response

    with pytest.raises(ValueError, match="response URL mismatch"):
        github_json(url, "read-only-test-token", get=fake_get)

    assert request["allow_redirects"] is False
    assert response.json_called is False


def test_prospective_github_api_json_accepts_exact_http_200_without_redirects():
    github_json = _load_prospective_github_json()
    url = PROSPECTIVE_GITHUB_API + "/actions/artifacts?per_page=1"
    response = _ProspectiveGithubJsonResponse(url, 200, {"artifacts": []})
    request = {}

    def fake_get(request_url, **kwargs):
        request["allow_redirects"] = kwargs.get("allow_redirects")
        return response

    assert github_json(url, "read-only-test-token", get=fake_get) == {"artifacts": []}
    assert request["allow_redirects"] is False
    assert response.json_called is True


def test_live_market_only_bridge_delegates_to_gate_local_supabase_runner(monkeypatch):
    import hashlib

    import market_anchor_1x2_v2_prospective_evaluation as live
    import market_anchor_1x2_v2_prospective_runner as runner

    monkeypatch.setattr(
        live, "require_personal_research_inference_scope",
        lambda: {"scope_status": "TEST_ONLY_EXPLICITLY_AUTHORIZED"},
    )
    monkeypatch.setattr(
        runner, "require_personal_research_inference_scope",
        lambda: {"scope_status": "TEST_ONLY_EXPLICITLY_AUTHORIZED"},
    )

    monkeypatch.setattr(
        live,
        "require_private_repository_for_source_artifacts",
        lambda repository, token, get: {
            "repository": repository,
            "private": True,
            "storage_policy": "PRIVATE_GITHUB_ACTIONS_ARTIFACTS",
        },
    )

    rows = []
    candidates = []
    for index in range(30):
        row = {
            "match_date": "2026-11-01",
            "home_team": f"Home {index:02d}",
            "away_team": f"Away {index:02d}",
            "kickoff_utc": f"2026-11-01T{index % 24:02d}:00:00Z",
            "source_artifact_id": 999,
        }
        rows.append(row)
        candidates.append({
            "row": row,
            "provenance": {"source_artifact_id": 999},
        })

    raw_archive = b"synthetic-forward-artifact"
    artifact = {
        "artifact_id": 123,
        "sha256": hashlib.sha256(raw_archive).hexdigest(),
        "created_at_utc": "2026-11-01T12:00:00Z",
    }
    forward_run = {"run_id": 456, "head_sha": "a" * 40}
    embedded_source = {999: b"synthetic-source-archive"}
    verified_source_sha = "b" * 64
    captured = {}

    monkeypatch.setattr(live, "discover_forward_artifacts", lambda token, get: [artifact])
    monkeypatch.setattr(live, "verify_forward_run", lambda item, token, get: forward_run)
    monkeypatch.setattr(live, "get_archive", lambda artifact_id, token, get: raw_archive)
    monkeypatch.setattr(live, "extract_forward_artifact", lambda raw: ({}, embedded_source))
    monkeypatch.setattr(
        live, "normalize_forward_report",
        lambda report, forward_artifact_id, forward_run: candidates,
    )
    monkeypatch.setattr(
        live, "select_first_eligible_forecasts",
        lambda items: (items, {"selected": len(items)}),
    )
    monkeypatch.setattr(
        live, "verify_source_artifacts_for_candidates",
        lambda items, token, current_gate_identities, get: {999: verified_source_sha},
    )

    def evaluate_from_supabase(
        client,
        source_candidates,
        *,
        token,
        observed_at_utc,
        outcome_read_state,
    ):
        selected_rows = [candidate["row"] for candidate in source_candidates]
        identities = {
            (row["match_date"], row["home_team"], row["away_team"])
            for row in selected_rows
        }
        captured["client"] = client
        captured["source_candidates"] = list(source_candidates)
        captured["selected_rows"] = selected_rows
        captured["token"] = token
        captured["observed_at_utc"] = observed_at_utc
        outcome_read_state["called"] = True
        return {
            "status": "EVALUATED_MARKET_ONLY_DIAGNOSTIC",
            "target_outcomes_read": True,
            "target_outcomes_scored": True,
            "scored_forecasts": len(identities),
            "source_archives_reverified": 1,
            "source_archive_sha256": {"999": verified_source_sha},
        }

    monkeypatch.setattr(live, "evaluate_live_market_only_from_supabase", evaluate_from_supabase)

    client = object()
    report = live.run_live_evaluation(
        client,
        "read-only-test-token",
        now=datetime.fromisoformat("2026-11-05T12:00:00+00:00"),
        get=lambda *_args, **_kwargs: None,
    )

    assert report["status"] == "EVALUATED_MARKET_ONLY_DIAGNOSTIC"
    assert report["target_outcomes_read"] is True
    assert captured["client"] is client
    assert captured["selected_rows"] == rows
    assert len(captured["source_candidates"]) == 30
    assert captured["token"] == "read-only-test-token"
    assert captured["observed_at_utc"] == "2026-11-05T12:00:00Z"
    assert report["source_archives_reverified"] == 1
    assert report["source_archive_sha256"] == {"999": verified_source_sha}



def test_prospective_evaluator_pr_validation_is_offline_and_secret_free():
    validation = ROOT / ".github" / "workflows" / "market-anchor-1x2-v2-prospective-evaluation-validation.yml"
    text = validation.read_text(encoding="utf-8")
    assert "pull_request:" in text
    assert "workflow_dispatch:" not in text
    assert "SUPABASE_KEY" not in text
    assert "SUPABASE_URL" not in text
    assert "GITHUB_TOKEN" not in text
    assert "market_anchor_1x2_v2_prospective_evaluation.py" in text
    assert "tests/test_market_anchor_1x2_v2_prospective_runner.py" in text


def test_run_live_evaluation_blocks_unlicensed_inference_before_privacy_or_artifact_reads(monkeypatch):
    import market_anchor_1x2_v2_prospective_evaluation as live

    calls = []

    def forbidden(*_args, **_kwargs):
        calls.append("unexpected_external_access")
        pytest.fail("unlicensed inference must stop before privacy/artifact/Supabase access")

    monkeypatch.setattr(live, "require_private_repository_for_source_artifacts", forbidden)
    monkeypatch.setattr(live, "discover_forward_artifacts", forbidden)

    class Client:
        def table(self, _name):
            pytest.fail("unlicensed inference must stop before Supabase reads")

    with pytest.raises(PermissionError, match="frozen-inference scope remains unresolved"):
        live.run_live_evaluation(
            Client(),
            "synthetic-read-only-token",
            now=datetime.fromisoformat("2026-11-08T06:00:00+00:00"),
            get=forbidden,
        )
    assert calls == []


class _PrivateRepositoryResponse:
    def __init__(self, private):
        self.status_code = 200
        self.url = PROSPECTIVE_GITHUB_API
        self.private = private

    def json(self):
        return {"full_name": "MaksimBlud/football-ai", "private": self.private}


def test_public_repository_blocks_before_forward_artifact_listing_or_supabase_reads(monkeypatch):
    import market_anchor_1x2_v2_prospective_evaluation as live

    monkeypatch.setattr(
        live, "require_personal_research_inference_scope",
        lambda: {"scope_status": "TEST_ONLY_EXPLICITLY_AUTHORIZED"},
    )

    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    calls = []

    def fake_get(url, **kwargs):
        calls.append((url, kwargs))
        return _PrivateRepositoryResponse(False)

    def forbidden_artifact_listing(*_args, **_kwargs):
        pytest.fail("public repository must be rejected before artifact listing")

    class Client:
        def table(self, _name):
            pytest.fail("public repository must be rejected before any Supabase read")

    monkeypatch.setattr(live, "discover_forward_artifacts", forbidden_artifact_listing)

    with pytest.raises(PermissionError, match="require a private GitHub repository"):
        live.run_live_evaluation(
            Client(),
            "synthetic-read-only-token",
            now=datetime.fromisoformat("2026-11-08T03:00:00+00:00"),
            get=fake_get,
        )

    assert len(calls) == 1
    assert calls[0][0] == PROSPECTIVE_GITHUB_API
    assert calls[0][1]["allow_redirects"] is False


def test_private_repository_gate_precedes_forward_artifact_listing(monkeypatch):
    import market_anchor_1x2_v2_prospective_evaluation as live

    monkeypatch.setattr(
        live, "require_personal_research_inference_scope",
        lambda: {"scope_status": "TEST_ONLY_EXPLICITLY_AUTHORIZED"},
    )

    monkeypatch.setenv("GITHUB_REPOSITORY", "MaksimBlud/football-ai")
    calls = []

    def fake_get(url, **kwargs):
        calls.append("privacy")
        return _PrivateRepositoryResponse(True)

    def empty_artifact_listing(token, get):
        calls.append("artifact_listing")
        return []

    monkeypatch.setattr(live, "discover_forward_artifacts", empty_artifact_listing)

    report = live.run_live_evaluation(
        object(),
        "synthetic-read-only-token",
        now=datetime.fromisoformat("2026-11-08T03:00:00+00:00"),
        get=fake_get,
    )

    assert calls == ["privacy", "artifact_listing"]
    assert report["status"] == "NO_FORWARD_ARTIFACTS"
    assert report["private_storage_verified"] is True
    assert report["target_outcomes_read"] is False
    assert report["target_outcomes_scored"] is False


def test_private_storage_gate_is_before_artifact_listing_in_live_evaluator_source():
    source = (ROOT / "market_anchor_1x2_v2_prospective_evaluation.py").read_text(encoding="utf-8")
    live = source[source.index("def run_live_evaluation"):source.index("def main()")]
    privacy = live.find("require_private_repository_for_source_artifacts(")
    artifact_listing = live.find("discover_forward_artifacts(")
    assert privacy >= 0
    assert artifact_listing >= 0
    assert privacy < artifact_listing



def test_direct_source_verifier_requires_inference_rights_before_any_archive_access(monkeypatch):
    import market_anchor_1x2_v2_prospective_evaluation as live

    calls = []

    def deny_inference_rights():
        calls.append("rights")
        raise PermissionError("frozen-inference scope remains unresolved")

    monkeypatch.setattr(live, "require_personal_research_inference_scope", deny_inference_rights)
    monkeypatch.setattr(
        live, "require_private_repository_for_source_artifacts",
        lambda *args, **kwargs: calls.append("privacy"),
    )
    monkeypatch.setattr(
        live, "discover_archives",
        lambda **kwargs: calls.append("archive-listing") or [],
    )

    candidate = {"row": {"source_artifact_id": 123}, "provenance": {}}
    with pytest.raises(PermissionError, match="frozen-inference scope remains unresolved"):
        live.verify_source_artifacts_for_candidates(
            [candidate], token="synthetic-token", current_gate_identities=set()
        )

    assert calls == ["rights"]


def test_direct_source_verifier_requires_private_storage_before_archive_listing(monkeypatch):
    import market_anchor_1x2_v2_prospective_evaluation as live

    calls = []

    monkeypatch.setattr(
        live, "require_personal_research_inference_scope",
        lambda: calls.append("rights") or {"scope_status": "SYNTHETIC_TEST_ONLY"},
    )

    def deny_private_storage(repository, token, *, get=None):
        calls.append(("privacy", repository, token))
        raise PermissionError("source archives require a private GitHub repository")

    monkeypatch.setattr(live, "require_private_repository_for_source_artifacts", deny_private_storage)
    monkeypatch.setattr(
        live, "discover_archives",
        lambda **kwargs: calls.append("archive-listing") or [],
    )

    candidate = {"row": {"source_artifact_id": 123}, "provenance": {}}
    with pytest.raises(PermissionError, match="require a private GitHub repository"):
        live.verify_source_artifacts_for_candidates(
            [candidate], token="synthetic-token", current_gate_identities=set()
        )

    assert calls == [
        "rights",
        ("privacy", "MaksimBlud/football-ai", "synthetic-token"),
    ]
