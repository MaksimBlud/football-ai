# BOOKMAKER_RECONSTRUCTION_CONSENSUS_V1

Research-only benchmark for the source used to represent the 1X2 market.

## Why this exists

The current historical market feature chooses `B365` whenever that triplet is present, then only falls back to `PS` or `Avg`. In recent EPL, La Liga and Serie A history, B365 is available on the full validation/OOT cohorts, so the current baseline is effectively one bookmaker rather than a market consensus.

## Frozen comparison

De-vigging is held fixed to proportional normalization so this experiment isolates source quality:

- `B365` — current effective baseline
- `PS` — Pinnacle/PS source
- `AVG` — Football-Data average bookmaker odds

Only fixtures where all three source triplets are valid are compared.

## Temporal design

- source selection: `2024-2025`
- untouched OOT: `2025-2026`
- selection metric: lowest pooled LogLoss, then Brier
- no `2026-2027` outcomes

## Diagnostics

Report pooled and per-league LogLoss, Brier, calibration ECE, source overround, source-probability dispersion, OOT paired bootstrap against B365, and OOT performance by dispersion quartile using thresholds frozen on validation.

## Safety

Research only, `NO_BET`, no production promotion, no production `.pkl` writes, no Supabase writes and no paid provider calls.
