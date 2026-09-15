-- Harden H2H bookmaker research storage to the exact append-only contract.
-- New Supabase tables can inherit broad service_role privileges from default
-- privileges; revoke them explicitly, then grant only the required operations.

revoke all privileges
    on table public.league_h2h_bookmaker_snapshots
    from anon, authenticated, service_role;

grant select, insert
    on table public.league_h2h_bookmaker_snapshots
    to service_role;
