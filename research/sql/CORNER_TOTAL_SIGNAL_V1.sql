-- CORNER_TOTAL_SIGNAL_V1
-- Read-only historical evidence query.
-- Must never include 2026/2027 outcomes.

with base as (
  select id, season, split_part(season,'/',1)::int as season_start,
         match_date, home_team, away_team, home_corners, away_corners,
         (home_corners + away_corners)::double precision as actual_total
  from public.matches
  where league='EPL'
    and season in ('2016/2017','2017/2018','2018/2019','2019/2020','2020/2021','2021/2022','2022/2023','2023/2024','2024/2025','2025/2026')
    and home_corners is not null and away_corners is not null
), team_rows as (
  select id as match_id, season, season_start, match_date, home_team as team,
         'H'::text as side, home_corners::double precision as corners_for,
         away_corners::double precision as corners_against
  from base
  union all
  select id, season, season_start, match_date, away_team, 'A'::text,
         away_corners::double precision, home_corners::double precision
  from base
), hist as (
  select *,
         count(*) over (
           partition by team order by match_date, match_id
           rows between 10 preceding and 1 preceding
         ) as prior_n,
         avg(corners_for) over (
           partition by team order by match_date, match_id
           rows between 10 preceding and 1 preceding
         ) as cf10,
         avg(corners_against) over (
           partition by team order by match_date, match_id
           rows between 10 preceding and 1 preceding
         ) as ca10
  from team_rows
), features as (
  select b.*,
         ((h.cf10 + a.ca10)/2.0 + (a.cf10 + h.ca10)/2.0) as expected_total,
         h.prior_n as home_prior_n,
         a.prior_n as away_prior_n
  from base b
  join hist h on h.match_id=b.id and h.side='H'
  join hist a on a.match_id=b.id and a.side='A'
), eligible as (
  select *,
         avg(actual_total) over (
           order by match_date, id
           rows between unbounded preceding and 1 preceding
         ) as baseline_total
  from features
  where home_prior_n=10 and away_prior_n=10
), test as (
  select *
  from eligible
  where season_start between 2019 and 2025
    and baseline_total is not null
), mae as (
  select season, count(*) as matches,
         avg(abs(expected_total-actual_total)) as signal_mae,
         avg(abs(baseline_total-actual_total)) as baseline_mae,
         avg(case when (expected_total>9.5)=(actual_total>9.5) then 1.0 else 0.0 end) as hit_rate_9_5
  from test
  group by season
), ranked as (
  select *,
         (actual_total>9.5)::int as y,
         rank() over (partition by season order by expected_total) as rmin,
         count(*) over (partition by season, expected_total) as tie_n
  from test
), auc_parts as (
  select *, (rmin + (tie_n-1)/2.0) as avg_rank
  from ranked
), auc as (
  select season,
         sum(y) as n_pos,
         count(*)-sum(y) as n_neg,
         sum(case when y=1 then avg_rank else 0 end) as sum_pos_ranks
  from auc_parts
  group by season
)
select m.season, m.matches,
       round(m.signal_mae::numeric,6) as signal_mae,
       round(m.baseline_mae::numeric,6) as baseline_mae,
       round((m.signal_mae-m.baseline_mae)::numeric,6) as delta_mae,
       round(((a.sum_pos_ranks-a.n_pos*(a.n_pos+1)/2.0)/(a.n_pos*a.n_neg))::numeric,6) as auc_9_5,
       round(m.hit_rate_9_5::numeric,6) as hit_rate_9_5
from mae m
join auc a using (season)
order by m.season;

-- Historical source fingerprint used when the reference evidence was pinned:
-- rows = 3800
-- first_date = 2016-08-13
-- last_date = 2026-05-24
-- source_md5 = 4854d62ace5e66dc68ff5e6bb6d9b737
--
-- Fingerprint definition:
-- select md5(string_agg(concat_ws('|',season,match_date::text,home_team,away_team,
--        home_corners::text,away_corners::text), E'\n' order by season,match_date,id))
-- from public.matches
-- where league='EPL' and season in (...same ten historical seasons...)
--   and home_corners is not null and away_corners is not null;
