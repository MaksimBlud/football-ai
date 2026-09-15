# BOOKMAKER_RECONSTRUCTION_DEVIG_V1

Research-only benchmark for reconstructing bookmaker fair 1X2 probabilities from raw historical decimal odds.

## Hypothesis

The current proportional margin removal may not be the strongest fair-market baseline. Compare three fixed methods on exactly the same fixtures:

- `PROPORTIONAL`
- `POWER`
- `SHIN`

## Frozen temporal design

- validation/selection: `2024-2025`
- untouched OOT: `2025-2026`
- no `2026-2027` outcomes may be used for fitting, method selection, or evaluation
- method is selected on validation by lowest LogLoss, then Brier as deterministic tie-breaker
- OOT is read only after method selection is fixed

## Source contract

The benchmark must use raw decimal bookmaker odds before any de-vigging. It uses the same preferred source order as the historical football signal lab: `B365` then `PS` then `Avg`. The existing `market_home/market_draw/market_away` feature columns cannot be used as raw inputs because they are already proportionally normalized and no longer contain overround information.

## Metrics

Report per league and pooled:

- LogLoss
- multiclass Brier score
- accuracy for context only
- top-label calibration ECE
- overround distribution
- selected-method OOT deltas versus `PROPORTIONAL`

## Safety

- research only
- `NO_BET`
- no production promotion
- no production `.pkl` writes
- no Supabase writes
- no paid provider calls
- public Football-Data historical CSVs only

A positive result changes only the market-baseline research hypothesis. It is not evidence to mutate `MARKET_ANCHOR_1X2_V2` or production inference without a separately frozen follow-up contract.
