# SEASON_INVARIANT_CORNERS_V1

Status: FROZEN REPEATABLE AUDIT / RESEARCH ONLY

## Goal

Test whether the previously identified `CORNERS10` football-state signal is stable across seasons and leagues rather than being a one-season accident, and estimate how quickly a new season can provide a useful drift signal without waiting for a fixed 100-match gate.

This block does not promote or replace any production model.

## Evidence boundary

The historical season-by-season `CORNERS10` results already existed in the earlier Historical Football Signal Lab before this block was created. Therefore those historical results are retrospective evidence, not newly independent prospective evidence.

The stability rules below provide a fixed, repeatable classification. They must not be presented as if the underlying historical outcomes were unseen.

The early-drift audit is also historical pseudo-live validation. It is used to design a future monitoring cadence, not to bypass any frozen prospective experiment.

## Data

Use the existing leakage-safe Historical Football Signal Lab inputs and point-in-time feature builder.

Primary historical leagues:
- EPL
- La Liga
- Serie A

Primary seasons are the configured completed historical seasons 2016-2017 through 2025-2026 where the source is available.

No 2026-2027 prospective outcomes are part of this historical evaluation.

## Primary candidate and baseline

Primary candidate: `CORNERS10`.

Primary football-only baseline: `GOALS10`.

`FORM10` remains a secondary descriptive baseline.

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
- Brier score delta = candidate minus `GOALS10`;
- log-loss delta = candidate minus `GOALS10`.

Lower is better, so a negative delta is a win for `CORNERS10`.

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

Because earlier historical reports were already known, this classification is an operational summary of retrospective evidence, not a new independent confirmatory trial.

## Window robustness

The decision candidate stays `CORNERS10`.

`CORNERS5` and `CORNERS15` are robustness checks only. They must not replace `CORNERS10` because one produces a prettier result.

Interpretation:
- if `CORNERS10` is stable and the direction is broadly similar for 5/15, confidence increases;
- if only one exact window works, treat the signal as more fragile.

No threshold search over arbitrary windows is allowed.

## Early-season drift audit

For every held-out historical season, train on earlier seasons only, order the test season chronologically, and inspect the cumulative paired result after exactly:
- 20 matches;
- 40 matches;
- 80 matches;
- 160 matches.

Later matches must not affect an earlier checkpoint score.

The audit records:
- mean paired Brier delta;
- mean paired log-loss delta;
- fraction of season tests where `CORNERS10` is better;
- fraction where the checkpoint direction agrees with the final held-out-season direction.

Interpretation for future monitoring:
- 20 matches = very early warning only;
- 40 matches = first practical drift signal;
- 80 matches = materially stronger in-season evidence;
- 160 matches = strong in-season confirmation.

These are monitoring checkpoints, not automatic promotion gates.

## Market check

Historical market incremental evidence remains a separate question. A football-only stable signal is not automatically useful if bookmaker prices already contain the same information.

The existing MARKET vs MARKET_CORNERS10 historical comparison must remain visible alongside this block; it must not be overwritten by the football-only portability result.

## Current-season use

Completed historical cross-season/cross-league evidence is the main evidence for structural stability.

Fresh 2026-2027 observations may later be used as a drift monitor, but only under a separate prospective contract that does not read outcomes belonging to any frozen experiment before its allowed gate.

No existing frozen prospective contract is changed by this research block.

## Safety

- research only;
- no production `.pkl` writes or promotion;
- no Supabase writes;
- no Odds API calls;
- no paid provider calls;
- no current prospective outcome peeking;
- no post-result threshold or arbitrary window selection.
