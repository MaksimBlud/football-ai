-- Research-only durable state for the La Liga Structural V2 live cycle.
-- Additive only.

create table if not exists
public.la_liga_structural_v2_observations (
    observation_key text primary key,
    league text not null
        check (league = 'LA_LIGA'),
    event_id text not null,
    snapshot_time_utc timestamptz not null,
    commence_time_utc timestamptz not null,
    payload jsonb not null,
    persisted_at_utc timestamptz not null
        default timezone('utc', now()),

    constraint la_liga_v2_argmax_preserved
        check (
            payload->>'market_argmax'
            =
            payload->>'shadow_argmax'
        ),

    constraint la_liga_v2_pre_kickoff
        check (
            coalesce(
                (
                    payload->>'pre_kickoff_valid'
                )::boolean,
                false
            )
        ),

    constraint la_liga_v2_research_only
        check (
            coalesce(
                (
                    payload->>'research_only'
                )::boolean,
                false
            )
        ),

    constraint la_liga_v2_snapshot_before_kickoff
        check (
            snapshot_time_utc
            <
            commence_time_utc
        )
);

create index if not exists
la_liga_v2_event_snapshot_idx
on public.la_liga_structural_v2_observations
(
    event_id,
    snapshot_time_utc desc
);


create table if not exists
public.la_liga_finished_results (
    season text not null,
    league text not null
        check (league = 'LA_LIGA'),
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
    source text not null,
    source_competition text not null,
    source_updated_at_utc timestamptz not null,
    persisted_at_utc timestamptz not null
        default timezone('utc', now()),

    primary key (
        season,
        match_date,
        home_team,
        away_team
    )
);

create index if not exists
la_liga_finished_results_date_idx
on public.la_liga_finished_results
(
    match_date
);

comment on table
public.la_liga_structural_v2_observations
is
'Immutable research-only Structural Edge V2 pre-kickoff observations.';

comment on table
public.la_liga_finished_results
is
'Immutable completed La Liga results for live research evaluation.';


-- ---------------------------------------------------------------------
-- RLS
--
-- These are backend research tables.
-- The project uses the Supabase service_role key for the scheduled
-- operating cycle. Only read and insert policies are provided.
-- ---------------------------------------------------------------------

alter table
public.la_liga_structural_v2_observations
enable row level security;

alter table
public.la_liga_finished_results
enable row level security;


do $$
begin
    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'la_liga_structural_v2_observations'
          and policyname = 'service role reads structural v2 observations'
    ) then
        create policy
        "service role reads structural v2 observations"
        on public.la_liga_structural_v2_observations
        for select
        to service_role
        using (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'la_liga_structural_v2_observations'
          and policyname = 'service role inserts structural v2 observations'
    ) then
        create policy
        "service role inserts structural v2 observations"
        on public.la_liga_structural_v2_observations
        for insert
        to service_role
        with check (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'la_liga_finished_results'
          and policyname = 'service role reads la liga finished results'
    ) then
        create policy
        "service role reads la liga finished results"
        on public.la_liga_finished_results
        for select
        to service_role
        using (true);
    end if;

    if not exists (
        select 1
        from pg_policies
        where schemaname = 'public'
          and tablename = 'la_liga_finished_results'
          and policyname = 'service role inserts la liga finished results'
    ) then
        create policy
        "service role inserts la liga finished results"
        on public.la_liga_finished_results
        for insert
        to service_role
        with check (true);
    end if;
end
$$;
