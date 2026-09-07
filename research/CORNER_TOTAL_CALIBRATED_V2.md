# CORNER_TOTAL_CALIBRATED_V2

Status: PREREGISTERED HISTORICAL RESEARCH

## Goal

Test whether the fixed CORNER_TOTAL_SIGNAL_V1 score contains useful total-corners information after honest out-of-sample calibration.

V1 failed as a raw predictor. V2 is allowed to calibrate/shrink the same fixed score, but it may not add new features, change the 10-match window, search weights, or inspect a held-out season while fitting that season's calibration.

## Evidence boundary

- Historical source: live Supabase `public.matches`, EPL only.
- Allowed outcomes: 2016/2017 through 2025/2026.
- Forbidden: 2026/2027 outcomes and all existing frozen prospective-cohort outcomes.
- Read-only research only. No Supabase writes, no Odds API calls, no production `.pkl` changes, no promotion.

## Fixed raw score

Use exactly the V1 score:

- expected_home = (Home corners-for last 10 + Away corners-against last 10) / 2
- expected_away = (Away corners-for last 10 + Home corners-against last 10) / 2
- raw_expected_total = expected_home + expected_away

Fixture eligibility is unchanged from V1: both teams must have 10 prior EPL matches.

## Calibration

For each held-out test season, fit one ordinary least-squares line on eligible fixtures from strictly earlier seasons only:

`calibrated_total = intercept + slope * raw_expected_total`

Both `intercept` and `slope` are estimated only from earlier seasons.

No clipping, no manual shrinkage constant, no regularization search, and no refit using the held-out season.

## Baseline

For each held-out season, baseline prediction is the mean actual total corners from the same strictly earlier-season training fixtures used to fit calibration.

The baseline is frozen at the start of the held-out season, just like the calibrated model.

## Held-out seasons

- 2019/2020
- 2020/2021
- 2021/2022
- 2022/2023
- 2023/2024
- 2024/2025
- 2025/2026

## Primary metric and decision

For each held-out season compute MAE for:
- calibrated_total;
- training-mean baseline.

`delta_mae = calibrated_mae - baseline_mae`.
Lower is better.

Frozen portability rule:
- weighted mean delta MAE < 0; and
- calibrated model beats baseline in at least 5 of 7 held-out seasons.

If both pass: `PORTABLE_CALIBRATED_TOTAL_SIGNAL`.
Otherwise: `NOT_PORTABLE_CALIBRATED_TOTAL_SIGNAL`.

## Secondary diagnostics

Report, but do not use to override the primary decision:
- fitted slope and intercept for each test season;
- AUC for actual total corners > 9.5 using `calibrated_total` as score;
- simple hit rate from `calibrated_total > 9.5`.

The primary line remains 9.5. No threshold search is allowed.

## Interpretation

A positive V2 means recent corner-state has weak but usable season-portable information after honest shrinkage/calibration.

A negative V2 means the simple 10-match aggregate does not contain enough stable information for total-corners prediction by itself. In that case the next experiment, if any, must add a new preregistered football mechanism (for example shots/territorial pressure or venue-specific corner state) rather than tuning V2 after the fact.

Neither outcome proves bookmaker edge without historical or prospective corner-market prices.
