from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/exact-main-vercel-deploy.yml"


def test_exact_main_workflow_supports_project_scoped_vercel_tokens_without_cli_project_env_override():
    source = WORKFLOW.read_text(encoding="utf-8")

    assert "VERCEL_ORG_ID:" not in source
    assert "EXPECTED_VERCEL_TEAM_ID: team_EDncljUUtFDTumz5hYleW8R3" in source
    assert "EXPECTED_VERCEL_PROJECT_ID: prj_lXttnTmlPncJPn2nKGSlid2vaxvg" in source
    assert "\n  VERCEL_PROJECT_ID:" not in source
    assert 'os.environ["VERCEL_PROJECT_ID"]' not in source
    assert 'https://api.vercel.com/v9/projects/$EXPECTED_VERCEL_PROJECT_ID' in source
    assert 'Authorization: Bearer $VERCEL_TOKEN' in source
    assert 'payload.get("id") == os.environ["EXPECTED_VERCEL_PROJECT_ID"]' in source
    assert 'payload.get("accountId") == os.environ["EXPECTED_VERCEL_TEAM_ID"]' in source
    assert "vercel link --yes" not in source
    assert "Materialize exact Vercel project link" in source
    assert '"orgId": os.environ["EXPECTED_VERCEL_TEAM_ID"]' in source
    assert '"projectId": os.environ["EXPECTED_VERCEL_PROJECT_ID"]' in source
    assert 'Path(".vercel/project.json")' in source


def test_scoped_token_preflight_and_materialized_link_happen_before_pull_and_deploy():
    source = WORKFLOW.read_text(encoding="utf-8")

    preflight = source.index("Verify scoped token can access exact project")
    link = source.index("Materialize exact Vercel project link")
    pull = source.index("Pull production project settings")
    deploy = source.index("Create staged production deployment from exact main")

    assert preflight < link < pull < deploy


def test_pull_and_deploy_use_only_the_verified_local_project_link():
    source = WORKFLOW.read_text(encoding="utf-8")

    pull_block = source[source.index("Pull production project settings") : source.index("Create staged production deployment from exact main")]
    deploy_block = source[source.index("Create staged production deployment from exact main") : source.index("Verify staged deployment SHA")]

    assert "VERCEL_PROJECT_ID" not in pull_block
    assert "VERCEL_ORG_ID" not in pull_block
    assert "VERCEL_PROJECT_ID" not in deploy_block
    assert "VERCEL_ORG_ID" not in deploy_block
    assert '--token="$VERCEL_TOKEN"' in pull_block
    assert '--token="$VERCEL_TOKEN"' in deploy_block
