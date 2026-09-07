# CORNER_COMBINED_DISCRIMINATOR_V4

Status: PREREGISTERED FINAL HISTORICAL FREE-DATA CORNER TEST

## Goal

Run one final historical test of whether the free EPL fields already studied can jointly distinguish matches with Over 9.5 total corners.

This is explicitly an adaptive/sequential research step informed by V1-V3. It is not independent confirmation. After V4, no further feature combinations or threshold tuning on these same held-out seasons are allowed inside this corner block.

## Evidence boundary

- Historical source: live Supabase `public.matches`, EPL only.
- Allowed outcomes: 2016/2017 through 2025/2026.
- Forbidden: 2026/2027 outcomes and all existing frozen prospective-cohort outcomes.
- Read-only research only. No Supabase writes, no Odds API calls, no production `.pkl` changes, no promotion.

## Fixed inputs

For each eligible fixture, use exactly three point-in-time scores, each based only on the teams' previous 10 EPL matches:

1. `corner_state` — the fixed V1 matchup corner-total score.
2. `shot_pressure` — the fixed V3 all-shots matchup pressure score.
3. `sot_pressure` — the fixed V3 shots-on-target matchup pressure score.

Both teams must have at least 10 prior EPL matches with all required fields.

No additional football features, market prices, alternative windows, interactions, nonlinear transforms, feature selection or hyperparameter search are allowed in V4.

## Fixed model

For each held-out season, fit one ordinary least-squares linear probability model on eligible fixtures from strictly earlier seasons only:

`P_score = intercept + b1*corner_state + b2*shot_pressure + b3*sot_pressure`

Target in training: `1` when actual total corners > 9.5, else `0`.

The score is used only for ranking/AUC. It does not need to be clipped to [0,1].

Coefficients for a held-out season must never use that season's outcomes.

## Held-out seasons

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

## Primary metric and frozen decision

For each held-out season calculate ROC AUC for Over 9.5 total corners using `P_score`.

Success requires both:
- match-weighted AUC > 0.52; and
- AUC > 0.50 in at least 5 of 7 held-out seasons.

If both pass: `PORTABLE_COMBINED_DISCRIMINATOR`.
Otherwise: `NOT_PORTABLE_COMBINED_DISCRIMINATOR`.

## Stop rule

V4 is the final free historical combination test in this corner block.

If V4 fails, do not search more combinations, weights, windows or thresholds on the same historical seasons. The next meaningful information source is bookmaker corner-market data or richer event/territorial data.

If V4 passes, it still does not prove betting edge. The next required step is comparison against actual bookmaker corner lines/prices, which remains behind the existing manual paid capability gate.
