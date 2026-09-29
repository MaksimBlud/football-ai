# MARKET_MAX_AVG_SPREAD_V1

Status: **research-only historical aggregate-market spread experiment**.

## Motivation

MARKET_BOOKMAKER_DISPERSION_V1 failed closed because only Bet365 had continuous individual-bookmaker coverage across 2019/20–2025/26.

This follow-up does not pretend Football-Data Max odds are a coherent bookmaker probability vector. Instead, Max-vs-Avg is treated only as an aggregate market breadth/spread proxy.

## Source

Zero-cost Football-Data EPL CSV files for 2019/20–2025/26.

Required standard columns:

- AvgH / AvgD / AvgA
- MaxH / MaxD / MaxA

Required closing columns:

- AvgCH / AvgCD / AvgCA

Max closing columns are not required for the primary hypothesis.

Every required triplet must have at least 90% valid coverage in every season or the experiment fails closed.

## Spread definition

For each 1X2 outcome i:

relative_gap_i = MaxOdds_i / AvgOdds_i - 1

Rows require MaxOdds_i >= AvgOdds_i > 1 for all three outcomes.

Fixture spread is the RMS of the three outcome gaps:

spread = sqrt(mean(relative_gap_H^2, relative_gap_D^2, relative_gap_A^2)).

No match outcome enters the spread calculation.

## Market probabilities

AVG_STANDARD and AVG_CLOSING are converted to probabilities with the already-frozen MULTIPLICATIVE de-vig transform.

## Repricing target

Closing movement magnitude is total-variation distance:

closing_tv = 0.5 * sum_i |p_close_i - p_open_i|.

## Outcome-error diagnostic

AVG_STANDARD multiclass Brier loss is used as a separate uncertainty diagnostic.

## Temporal threshold protocol

Discovery seasons: 2019/20–2023/24.

Using spread values only (no outcomes, no closing movement), freeze:

- LOW threshold = discovery 25th percentile
- HIGH threshold = discovery 75th percentile

These exact thresholds are then applied unchanged to 2024/25 and 2025/26.

Middle-spread fixtures are not used in the high-vs-low contrast.

## Repricing support gate

DISPERSION_REPRICING_SUPPORT requires all of:

1. discovery pooled HIGH mean closing_tv > LOW;
2. positive HIGH-minus-LOW closing_tv effect in at least 3 of 5 discovery seasons;
3. validation 2024/25 HIGH-minus-LOW effect > 0;
4. final test 2025/26 HIGH-minus-LOW effect > 0;
5. stratified bootstrap 95% CI over all seven seasons entirely above zero.

## Error support gate

DISPERSION_ERROR_SUPPORT uses the same frozen groups and requires the analogous conditions for AVG_STANDARD Brier loss.

This tests whether spread is an uncertainty flag, not a betting rule.

## Interpretation

Possible signals:

- MAX_AVG_REPRICING_SIGNAL
- MAX_AVG_ERROR_SIGNAL

If neither passes: NO_MAX_AVG_SPREAD_SIGNAL.

Any positive result remains research-only and requires a separate prospective/integration test.

## Safety

- zero paid Odds API calls;
- no Supabase reads/writes;
- no model training;
- no .pkl changes;
- no production promotion;
- JSON research artifact only.
