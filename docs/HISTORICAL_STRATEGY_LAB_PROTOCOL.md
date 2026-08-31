# Historical Strategy Lab protocol

Status: research-only.

This lab is for hypothesis discovery on historical matches. It is not the forward canonical OOS sample and must never be merged conceptually with the live prediction ledger when reporting evidence.

## Data contract

Use only bookmaker 1X2 prices that are demonstrably pre-match for the decision time being simulated. Football-Data opening-style columns and closing-style columns are different decision-time experiments and must be reported separately. Never use a closing column while claiming an earlier decision time.

Minimum normalized fields:

- `league`
- `season`
- `result` (`H`, `D`, `A`)
- `market_home_odds`
- `market_draw_odds`
- `market_away_odds`

The lab recomputes no-vig probabilities from those odds. Results are labels only and are never used to construct the market probabilities.

## First baseline

The first strategy is deliberately simple: choose the largest no-vig market probability (the market favourite), stake one unit, and settle at the exact historical odds supplied to the lab.

Report:

- matches and wins;
- top-pick accuracy;
- multiclass Brier score;
- multiclass log loss;
- average selected odds;
- flat-stake profit and ROI;
- maximum drawdown;
- fixed confidence buckets;
- fixed odds buckets;
- league × season stability.

Fixed descriptive buckets are preferred before any threshold search so that the first pass is not silently optimized to the same history it is evaluated on.

## Discovery versus validation

Historical data may be used to discover candidate rules. Once a candidate rule is selected, freeze its definition and evaluate it on a chronologically later holdout or walk-forward split. The live canonical ledger remains the final forward OOS confirmation and must not be used for repeated tuning.

A candidate strategy must record:

1. source and exact odds columns;
2. simulated decision time (opening, closing, or another explicit timestamp);
3. discovery seasons;
4. untouched validation seasons;
5. rule definition before validation;
6. number of bets, ROI, drawdown, Brier/log loss and season-level stability.

## Current repository source status

The repository already contains Football-Data historical market tooling. EPL and La Liga runtime configuration covers seasons 2016-2017 through 2025-2026. RPL historical provider identifiers remain unresolved and must not be guessed. Raw historical CSVs are runtime/research data and are not committed to Git.

Other operational leagues should enter Historical Strategy Lab only after their historical provider contract and team normalization are explicitly verified.

## Safety

This lab must not:

- train or promote a production model;
- change Structural parameters;
- write Supabase;
- alter scheduled live workflows;
- modify production `.pkl` artifacts.
