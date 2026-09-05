-- Research-only multi-market bookmaker snapshots.
-- Additive only. Existing 1X2 odds_snapshots and prediction ledgers remain untouched.

create table if not exists public.league_multi_market_snapshots (
    snapshot_key text primary key,
    league text not null,
    event_id text not null,
    home_team text not null,
    away_team text not null,
    kickoff_utc timestamptz not null,
    snapshot_time_utc timestamptz not null,
    payload jsonb not null,
    provider text not null default 'THE_ODDS_API',
    persisted_at_utc timestamptz not null default timezone('utc', now()),

    constraint league_multi_market_pre_kickoff
        check (snapshot_time_utc < kickoff_utc),
    constraint league_multi_market_research_only
        check (coalesce((payload->>'research_only')::boolean, false)),
    constraint league_multi_market_schema_version
        check (payload->>'schema_version' = 'MULTI_MARKET_V1')
);

create index if not exists league_multi_market_event_snapshot_idx
on public.league_multi_market_snapshots (league, event_id, snapshot_time_utc desc);

create index if not exists league_multi_market_kickoff_idx
on public.league_multi_market_snapshots (kickoff_utc);

comment on table public.league_multi_market_snapshots is
'Immutable research-only pre-kickoff bookmaker snapshots for handicap, goal totals and corner markets.';

alter table public.league_multi_market_snapshots enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='league_multi_market_snapshots'
          and policyname='service role reads league multi market snapshots'
    ) then
        create policy "service role reads league multi market snapshots"
        on public.league_multi_market_snapshots for select to service_role using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='league_multi_market_snapshots'
          and policyname='service role inserts league multi market snapshots'
    ) then
        create policy "service role inserts league multi market snapshots"
        on public.league_multi_market_snapshots for insert to service_role with check (true);
    end if;
end
$$;
