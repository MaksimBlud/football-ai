# LA_LIGA_STANDARD_TO_CLOSE_SIGNAL_V6

V3 rejected a global football residual over the La Liga POWER 1X2 prior, V4's conditional residual failed untouched OOT, and V5 found no accepted multi-market replacement. V6 changes the target: instead of predicting the match outcome, it asks whether pre-match football state can predict how the bookmaker's 1X2 market later moves toward its explicit closing fields.

## Terminology and target contract

Football-Data `B365H/B365D/B365A` are labeled **standard**, not opening. The experiment makes no claim about their exact timestamp. `B365CH/B365CD/B365CA` are the explicit closing fields. Only rows with valid paired standard and closing triplets are eligible.

Both triplets are converted to fair probabilities with the already-used POWER de-vig. The two regression targets are closing-minus-standard changes in `log(P_home/P_draw)` and `log(P_away/P_draw)`. This avoids a redundant three-probability target while preserving market direction. Match outcome is not a target or feature.

## Frozen temporal design

- La Liga only.
- Train: 2016-17 through 2023-24.
- Selection: 2024-25 only.
- Untouched temporal OOT: 2025-26.
- No 2026-27 outcomes or prices.
- Baseline: zero predicted movement.
- Candidate families: standard POWER market state alone, then market state plus each already-defined leakage-safe football family: FORM, FORM_GOALS, FORM_GOALS_CORNERS, ALL_FOOTBALL.
- Model: fixed multi-output Ridge regression, alpha=10.0; median imputation and scaling fit on training data only.
- Selection requires lower MAE and lower RMSE than zero movement on 2024-25.
- OOT acceptance again requires lower MAE and lower RMSE on 2025-26.
- Direction accuracy is diagnostic only and cannot authorize acceptance.
- Failure means `ZERO_MOVEMENT_FALLBACK`.

This is deliberately a compact hypothesis test. V6 does not search alpha, target transforms, thresholds, seasons, or arbitrary feature subsets after seeing validation/OOT results.

## Interpretation

A positive result would mean the available pre-match information contains repeatable signal about later bookmaker repricing. It would not by itself establish betting value, because historical standard fields have no proven collection timestamp and are not equivalent to a live timestamped snapshot. Any live follow-up must separately freeze a timestamped observed snapshot and compare it with the true last pre-kickoff snapshot.

## Safety

Historical research only; `NO_BET`; no production promotion; no production `.pkl` writes; no Supabase writes; no paid Odds API calls. Production model hashes must remain unchanged.
