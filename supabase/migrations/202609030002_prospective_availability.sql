-- Prospective player-availability research state. Additive and insert-only by policy.

create table if not exists public.prospective_availability_polls (
    poll_key text primary key,
    provider text not null check (provider = 'API_FOOTBALL'),
    provider_fixture_id bigint not null,
    league text not null check (league in ('EPL', 'LA_LIGA', 'SERIE_A')),
    home_team text not null,
    away_team text not null,
    commence_time_utc timestamptz not null,
    observed_at_utc timestamptz not null,
    raw_payload_sha256 text not null check (length(raw_payload_sha256) = 64),
    item_count integer not null check (item_count >= 0),
    payload jsonb not null,
    persisted_at_utc timestamptz not null default timezone('utc', now()),
    constraint prospective_availability_poll_pre_kickoff check (observed_at_utc < commence_time_utc)
);

create index if not exists prospective_availability_polls_fixture_time_idx
on public.prospective_availability_polls
(league, home_team, away_team, commence_time_utc, observed_at_utc desc);

create table if not exists public.prospective_availability_observations (
    observation_key text primary key,
    state_key text not null,
    poll_key text not null references public.prospective_availability_polls(poll_key),
    provider text not null check (provider = 'API_FOOTBALL'),
    provider_fixture_id bigint not null,
    provider_team_id bigint not null,
    provider_player_id bigint not null,
    league text not null check (league in ('EPL', 'LA_LIGA', 'SERIE_A')),
    home_team text not null,
    away_team text not null,
    commence_time_utc timestamptz not null,
    team_name text not null,
    player_name text not null,
    availability_type text not null check (availability_type in ('Injury', 'Suspension')),
    reason text not null,
    source_timestamp_utc timestamptz not null,
    source_timestamp_kind text not null check (source_timestamp_kind in ('provider_published', 'collector_observed')),
    observed_at_utc timestamptz not null,
    first_seen_timestamp_utc timestamptz not null,
    raw_payload_sha256 text not null check (length(raw_payload_sha256) = 64),
    persisted_at_utc timestamptz not null default timezone('utc', now()),
    constraint prospective_availability_first_seen_order check (first_seen_timestamp_utc <= observed_at_utc),
    constraint prospective_availability_observation_pre_kickoff check (observed_at_utc < commence_time_utc)
);

create index if not exists prospective_availability_observations_state_idx
on public.prospective_availability_observations(state_key, first_seen_timestamp_utc);

create index if not exists prospective_availability_observations_poll_idx
on public.prospective_availability_observations(poll_key);

alter table public.prospective_availability_polls enable row level security;
alter table public.prospective_availability_observations enable row level security;

do $$
begin
    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='prospective_availability_polls'
          and policyname='service role reads prospective availability polls'
    ) then
        create policy "service role reads prospective availability polls"
        on public.prospective_availability_polls for select to service_role using (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='prospective_availability_polls'
          and policyname='service role inserts prospective availability polls'
    ) then
        create policy "service role inserts prospective availability polls"
        on public.prospective_availability_polls for insert to service_role with check (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='prospective_availability_observations'
          and policyname='service role reads prospective availability observations'
    ) then
        create policy "service role reads prospective availability observations"
        on public.prospective_availability_observations for select to service_role using (true);
    end if;
    if not exists (
        select 1 from pg_policies
        where schemaname='public' and tablename='prospective_availability_observations'
          and policyname='service role inserts prospective availability observations'
    ) then
        create policy "service role inserts prospective availability observations"
        on public.prospective_availability_observations for insert to service_role with check (true);
    end if;
end
$$;

comment on table public.prospective_availability_polls is
'Immutable full API-Football pre-kickoff availability polls for prospective research.';
comment on table public.prospective_availability_observations is
'Immutable poll membership rows with state-level first-seen information time.';
