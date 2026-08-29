-- Canonical append-only prediction ledger.
--
-- Stores immutable pre-match prediction states for research/evaluation.
-- Does not replace league_structural_v2_observations or
-- league_finished_results.

create table if not exists public.league_prediction_ledger (
    prediction_key text primary key,

    league text not null,
    event_id text not null,

    home_team text not null,
    away_team text not null,

    kickoff_utc timestamptz not null,
    prediction_time_utc timestamptz not null,
    snapshot_time_utc timestamptz not null,

    hours_to_kickoff double precision,

    market_home_prob double precision not null,
    market_draw_prob double precision not null,
    market_away_prob double precision not null,

    market_pick text not null,
    market_pick_probability double precision not null,

    market_top_probability double precision not null,
    market_second_probability double precision not null,
    market_probability_margin double precision not null,

    structural_status text,

    structural_home_prob double precision,
    structural_draw_prob double precision,
    structural_away_prob double precision,

    structural_pick text,
    structural_pick_probability double precision,

    structural_top_probability double precision,
    structural_second_probability double precision,
    structural_probability_margin double precision,

    structural_score double precision,
    structural_applied boolean not null default false,

    prediction_mode text not null,

    observation_key text,

    created_at_utc timestamptz not null default now(),

    constraint league_prediction_market_home_prob_check
        check (
            market_home_prob >= 0
            and market_home_prob <= 1
        ),

    constraint league_prediction_market_draw_prob_check
        check (
            market_draw_prob >= 0
            and market_draw_prob <= 1
        ),

    constraint league_prediction_market_away_prob_check
        check (
            market_away_prob >= 0
            and market_away_prob <= 1
        ),

    constraint league_prediction_market_pick_check
        check (
            market_pick in ('H', 'D', 'A')
        ),

    constraint league_prediction_mode_check
        check (
            prediction_mode in (
                'MARKET_ONLY',
                'STRUCTURAL_V2'
            )
        ),

    constraint league_prediction_structural_pick_check
        check (
            structural_pick is null
            or structural_pick in ('H', 'D', 'A')
        ),

    constraint league_prediction_market_sum_check
        check (
            abs(
                (
                    market_home_prob
                    + market_draw_prob
                    + market_away_prob
                ) - 1.0
            ) <= 0.01
        ),

    constraint league_prediction_structural_sum_check
        check (
            (
                structural_home_prob is null
                and structural_draw_prob is null
                and structural_away_prob is null
            )
            or
            abs(
                (
                    structural_home_prob
                    + structural_draw_prob
                    + structural_away_prob
                ) - 1.0
            ) <= 0.01
        )
);


create index if not exists
    league_prediction_ledger_league_idx
on public.league_prediction_ledger (
    league
);


create index if not exists
    league_prediction_ledger_event_idx
on public.league_prediction_ledger (
    league,
    event_id
);


create index if not exists
    league_prediction_ledger_kickoff_idx
on public.league_prediction_ledger (
    kickoff_utc
);


create index if not exists
    league_prediction_ledger_prediction_time_idx
on public.league_prediction_ledger (
    prediction_time_utc
);


create index if not exists
    league_prediction_ledger_snapshot_idx
on public.league_prediction_ledger (
    league,
    snapshot_time_utc
);
