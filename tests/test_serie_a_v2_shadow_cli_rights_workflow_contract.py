from pathlib import Path

WORKFLOW = Path(".github/workflows/serie-a-v2-shadow-cli-rights-validation.yml")


def test_shadow_cli_rights_validation_workflow_is_push_only_and_offline():
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "push:" in source
    assert branch_name() in source
    for forbidden in (
        "pull_request:",
        "schedule:",
        "workflow_dispatch:",
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "THE_ODDS_API_KEY",
        "api.the-odds-api.com",
        "football-data.co.uk",
        "database.supabase",
        "secrets.GITHUB_TOKEN",
    ):
        assert forbidden not in source
    assert "permissions:\n  contents: read" in source
    assert "serie_a_v2_frozen_shadow_preview.py" in source
    assert "market_anchor_v2_source_rights.py" in source
    assert "tests/test_serie_a_v2_frozen_shadow_preview.py" in source


def branch_name():
    return "research/v2-shadow-cli-rights-gate-20261105-run11"
