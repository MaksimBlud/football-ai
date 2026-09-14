-- Private immutable model-artifact registry for controlled Total Goals inference.
--
-- Binary model artifacts remain outside Git.  This migration creates a private
-- Supabase Storage bucket plus a server-side-only metadata ledger.  It does not
-- upload, train, promote, load, or execute any model artifact.

insert into storage.buckets (id, name, public)
values ('model-artifacts', 'model-artifacts', false)
on conflict (id) do update
set public = false
where storage.buckets.public is distinct from false;

create table if not exists public.model_artifact_bundles (
    bundle_sha256 text primary key,
    bundle_version text not null,
    artifact_family text not null,
    storage_bucket text not null,
    storage_prefix text not null unique,
    component_hashes jsonb not null,
    manifest jsonb not null,
    source_note text,
    registered_at_utc timestamptz not null default now(),
    registered_by text not null default 'manual-controlled-registry',
    constraint model_artifact_bundle_sha256_format
        check (bundle_sha256 ~ '^[0-9a-f]{64}$'),
    constraint model_artifact_bundle_version_nonempty
        check (length(trim(bundle_version)) > 0),
    constraint model_artifact_family_nonempty
        check (length(trim(artifact_family)) > 0),
    constraint model_artifact_storage_bucket_nonempty
        check (length(trim(storage_bucket)) > 0),
    constraint model_artifact_storage_prefix_nonempty
        check (length(trim(storage_prefix)) > 0),
    constraint model_artifact_component_hashes_object
        check (jsonb_typeof(component_hashes) = 'object'),
    constraint model_artifact_manifest_object
        check (jsonb_typeof(manifest) = 'object')
);

alter table public.model_artifact_bundles enable row level security;

create policy "service role inserts model artifact bundles"
    on public.model_artifact_bundles
    for insert
    to service_role
    with check (true);

create policy "service role reads model artifact bundles"
    on public.model_artifact_bundles
    for select
    to service_role
    using (true);

revoke all privileges
    on table public.model_artifact_bundles
    from anon, authenticated;

revoke update, delete
    on table public.model_artifact_bundles
    from service_role;

grant select, insert
    on table public.model_artifact_bundles
    to service_role;

-- Defense in depth: even a database role with UPDATE/DELETE table privileges
-- cannot mutate registered bundle identities through ordinary DML.
create or replace function public.reject_model_artifact_bundle_mutation()
returns trigger
language plpgsql
set search_path = ''
as $$
begin
    raise exception 'model_artifact_bundles is append-only';
end;
$$;

revoke all on function public.reject_model_artifact_bundle_mutation() from public;

drop trigger if exists reject_model_artifact_bundle_update_delete
    on public.model_artifact_bundles;

create trigger reject_model_artifact_bundle_update_delete
before update or delete on public.model_artifact_bundles
for each row
execute function public.reject_model_artifact_bundle_mutation();
