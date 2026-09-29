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


## First frozen execution

First complete run:

- workflow run: 36580542534
- head: 028ef8fb2034d6c1dd6d9c20a558e9816c280483
- artifact: 11039093220
- artifact digest: sha256:d618c7a6ca643b780c8b2f20912145e3593abd6319c0bf188882363bd40c893e

All 2,660 rows passed the frozen source/coverage gate.

Discovery-only spread thresholds:

- LOW q25 = 0.0417778
- HIGH q75 = 0.0626432

### Preregistered repricing hypothesis

The predicted HIGH > LOW repricing effect did not reproduce.

- positive discovery seasons: 2/5
- positive seasons overall: 2/7
- pooled HIGH-minus-LOW closing TV: -0.0016935
- 95% bootstrap CI: [-0.0034702, +0.0000805]

Result: no MAX_AVG_REPRICING_SIGNAL.

### Preregistered error hypothesis

The predicted HIGH > LOW market-error effect failed in the opposite direction.

- positive discovery seasons: 0/5
- positive seasons overall: 0/7
- pooled HIGH-minus-LOW AVG_STANDARD Brier: -0.2144139
- 95% bootstrap CI: [-0.2559912, -0.1723928]

Result: no MAX_AVG_ERROR_SIGNAL under the frozen direction.

Frozen V1 interpretation:

NO_MAX_AVG_SPREAD_SIGNAL

## Post-hoc observation — hypothesis generator only

HIGH spread had **lower**, not higher, AVG_STANDARD Brier in every one of the seven EPL
seasons. The pooled difference is large and the bootstrap interval is entirely negative.

This inverse direction was not preregistered and therefore is **not** accepted as V1
evidence.

A likely confound is market confidence: Max-vs-Avg relative gaps may mechanically become
larger in strong-favorite matches, which are already easier for the market to predict.

The correct next step is a separate frozen replication on other leagues with explicit
control for baseline favorite probability. V1 is not reinterpreted after seeing outcomes.
