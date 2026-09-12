-- Explicit Data API grants for the durable product snapshot table.
-- Supabase projects created after 2026-05-30 no longer auto-expose new
-- public tables, so grants must be part of the migration history.
--
-- The product web app and publisher are server-side only. Keep anon and
-- authenticated roles completely out, and keep service_role append-only.

revoke all privileges
    on table public.product_prediction_snapshots
    from anon, authenticated;

revoke update, delete
    on table public.product_prediction_snapshots
    from service_role;

grant select, insert
    on table public.product_prediction_snapshots
    to service_role;

revoke all privileges
    on sequence public.product_prediction_snapshots_id_seq
    from anon, authenticated;

grant usage, select
    on sequence public.product_prediction_snapshots_id_seq
    to service_role;
