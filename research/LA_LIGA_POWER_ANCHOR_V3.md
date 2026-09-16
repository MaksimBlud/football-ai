# LA_LIGA_POWER_ANCHOR_V3

Research-only follow-up to the market reconstruction and La Liga market-anchor work.

## Question

After replacing proportional margin removal with the already-selected `POWER` de-vig market prior, does any already-defined football feature family add incremental 1X2 probability quality?

## Frozen design

- league: `LA_LIGA` only
- training: `2016-2017..2023-2024`
- validation/selection: `2024-2025`
- untouched temporal OOT: `2025-2026`
- no `2026-2027` outcomes may be used
- raw historical decimal odds are mandatory; normalized market probabilities cannot reconstruct overround
- market prior: fixed `POWER` de-vig
- football feature families: `FORM`, `FORM_GOALS`, `FORM_GOALS_CORNERS`, `ALL_FOOTBALL`
- lambda grid: `0, 0.10, 0.25, 0.50, 0.75, 1.0`
- L2: unchanged at `1.0`
- validation admissibility requires improvement over POWER market on both Brier and LogLoss
- deterministic selection among admissible candidates: LogLoss, Brier, lambda, feature name
- OOT acceptance again requires improvement on both Brier and LogLoss
- failure means exact `POWER_MARKET_FALLBACK`

`lambda=0` must be bitwise identity to the POWER market probabilities. Accuracy is context only and cannot authorize acceptance.

## Evidence boundary

This is historical temporal OOT research, not prospective 2026-27 evidence. The three already-opened La Liga prospective outcomes from 2026-09 are not inputs to selection or evaluation and cannot be used to retune this contract.

## Safety

- `NO_BET`
- no production promotion
- no production `.pkl` writes
- no Supabase writes
- no paid Odds API calls
- public Football-Data history only

A positive historical result may justify a separately frozen prospective POWER-anchor experiment. It does not itself authorize production inference changes.
