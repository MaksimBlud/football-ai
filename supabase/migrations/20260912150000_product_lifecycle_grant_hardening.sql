-- Harden the lifecycle table to the exact append-only service-role contract.
-- New Supabase tables can inherit broader service_role table privileges than
-- SELECT/INSERT; revoke all table privileges first, then grant only what the
-- lifecycle writer/reader requires.

revoke all privileges
    on table public.product_prediction_lifecycle_events
    from anon, authenticated, service_role;

grant select, insert
    on table public.product_prediction_lifecycle_events
    to service_role;

revoke all privileges
    on sequence public.product_prediction_lifecycle_events_id_seq
    from anon, authenticated, service_role;

grant usage, select
    on sequence public.product_prediction_lifecycle_events_id_seq
    to service_role;
