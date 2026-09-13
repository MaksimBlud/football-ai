from pathlib import Path

from deployment_identity import deployment_git_sha


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/exact-main-vercel-deploy.yml"


def test_deployment_identity_prefers_explicit_exact_sha(monkeypatch):
    monkeypatch.setenv("DEPLOYMENT_GIT_SHA", "a" * 40)
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "b" * 40)

    assert deployment_git_sha() == "a" * 40


def test_deployment_identity_falls_back_to_vercel_git_sha(monkeypatch):
    monkeypatch.delenv("DEPLOYMENT_GIT_SHA", raising=False)
    monkeypatch.setenv("VERCEL_GIT_COMMIT_SHA", "c" * 40)

    assert deployment_git_sha() == "c" * 40


def test_deployment_identity_is_explicit_when_source_is_missing(monkeypatch):
    monkeypatch.delenv("DEPLOYMENT_GIT_SHA", raising=False)
    monkeypatch.delenv("VERCEL_GIT_COMMIT_SHA", raising=False)

    assert deployment_git_sha() == "unknown"


def test_web_health_wires_deployment_identity_without_changing_routes():
    source = (ROOT / "web_app.py").read_text(encoding="utf-8")

    assert "from deployment_identity import deployment_git_sha" in source
    assert '@app.get("/health")' in source
    assert '"deployment_git_sha": deployment_git_sha()' in source


def test_exact_main_workflow_is_manual_and_fail_closed():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "workflow_dispatch:" in source
    assert "schedule:" not in source
    assert "push:" not in source
    assert "VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}" in source
    assert 'if [ -z "${VERCEL_TOKEN:-}" ]' in source
    assert "VERCEL_TOKEN is not configured" in source
    assert "SUPABASE_KEY" not in source
    assert "ODDS_API" not in source


def test_exact_main_workflow_stages_verifies_then_promotes():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "ref: main" in source
    assert "git rev-parse HEAD" in source
    assert "git fetch origin main --depth=1" in source
    assert "git rev-parse origin/main" in source
    assert "--prod --skip-domain" in source
    assert '--env "DEPLOYMENT_GIT_SHA=$SOURCE_SHA"' in source
    assert "vercel promote" in source
    assert "/health" in source
    assert "/product-market-view" in source
    assert "/portfolio-risk-view" in source
    assert "/production-readiness-view" in source
    assert "football-ai-real-epl-snapshot.vercel.app" in source


def test_exact_main_workflow_targets_only_the_known_vercel_project():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "team_EDncljUUtFDTumz5hYleW8R3" in source
    assert "prj_lXttnTmlPncJPn2nKGSlid2vaxvg" in source
