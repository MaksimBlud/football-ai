# SEASON_INVARIANT_CORNERS_V1

Status: PREREGISTERED / RESEARCH ONLY

## Goal

Test whether the previously identified CORNERS10 football-state signal is stable across seasons and leagues rather than being a one-season accident.

This block does not promote or replace any production model.

## Data

Use the existing leakage-safe Historical Football Signal Lab inputs and point-in-time feature builder.

Primary historical leagues:
- EPL
- La Liga
- Serie A

Primary seasons are the already configured completed historical seasons 2016-2017 through 2025-2026 where the source is available.

No 2026-2027 prospective outcomes are part of this historical evaluation.

## Primary candidate and baseline

Primary candidate: `CORNERS10`.

Primary football-only baseline: `GOALS10`.

`FORM10` remains a secondary descriptive baseline only.

The primary decision must not be switched to another candidate after seeing results.

## Evaluation design

Use expanding-season walk-forward only:
- require at least 3 earlier seasons for training;
- fit only on seasons earlier than the test season;
- evaluate on the next unseen season;
- repeat through all available seasons and leagues.

This preserves chronology. Future seasons must never influence an earlier training fold.

## Primary metrics

Use paired changes for the exact same league and test season:
- Brier score delta = candidate minus GOALS10;
- log-loss delta = candidate minus GOALS10.

Lower is better, so a negative delta is a win for CORNERS10.

Accuracy is descriptive only and is not a primary decision metric.

## Frozen stability classification

For each league separately, require at least 5 eligible unseen test seasons.

`STRONG`:
- weighted mean Brier delta < 0;
- weighted mean log-loss delta < 0;
- Brier win rate >= 70%;
- log-loss win rate >= 70%.

`SUPPORTIVE`:
- weighted mean Brier delta < 0;
- weighted mean log-loss delta < 0;
- Brier win rate >= 55%;
- log-loss win rate >= 55%;
- but STRONG criteria are not all met.

`UNSTABLE`:
- all other cases, including insufficient eligible seasons.

Overall historical portability classification:
- `PORTABLE_STRONG` only if all three primary leagues are STRONG;
- `PORTABLE_SUPPORTIVE` if no league is UNSTABLE and at least two leagues are STRONG or SUPPORTIVE;
- otherwise `NOT_PORTABLE`.

These thresholds are frozen before the new invariant report is executed.

## Window robustness

The decision candidate stays CORNERS10.

`CORNERS5` and `CORNERS15` are robustness checks only. They must not replace CORNERS10 as the primary candidate because one produces a prettier result.

Interpretation:
- if CORNERS10 is stable and the direction is broadly similar for 5/15, confidence increases;
- if only one exact window works, treat the signal as more fragile.

No threshold search over arbitrary windows is allowed.

## Market check

Only if the historical football-only portability result is PORTABLE_STRONG or PORTABLE_SUPPORTIVE do we revisit the already existing MARKET vs MARKET_CORNERS10 incremental comparison.

A football-only stable signal is not automatically useful if the bookmaker market already contains the information.

## Current-season use

The completed historical cross-season/cross-league test is the main evidence for structural stability.

Fresh 2026-2027 observations are used later as a drift monitor, not as a new 100-match discovery sample.

A future live drift monitor must have its own prospective contract and must not read outcomes belonging to any currently frozen experiment before its allowed gate.

No existing frozen prospective contract is changed by this research block.

## Safety

- research only;
- no production `.pkl` writes or promotion;
- no Supabase writes;
- no Odds API calls;
- no paid provider calls;
- no current prospective outcome peeking;
- no post-result threshold or window selection.
