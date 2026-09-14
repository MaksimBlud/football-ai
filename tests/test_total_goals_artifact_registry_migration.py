from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATION = ROOT / "supabase/migrations/20260914030000_total_goals_artifact_registry.sql"


def test_registry_bucket_is_private_and_metadata_is_server_side_only():
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "insert into storage.buckets" in sql
    assert "'model-artifacts', 'model-artifacts', false" in sql
    assert "create table if not exists public.model_artifact_bundles" in sql
    assert "enable row level security" in sql
    assert 'to service_role' in sql
    assert "from anon, authenticated" in sql
    assert "grant select, insert" in sql
    assert "revoke update, delete" in sql
    assert "grant update" not in sql
    assert "grant delete" not in sql


def test_registry_metadata_is_append_only_with_content_identity_constraints():
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "bundle_sha256 text primary key" in sql
    assert "storage_prefix text not null unique" in sql
    assert "component_hashes jsonb not null" in sql
    assert "manifest jsonb not null" in sql
    assert "^[0-9a-f]{64}$" in sql
    assert "reject_model_artifact_bundle_mutation" in sql
    assert "before update or delete" in sql
    assert "model_artifact_bundles is append-only" in sql


def test_migration_does_not_grant_public_storage_object_access():
    sql = MIGRATION.read_text(encoding="utf-8").lower()

    assert "create policy" in sql
    assert "on storage.objects" not in sql
    assert "to anon" not in sql
    assert "to authenticated" not in sql
