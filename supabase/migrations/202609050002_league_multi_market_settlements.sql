-- Research-only append-only Multi-Market V2 settlement revisions.
-- Additive only. No existing table or policy is modified.

create table if not exists public.league_multi_market_settlements (
    settlement_key text primary key,
    snapshot_key text not null references public.league_multi_market_snapshots(snapshot_key),
    league text not null,
    event_id text not null,
    home_team text not null,
    away_team text not null,
    kickoff_utc timestamptz not null,
    snapshot_time_utc timestamptz not null,
    result_season text not null,
    result_match_date date not null,
    outcome_fingerprint text not null,
    outcome_completeness text not null,
    payload jsonb not null,
    persisted_at_utc timestamptz not null default timezone('utc', now()),

    constraint league_multi_market_settlement_pre_kickoff
        check (snapshot_time_utc < kickoff_utc),
    constraint league_multi_market_settlement_research_only
        check (coalesce((payload->>'research_only')::boolean, false)),
    constraint league_multi_market_settlement_schema_version
        check (payload->>'schema_version' = 'MULTI_MARKET_SETTLEMENT_V2'),
    constraint league_multi_market_settlement_identity_version
        check (payload->>'identity_version' = 'LEAGUE_LOCAL_DATE_EXACT_TEAMS_V1'),
    constraint league_multi_market_settlement_completeness
        check (outcome_completeness in ('GOALS_ONLY', 'GOALS_AND_CORNERS')),
    constraint league_multi_market_settlement_payload_completeness
        check (payload->>'outcome_completeness' = outcome_completeness),
    unique (snapshot_key, outcome_fingerprint)
);

create index if not exists league_multi_market_settlement_snapshot_idx
on public.league_multi_market_settlements (snapshot_key, persisted_at_utc desc);

create index if not exists league_multi_market_settlement_event_idx
on public.league_multi_market_settlements (league, event_id, persisted_at_utc desc);

create index if not exists league_multi_market_settlement_result_idx
on public.league_multi_market_settlements
(league, result_match_date, home_team, away_team);

comment on table public.league_multi_market_settlements is
'Immutable research-only Multi-Market V2 settlement revisions. Later corner outcomes append a new revision; earlier goals-only revisions are not updated.';

alter table public.league_multi_market_settlements enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname='public'
          and tablename='league_multi_market_settlements'
          and policyname='service role reads league multi market settlements'
    ) then
        create policy "service role reads league multi market settlements"
        on public.league_multi_market_settlements
        for select to service_role using (true);
    end if;

    if not exists (
        select 1 from pg_policies
        where schemaname='public'
          and tablename='league_multi_market_settlements'
          and policyname='service role inserts league multi market settlements'
    ) then
        create policy "service role inserts league multi market settlements"
        on public.league_multi_market_settlements
        for insert to service_role with check (true);
    end if;
end
$$;
