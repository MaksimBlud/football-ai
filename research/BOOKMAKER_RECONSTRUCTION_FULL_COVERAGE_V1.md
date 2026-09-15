# BOOKMAKER_RECONSTRUCTION_FULL_COVERAGE_V1

Post-outcome research diagnostic comparing the two historical 1X2 sources that retain full 2025-2026 coverage: B365 and Football-Data AVG.

## Why this exists

`BOOKMAKER_RECONSTRUCTION_CONSENSUS_V1` established that PS coverage falls to zero from February 2026, while B365 and AVG both cover all 1,140 EPL/La Liga/Serie A matches in 2025-2026. The three-source common cohort therefore cannot represent a full season.

This diagnostic fixes:

- baseline source: `B365`
- candidate source: `AVG`
- de-vig method: proportional normalization

There is no outcome-based source selection in this experiment. AVG is evaluated because it is the full-coverage multi-book aggregate source identified by the coverage audit.

## Scope

Measure B365 vs AVG on the same fixtures for every season from 2016-2017 through 2025-2026, pooled and by league. Report Brier and LogLoss deltas, season persistence, league-season persistence, full coverage, and paired bootstrap uncertainty for the final season.

## Evidence class

This is explicitly `POST_OUTCOME_FULL_COVERAGE_DIAGNOSTIC`, not a new untouched OOT experiment. Some 2025-2026 outcomes were already inspected by earlier source diagnostics. Results can motivate a separately frozen prospective market-baseline contract, but cannot mutate the existing market anchor or production inference.

## Safety

Research only, `NO_BET`, no production promotion, no production `.pkl` writes, no Supabase writes, no paid provider calls, and no 2026-2027 outcomes.
