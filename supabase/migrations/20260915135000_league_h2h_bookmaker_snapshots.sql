create table public.league_h2h_bookmaker_snapshots (
    snapshot_key text primary key,
    created_at timestamptz not null default now(),
    league text not null,
    event_id text not null,
    home_team text not null,
    away_team text not null,
    kickoff_utc timestamptz not null,
    snapshot_time_utc timestamptz not null,
    provider text not null default 'THE_ODDS_API',
    raw_bookmakers_count integer not null,
    accepted_bookmakers_count integer not null,
    payload jsonb not null,
    payload_sha256 text not null,
    constraint league_h2h_bookmaker_pre_kickoff
        check (snapshot_time_utc < kickoff_utc),
    constraint league_h2h_bookmaker_research_only
        check (coalesce((payload ->> 'research_only')::boolean, false)),
    constraint league_h2h_bookmaker_schema_version
        check (payload ->> 'schema_version' = 'H2H_BOOKMAKER_V1'),
    constraint league_h2h_bookmaker_provider
        check (provider = 'THE_ODDS_API'),
    constraint league_h2h_bookmaker_counts
        check (
            raw_bookmakers_count >= 0
            and accepted_bookmakers_count >= 0
            and accepted_bookmakers_count <= raw_bookmakers_count
        ),
    constraint league_h2h_bookmaker_payload_hash
        check (length(payload_sha256) = 64)
);

create index league_h2h_bookmaker_event_snapshot_idx
    on public.league_h2h_bookmaker_snapshots
    (league, event_id, snapshot_time_utc desc);

create index league_h2h_bookmaker_kickoff_idx
    on public.league_h2h_bookmaker_snapshots
    (kickoff_utc);

alter table public.league_h2h_bookmaker_snapshots enable row level security;

revoke all on table public.league_h2h_bookmaker_snapshots from anon, authenticated;
grant select, insert on table public.league_h2h_bookmaker_snapshots to service_role;

create policy "service role reads h2h bookmaker snapshots"
    on public.league_h2h_bookmaker_snapshots
    for select
    to service_role
    using (true);

create policy "service role inserts h2h bookmaker snapshots"
    on public.league_h2h_bookmaker_snapshots
    for insert
    to service_role
    with check (true);
