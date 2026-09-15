from pathlib import Path


HARDENING_MIGRATION = Path(
    "supabase/migrations/20260915142500_h2h_bookmaker_grant_hardening.sql"
)


def _sql() -> str:
    return " ".join(HARDENING_MIGRATION.read_text(encoding="utf-8").lower().split())


def test_h2h_bookmaker_grants_are_explicitly_hardened():
    sql = _sql()

    revoke = (
        "revoke all privileges on table public.league_h2h_bookmaker_snapshots "
        "from anon, authenticated, service_role;"
    )
    grant = (
        "grant select, insert on table public.league_h2h_bookmaker_snapshots "
        "to service_role;"
    )

    assert revoke in sql
    assert grant in sql
    assert sql.index(revoke) < sql.index(grant)

    for forbidden in ("grant update", "grant delete", "grant truncate"):
        assert forbidden not in sql
