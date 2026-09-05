from pathlib import Path


ROOT = (
    Path(__file__)
    .resolve()
    .parents[1]
)

WORKFLOW = (
    ROOT
    / ".github"
    / "workflows"
    / "la-liga-live-cycle.yml"
)

MIGRATION = (
    ROOT
    / "supabase"
    / "migrations"
    / "202608240001_la_liga_live_state.sql"
)


def test_workflow_contract():
    text = (
        WORKFLOW
        .read_text(
            encoding="utf-8"
        )
    )

    # This entrypoint performs a real h2h provider collection, so quota safety
    # requires explicit manual dispatch plus a zero-cost hard-reserve preflight.
    assert "workflow_dispatch:" in text
    assert "cron:" not in text
    assert "push:" not in text
    assert "python odds_api_budget_guard.py --max-cost 1" in text

    assert (
        "concurrency:"
        in text
    )

    assert (
        "contents: read"
        in text
    )

    assert (
        'python-version: "3.12"'
        in text
    )

    for secret in (
        "THE_ODDS_API_KEY",
        "SUPABASE_URL",
        "SUPABASE_KEY",
    ):
        assert secret in text

    assert (
        "python3 scheduled_la_liga_live_cycle.py"
        in text
    )

    assert (
        "python3 la_liga_live_cycle.py"
        not in text
    )

    lowered = text.lower()

    for forbidden in (
        "git add",
        "git commit",
        "git push",
        "git reset",
        "git clean",
    ):
        assert (
            forbidden
            not in lowered
        )


def test_migration_is_additive():
    sql = (
        MIGRATION
        .read_text(
            encoding="utf-8"
        )
        .lower()
    )

    forbidden = (
        "drop table",
        "drop column",
        "truncate ",
        "delete from",
        "update ",
        "rename column",
        "alter column",
    )

    for token in forbidden:
        assert token not in sql

    assert (
        "odds_snapshots"
        not in sql
    )

    assert (
        "la_liga_structural_v2_observations"
        in sql
    )

    assert (
        "la_liga_finished_results"
        in sql
    )

    assert (
        "market_argmax"
        in sql
    )

    assert (
        "shadow_argmax"
        in sql
    )
