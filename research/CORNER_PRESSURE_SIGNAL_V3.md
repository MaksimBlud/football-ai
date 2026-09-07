# CORNER_PRESSURE_SIGNAL_V3

Status: PREREGISTERED HISTORICAL RESEARCH

## Goal

Test whether recent attacking pressure, measured by shots, can distinguish EPL matches with high total corners from matches with low total corners.

V1/V2 showed a small season-portable signal for expected corner count after calibration, but almost no useful Over/Under 9.5 discrimination. V3 targets that discrimination problem directly.

## Evidence boundary

- Historical source: live Supabase `public.matches`, EPL only.
- Allowed outcomes: 2016/2017 through 2025/2026.
- Forbidden: 2026/2027 outcomes and all existing frozen prospective-cohort outcomes.
- Read-only research only. No Supabase writes, no Odds API calls, no production `.pkl` changes, no promotion.

## Fixed primary pressure score

Use only each team's previous 10 EPL matches available before the fixture.

For Home vs Away:

- expected_home_shots = (Home shots-for last 10 + Away shots-against last 10) / 2
- expected_away_shots = (Away shots-for last 10 + Home shots-against last 10) / 2
- shot_pressure_score = expected_home_shots + expected_away_shots

Both teams must have at least 10 prior EPL matches with shot data. Histories continue across season boundaries.

No weight search, window search or feature search is allowed in V3.

## Primary target

`actual total corners > 9.5`.

The fixed held-out seasons are:
- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

## Primary metric and frozen decision

For each held-out season, calculate ROC AUC using `shot_pressure_score` as the continuous score for Over 9.5 corners.

Primary portability rule:
- match-weighted AUC > 0.52; and
- AUC > 0.50 in at least 5 of 7 held-out seasons.

If both pass: `PORTABLE_PRESSURE_DISCRIMINATOR`.
Otherwise: `NOT_PORTABLE_PRESSURE_DISCRIMINATOR`.

The threshold 0.52 is fixed before evaluation and is intended to require more than a trivially-above-random average.

## Secondary diagnostics

Report but do not use to replace the primary signal:
- the same matchup formula using shots on target instead of all shots;
- season-by-season AUC for that shots-on-target score;
- simple Spearman/Pearson direction between pressure score and actual total corners if convenient.

Shots on target cannot become the primary V3 feature if it happens to look better after evaluation.

## Interpretation

A positive result means attacking-volume pressure provides season-portable information for identifying high-corner matches and can justify a separately preregistered combined corner+pressure experiment.

A negative result means the available free historical shot/corner aggregates do not give a sufficiently stable Over/Under discriminator by this mechanism. Do not retune V3 after the fact.

Neither outcome proves bookmaker edge because historical bookmaker corner prices are not available in this block.
