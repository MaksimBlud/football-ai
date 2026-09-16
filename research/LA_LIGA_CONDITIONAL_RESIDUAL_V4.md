# LA_LIGA_CONDITIONAL_RESIDUAL_V4

Research-only test of selective intervention over the fixed La Liga POWER market prior.

The V3 result rejected a global football correction. V4 asks a narrower question: can the same residual help only when disagreement is sufficiently large and the market is in a pre-defined confidence regime?

## Frozen design

- train residual model: 2016-17..2023-24
- gate selection: 2024-25 only
- untouched temporal OOT: 2025-26
- no 2026-27 outcomes
- market prior: raw B365 odds -> fixed POWER de-vig
- residual families: FORM, FORM_GOALS, FORM_GOALS_CORNERS, ALL_FOOTBALL
- correction strength fixed at lambda=0.25; V4 does not search lambda
- gate inputs only: residual-vs-market disagreement magnitude and market entropy
- disagreement thresholds: validation quantiles 0.50, 0.65, 0.80
- entropy thresholds: validation quantiles 0.35, 0.65, tested as LOW/HIGH regimes
- minimum acted validation sample: 30
- gate must beat POWER market on both validation Brier and LogLoss
- selected gate is frozen before 2025-26 is opened
- OOT acceptance again requires lower Brier and lower LogLoss than POWER
- otherwise exact POWER market fallback

This deliberately keeps the search small. It is a hypothesis test for gating, not an unrestricted threshold optimiser.

## Safety

Historical research only; NO_BET; no production promotion; no Supabase writes; no paid Odds API; production `.pkl` hashes must remain unchanged.
