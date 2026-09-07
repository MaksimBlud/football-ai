-- CORNER_PRESSURE_SIGNAL_V3
-- Read-only historical evidence query. Never include 2026/2027 outcomes.

with base as (
  select id,season,split_part(season,'/',1)::int as season_start,match_date,
         home_team,away_team,home_shots,away_shots,home_shots_target,away_shots_target,
         home_corners,away_corners,(home_corners+away_corners)::double precision as actual_total_corners
  from public.matches
  where league='EPL'
    and season in ('2016/2017','2017/2018','2018/2019','2019/2020','2020/2021','2021/2022','2022/2023','2023/2024','2024/2025','2025/2026')
    and home_shots is not null and away_shots is not null
    and home_shots_target is not null and away_shots_target is not null
    and home_corners is not null and away_corners is not null
), team_rows as (
  select id match_id,match_date,home_team team,'H'::text side,
         home_shots::double precision shots_for,away_shots::double precision shots_against,
         home_shots_target::double precision sot_for,away_shots_target::double precision sot_against from base
  union all
  select id,match_date,away_team,'A'::text,
         away_shots::double precision,home_shots::double precision,
         away_shots_target::double precision,home_shots_target::double precision from base
), hist as (
  select *,
    count(*) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) prior_n,
    avg(shots_for) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) sf10,
    avg(shots_against) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) sa10,
    avg(sot_for) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) sotf10,
    avg(sot_against) over(partition by team order by match_date,match_id rows between 10 preceding and 1 preceding) sota10
  from team_rows
), scored as (
  select b.season,b.id,b.actual_total_corners,
    ((h.sf10+a.sa10)/2.0+(a.sf10+h.sa10)/2.0) shot_pressure,
    ((h.sotf10+a.sota10)/2.0+(a.sotf10+h.sota10)/2.0) sot_pressure
  from base b join hist h on h.match_id=b.id and h.side='H'
              join hist a on a.match_id=b.id and a.side='A'
  where h.prior_n=10 and a.prior_n=10 and b.season_start between 2019 and 2025
), long_scores as (
  select season,id,actual_total_corners,'SHOTS'::text signal,shot_pressure score from scored
  union all
  select season,id,actual_total_corners,'SHOTS_ON_TARGET',sot_pressure from scored
), ranked as (
  select *, (actual_total_corners>9.5)::int y,
    rank() over(partition by season,signal order by score) rmin,
    count(*) over(partition by season,signal,score) tie_n
  from long_scores
), x as (
  select *, (rmin+(tie_n-1)/2.0) avg_rank from ranked
), agg as (
  select season,signal,count(*) matches,sum(y) n_pos,count(*)-sum(y) n_neg,
    sum(case when y=1 then avg_rank else 0 end) sum_pos_ranks,
    corr(score,actual_total_corners) pearson_corr
  from x group by season,signal
)
select season,signal,matches,n_pos,n_neg,
  round(((sum_pos_ranks-n_pos*(n_pos+1)/2.0)/(n_pos*n_neg))::numeric,6) auc_9_5,
  round(pearson_corr::numeric,6) pearson_corr
from agg order by signal,season;
