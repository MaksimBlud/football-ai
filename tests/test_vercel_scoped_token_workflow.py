from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/exact-main-vercel-deploy.yml"


def test_exact_main_workflow_supports_project_scoped_vercel_tokens():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "VERCEL_ORG_ID:" not in source
    assert "EXPECTED_VERCEL_TEAM_ID: team_EDncljUUtFDTumz5hYleW8R3" in source
    assert "VERCEL_PROJECT_ID: prj_lXttnTmlPncJPn2nKGSlid2vaxvg" in source
    assert 'https://api.vercel.com/v9/projects/$VERCEL_PROJECT_ID' in source
    assert 'Authorization: Bearer $VERCEL_TOKEN' in source
    assert 'payload.get("id") == os.environ["VERCEL_PROJECT_ID"]' in source
    assert 'payload.get("accountId") == os.environ["EXPECTED_VERCEL_TEAM_ID"]' in source
    assert source.count('--project="$VERCEL_PROJECT_ID"') >= 2


def test_scoped_token_preflight_happens_before_pull_and_deploy():
    source = WORKFLOW.read_text(encoding="utf-8")

    preflight = source.index("Verify scoped token can access exact project")
    pull = source.index("Pull production project settings")
    deploy = source.index("Create staged production deployment from exact main")

    assert preflight < pull < deploy
