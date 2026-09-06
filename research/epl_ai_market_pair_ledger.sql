-- Research only: prospective EPL Football-AI-vs-market paired evidence.
-- Deliberately contains no outcome/result columns.

create table if not exists public.epl_ai_market_pair_ledger (
    pair_key text primary key,
    experiment_id text not null default 'EPL_AI_MARKET_PAIR_V1',
    league text not null,
    event_id text not null,
    provider_home_team text not null,
    provider_away_team text not null,
    model_home_team text not null,
    model_away_team text not null,
    kickoff_utc timestamptz not null,
    market_snapshot_time_utc timestamptz not null,
    model_generated_at_utc timestamptz not null,
    market_home_prob double precision not null,
    market_draw_prob double precision not null,
    market_away_prob double precision not null,
    model_home_prob double precision not null,
    model_draw_prob double precision not null,
    model_away_prob double precision not null,
    raw_model_home_prob double precision not null,
    raw_model_draw_prob double precision not null,
    raw_model_away_prob double precision not null,
    model_artifact_sha256 text not null,
    calibrator_artifact_sha256 text not null,
    code_commit_sha text not null,
    history_max_match_date date not null,
    history_rows integer not null check (history_rows > 0),
    created_at_utc timestamptz not null default now(),
    constraint epl_ai_pair_experiment_ck check (experiment_id = 'EPL_AI_MARKET_PAIR_V1'),
    constraint epl_ai_pair_league_ck check (league = 'EPL'),
    constraint epl_ai_pair_market_pre_kickoff_ck check (market_snapshot_time_utc < kickoff_utc),
    constraint epl_ai_pair_model_pre_kickoff_ck check (model_generated_at_utc < kickoff_utc),
    constraint epl_ai_pair_history_before_market_ck check (history_max_match_date < (market_snapshot_time_utc at time zone 'UTC')::date),
    constraint epl_ai_pair_market_prob_ck check (
      market_home_prob between 0 and 1 and market_draw_prob between 0 and 1 and market_away_prob between 0 and 1
      and abs((market_home_prob + market_draw_prob + market_away_prob) - 1.0) <= 0.000001
    ),
    constraint epl_ai_pair_model_prob_ck check (
      model_home_prob between 0 and 1 and model_draw_prob between 0 and 1 and model_away_prob between 0 and 1
      and abs((model_home_prob + model_draw_prob + model_away_prob) - 1.0) <= 0.000001
    ),
    constraint epl_ai_pair_raw_model_prob_ck check (
      raw_model_home_prob between 0 and 1 and raw_model_draw_prob between 0 and 1 and raw_model_away_prob between 0 and 1
      and abs((raw_model_home_prob + raw_model_draw_prob + raw_model_away_prob) - 1.0) <= 0.000001
    )
);

create unique index if not exists epl_ai_market_pair_identity_uq
    on public.epl_ai_market_pair_ledger (
        event_id,
        market_snapshot_time_utc,
        model_artifact_sha256,
        calibrator_artifact_sha256
    );

create index if not exists epl_ai_market_pair_kickoff_idx
    on public.epl_ai_market_pair_ledger (kickoff_utc, event_id);

-- Keep the table append-only for normal API roles. Service-role/admin bypass remains
-- available for database administration, but the scheduled collector never updates rows.
revoke update, delete, truncate on public.epl_ai_market_pair_ledger from anon, authenticated;
grant select, insert on public.epl_ai_market_pair_ledger to anon, authenticated;
