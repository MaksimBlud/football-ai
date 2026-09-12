-- Least-privilege public read path for the Football AI product website.
--
-- The publishable Supabase key maps unauthenticated requests to the `anon` role.
-- Only upcoming product fields needed by the web contract are exposed. Internal
-- model provenance, historical rows and write privileges remain server-only.

revoke all privileges
    on table public.product_prediction_snapshots
    from anon;

grant select (
    snapshot_schema_version,
    generated_at_utc,
    league,
    event_id,
    commence_time_utc,
    match_date,
    match_time,
    home_team,
    away_team,
    home_team_model,
    away_team_model,
    prediction,
    prediction_strength,
    model_agreement,
    home_probability,
    draw_probability,
    away_probability,
    expected_home_goals,
    expected_away_goals,
    expected_total_goals,
    over_2_5_probability,
    under_2_5_probability,
    btts_yes_probability,
    btts_no_probability,
    top_score,
    top_score_probability
)
    on table public.product_prediction_snapshots
    to anon;

drop policy if exists "anon reads upcoming product prediction snapshots"
    on public.product_prediction_snapshots;

create policy "anon reads upcoming product prediction snapshots"
    on public.product_prediction_snapshots
    for select
    to anon
    using (
        snapshot_schema_version = 'product-prediction.v1'
        and commence_time_utc >= now() - interval '2 hours'
        and commence_time_utc < now() + interval '15 days'
    );

-- odds_snapshots predates the new explicit-grants default and historically has
-- broad role grants. Reduce only the anon role; service/research access is kept.
revoke all privileges
    on table public.odds_snapshots
    from anon;

grant select (
    event_id,
    snapshot_time_utc,
    commence_time_utc,
    home_team,
    away_team,
    home_odds,
    draw_odds,
    away_odds
)
    on table public.odds_snapshots
    to anon;

drop policy if exists "anon reads upcoming product odds"
    on public.odds_snapshots;

create policy "anon reads upcoming product odds"
    on public.odds_snapshots
    for select
    to anon
    using (
        commence_time_utc >= now() - interval '2 hours'
        and commence_time_utc < now() + interval '15 days'
        and snapshot_time_utc >= now() - interval '14 days'
    );
