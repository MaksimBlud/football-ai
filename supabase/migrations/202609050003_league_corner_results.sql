-- Research-only canonical corner outcomes for Multi-Market V2.
-- Additive only; does not alter existing result or snapshot tables.

create table if not exists public.league_corner_results (
    corner_result_key text primary key,
    league text not null,
    season text not null,
    match_date date not null,
    home_team text not null,
    away_team text not null,
    home_goals integer not null check (home_goals >= 0),
    away_goals integer not null check (away_goals >= 0),
    home_corners integer not null check (home_corners >= 0),
    away_corners integer not null check (away_corners >= 0),
    source text not null,
    source_fingerprint text not null,
    source_fetched_at_utc timestamptz not null,
    payload jsonb not null,
    persisted_at_utc timestamptz not null default timezone('utc', now()),

    constraint league_corner_result_research_only
        check (coalesce((payload->>'research_only')::boolean, false)),
    constraint league_corner_result_schema_version
        check (payload->>'schema_version' = 'LEAGUE_CORNER_RESULT_V1'),
    constraint league_corner_result_identity_reconciled
        check (coalesce((payload->>'identity_reconciled')::boolean, false)),
    constraint league_corner_result_goals_reconciled
        check (coalesce((payload->>'goals_reconciled')::boolean, false)),
    unique (
        league,
        season,
        match_date,
        home_team,
        away_team,
        source_fingerprint
    )
);

create index if not exists league_corner_results_fixture_idx
on public.league_corner_results
(league, season, match_date, home_team, away_team, persisted_at_utc desc);

comment on table public.league_corner_results is
'Append-only research-only corner outcomes reconciled exactly against canonical league_finished_results before persistence.';

alter table public.league_corner_results enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname='public'
          and tablename='league_corner_results'
          and policyname='service role reads league corner results'
    ) then
        create policy "service role reads league corner results"
        on public.league_corner_results
        for select to service_role using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname='public'
          and tablename='league_corner_results'
          and policyname='service role inserts league corner results'
    ) then
        create policy "service role inserts league corner results"
        on public.league_corner_results
        for insert to service_role with check (true);
    end if;
end
$$;
