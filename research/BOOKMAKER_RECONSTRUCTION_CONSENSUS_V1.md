# BOOKMAKER_RECONSTRUCTION_CONSENSUS_V1

Research-only benchmark for the source used to represent the 1X2 market.

## Why this exists

The current historical market feature chooses `B365` whenever that triplet is present, then only falls back to `PS` or `Avg`. In recent EPL, La Liga and Serie A history, B365 is therefore often the effective baseline rather than a true bookmaker consensus.

## Frozen comparison

De-vigging is held fixed to proportional normalization so this experiment isolates source quality:

- `B365` — current effective baseline
- `PS` — Pinnacle/PS source
- `AVG` — Football-Data average bookmaker odds

Head-to-head performance is calculated only on fixtures where all three source triplets are valid.

## Temporal design

- source selection: `2024-2025`
- untouched OOT: `2025-2026`
- selection metric: lowest pooled LogLoss, then Brier
- no `2026-2027` outcomes

## Coverage contract

Source availability is measured **before** common-cohort filtering. The report includes:

- total finished matches by season and league;
- complete-triplet count/fraction for B365, PS and AVG;
- all-three-sources common count/fraction;
- monthly 2025-2026 coverage by league.

The first OOT execution exposed an important limitation: the common B365+PS+AVG cohort is incomplete in 2025-2026. Therefore the common-source OOT scores are a same-fixture diagnostic only. They must not be described as evidence that a selected alternative source is better over the full 2025-2026 market cohort unless full-cohort coverage is independently established.

No fallback or hybrid source rule is introduced after seeing this result. Any future source-combination policy must be frozen in a separate experiment before its OOT outcomes are read.

## Diagnostics

Report pooled and per-league LogLoss, Brier, calibration ECE, source overround, source-probability dispersion, OOT paired bootstrap against B365, and OOT performance by dispersion quartile using thresholds frozen on validation. Coverage diagnostics are reported separately from performance diagnostics.

## Safety

Research only, `NO_BET`, no production promotion, no production `.pkl` writes, no Supabase writes and no paid provider calls.
