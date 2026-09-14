-- Tighten the private artifact registry to the minimum server-side privileges.
--
-- The initial registry migration revoked UPDATE/DELETE but PostgreSQL table
-- defaults still exposed TRUNCATE/REFERENCES/TRIGGER to service_role.  TRUNCATE
-- would bypass the row-level UPDATE/DELETE trigger and violate append-only
-- semantics, so remove every table privilege and add back only SELECT/INSERT.

revoke all privileges
    on table public.model_artifact_bundles
    from anon, authenticated, service_role;

grant select, insert
    on table public.model_artifact_bundles
    to service_role;
