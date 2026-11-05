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
    assert "market_anchor_1x2_v2_prospective_evaluation.py" in job
    assert "actions/upload-artifact@v4" in job
    assert "retention-days: 90" in job



def test_source_preflight_and_outcome_evaluator_share_one_gate_snapshot():
    script = (ROOT / "market_anchor_1x2_v2_prospective_evaluation.py").read_text(encoding="utf-8")
    assert "read_completed_primary_event_identities" not in script
    assert "current_gate = " not in script
    assert "def verify_source_preflight(completed_identities, _gate_attestation):" in script
    assert "preflight=verify_source_preflight" in script
    assert "current_gate_identities=set(completed_identities)" in script



def test_live_evaluation_checks_ai_usage_rights_before_external_reads():
    script = (ROOT / "market_anchor_1x2_v2_prospective_evaluation.py").read_text(encoding="utf-8")
    main = script[script.index("def main()"):]
    guard = main.find("require_personal_research_inference_scope()")
    assert guard >= 0
    for side_effect in ("from supabase import create_client", "run_live_evaluation("):
        position = main.find(side_effect)
        assert position >= 0
        assert guard < position


def test_current_policy_limits_live_v2_evaluation_to_noncommercial_research_scope():
    scope = require_personal_research_inference_scope(DEFAULT_RIGHTS_MANIFEST_PATH)
    assert scope["scope_status"] == "CONDITIONAL_RESEARCH_ONLY"
    assert scope["research_inference_scope"] == "PERSONAL_BETTING_OR_ACADEMIC_RESEARCH_ONLY"
    assert scope["provider_issued_ai_inference_license"] is False
    assert scope["commercial_use_permitted"] is False
    assert scope["public_product_use_permitted"] is False


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
