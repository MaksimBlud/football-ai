# LA_LIGA_MARKET_MOVEMENT_REGIMES_V7

V6 found no accepted general predictor of the direction/magnitude of Bet365 standard-to-explicit-closing 1X2 movement. V7 changes the question without tuning V6 after OOT: can we identify, before the target is known, which matches are likely to undergo a materially large repricing?

## Frozen design

The paired market construction and temporal split are inherited from V6. Football-Data `B365H/B365D/B365A` remain **standard**, not opening. `B365CH/B365CD/B365CA` are explicit closing fields. Both are POWER de-vigged. Match results are not used.

Movement magnitude is the Euclidean norm of the two independent closing-minus-standard log probability ratio changes: home/draw and away/draw. The material-movement threshold is the 75th percentile of **training-only** movement magnitude. It is then frozen for 2024-25 validation and 2025-26 untouched OOT.

Baseline probability is the training prevalence of material movement. Candidate models use fixed logistic regression (`C=0.1`) over standard market state alone or standard market state plus the existing leakage-safe FORM, FORM_GOALS, FORM_GOALS_CORNERS, or ALL_FOOTBALL families.

A candidate is admissible only if it improves both Brier and LogLoss versus the constant-prevalence baseline on 2024-25. The selected candidate is accepted only if it again improves both proper scores on untouched 2025-26. ROC AUC and average precision are diagnostic only.

No quantile, C, feature subset, threshold, or season is retuned after OOT. Failure means `CONSTANT_PREVALENCE_FALLBACK`.

## Safety

Historical research only; `NO_BET`; no production promotion; no production `.pkl` writes; no Supabase writes; no paid Odds API calls; no 2026-27 data.
