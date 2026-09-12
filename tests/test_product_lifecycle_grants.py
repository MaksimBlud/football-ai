from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_lifecycle_grant_hardening_revokes_broad_service_role_privileges():
    sql = (
        ROOT
        / "supabase/migrations/20260912150000_product_lifecycle_grant_hardening.sql"
    ).read_text(encoding="utf-8").lower()

    assert "revoke all privileges" in sql
    assert "from anon, authenticated, service_role" in sql
    assert "grant select, insert" in sql
    assert "to service_role" in sql
    assert "grant update" not in sql
    assert "grant delete" not in sql
    assert "grant truncate" not in sql
    assert "grant trigger" not in sql
    assert "grant references" not in sql
