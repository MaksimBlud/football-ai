-- CORNER_TOTAL_CALIBRATED_V2
-- Read-only historical evidence query.
-- Must never include 2026/2027 outcomes.

with base as (
  select id, season, split_part(season,'/',1)::int as season_start, match_date,
         home_team, away_team, home_corners, away_corners,
         (home_corners + away_corners)::double precision as actual_total
  from public.matches
  where league='EPL'
    and season in ('2016/2017','2017/2018','2018/2019','2019/2020','2020/2021','2021/2022','2022/2023','2023/2024','2024/2025','2025/2026')
    and home_corners is not null and away_corners is not null
), team_rows as (
  select id as match_id, match_date, home_team as team, 'H'::text as side,
         home_corners::double precision as corners_for, away_corners::double precision as corners_against
  from base
  union all
  select id, match_date, away_team, 'A'::text,
         away_corners::double precision, home_corners::double precision
  from base
), hist as (
  select *,
         count(*) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) as prior_n,
         avg(corners_for) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) as cf10,
         avg(corners_against) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) as ca10
  from team_rows
), eligible as (
  select b.*,
         ((h.cf10+a.ca10)/2.0 + (a.cf10+h.ca10)/2.0) as raw_expected_total
  from base b
  join hist h on h.match_id=b.id and h.side='H'
  join hist a on a.match_id=b.id and a.side='A'
  where h.prior_n=10 and a.prior_n=10
), test_seasons as (
  select * from (values (2019),(2020),(2021),(2022),(2023),(2024),(2025)) v(test_start)
), params as (
  select ts.test_start,
         avg(e.actual_total) as baseline_total,
         regr_slope(e.actual_total,e.raw_expected_total) as slope,
         regr_intercept(e.actual_total,e.raw_expected_total) as intercept,
         count(*) as train_matches
  from test_seasons ts
  join eligible e on e.season_start < ts.test_start
  group by ts.test_start
), scored as (
  select e.season,e.season_start,e.id,e.actual_total,e.raw_expected_total,
         p.train_matches,p.baseline_total,p.slope,p.intercept,
         (p.intercept+p.slope*e.raw_expected_total) as calibrated_total
  from eligible e
  join params p on p.test_start=e.season_start
  where e.season_start between 2019 and 2025
), mae as (
  select season,count(*) as matches,min(train_matches) as train_matches,
         min(slope) as slope,min(intercept) as intercept,
         avg(abs(calibrated_total-actual_total)) as calibrated_mae,
         avg(abs(baseline_total-actual_total)) as baseline_mae,
         avg(case when (calibrated_total>9.5)=(actual_total>9.5) then 1.0 else 0.0 end) as hit_rate_9_5
  from scored group by season
), ranked as (
  select *, (actual_total>9.5)::int as y,
         rank() over(partition by season order by calibrated_total) as rmin,
         count(*) over(partition by season,calibrated_total) as tie_n
  from scored
), aucparts as (
  select *, (rmin+(tie_n-1)/2.0) as avg_rank from ranked
), auc as (
  select season,sum(y) as n_pos,count(*)-sum(y) as n_neg,
         sum(case when y=1 then avg_rank else 0 end) as sum_pos_ranks
  from aucparts group by season
)
select m.season,m.matches,m.train_matches,
       round(m.slope::numeric,6) as slope,
       round(m.intercept::numeric,6) as intercept,
       round(m.calibrated_mae::numeric,6) as calibrated_mae,
       round(m.baseline_mae::numeric,6) as baseline_mae,
       round((m.calibrated_mae-m.baseline_mae)::numeric,6) as delta_mae,
       round(((a.sum_pos_ranks-a.n_pos*(a.n_pos+1)/2.0)/(a.n_pos*a.n_neg))::numeric,6) as auc_9_5,
       round(m.hit_rate_9_5::numeric,6) as hit_rate_9_5
from mae m join auc a using(season)
order by m.season;

-- Historical source fingerprint inherited from V1:
-- rows = 3800
-- first_date = 2016-08-13
-- last_date = 2026-05-24
-- source_md5 = 4854d62ace5e66dc68ff5e6bb6d9b737
