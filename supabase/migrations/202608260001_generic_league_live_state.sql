-- Generic multi-league durable research state.
-- Additive only.
-- Existing La Liga durable tables remain untouched.

create table if not exists
public.league_structural_v2_observations (
    observation_key text primary key,

    league text not null,

    event_id text not null,

    snapshot_time_utc timestamptz not null,

    commence_time_utc timestamptz not null,

    payload jsonb not null,

    persisted_at_utc timestamptz not null
        default timezone('utc', now()),

    constraint league_v2_argmax_preserved
        check (
            payload->>'market_argmax'
            =
            payload->>'shadow_argmax'
        ),

    constraint league_v2_pre_kickoff
        check (
            coalesce(
                (
                    payload->>'pre_kickoff_valid'
                )::boolean,
                false
            )
        ),

    constraint league_v2_research_only
        check (
            coalesce(
                (
                    payload->>'research_only'
                )::boolean,
                false
            )
        ),

    constraint league_v2_snapshot_before_kickoff
        check (
            snapshot_time_utc
            <
            commence_time_utc
        )
);


create index if not exists
league_v2_league_event_snapshot_idx
on public.league_structural_v2_observations
(
    league,
    event_id,
    snapshot_time_utc desc
);


create table if not exists
public.league_finished_results (
    league text not null,

    season text not null,

    match_date date not null,

    match_time text,

    home_team text not null,

    away_team text not null,

    home_goals integer not null
        check (home_goals >= 0),

    away_goals integer not null
        check (away_goals >= 0),

    result text not null
        check (
            result in (
                'H',
                'D',
                'A'
            )
        ),

    source text,

    source_competition text,

    source_updated_at_utc timestamptz,

    persisted_at_utc timestamptz not null
        default timezone('utc', now()),

    primary key (
        league,
        season,
        match_date,
        home_team,
        away_team
    )
);


create index if not exists
league_finished_results_league_date_idx
on public.league_finished_results
(
    league,
    match_date
);


comment on table
public.league_structural_v2_observations
is
'Immutable multi-league Structural Edge V2 pre-kickoff research observations.';


comment on table
public.league_finished_results
is
'Immutable multi-league finished football results for live research evaluation.';


alter table
public.league_structural_v2_observations
enable row level security;

alter table
public.league_finished_results
enable row level security;


do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'league_structural_v2_observations'
          and policyname = 'service role reads league structural v2 observations'
    ) then
        create policy
        "service role reads league structural v2 observations"
        on public.league_structural_v2_observations
        for select
        to service_role
        using (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'league_structural_v2_observations'
          and policyname = 'service role inserts league structural v2 observations'
    ) then
        create policy
        "service role inserts league structural v2 observations"
        on public.league_structural_v2_observations
        for insert
        to service_role
        with check (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'league_finished_results'
          and policyname = 'service role reads league finished results'
    ) then
        create policy
        "service role reads league finished results"
        on public.league_finished_results
        for select
        to service_role
        using (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'league_finished_results'
          and policyname = 'service role inserts league finished results'
    ) then
        create policy
        "service role inserts league finished results"
        on public.league_finished_results
        for insert
        to service_role
        with check (true);
    end if;
end
$$;
