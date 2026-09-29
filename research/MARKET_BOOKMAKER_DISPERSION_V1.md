# MARKET_BOOKMAKER_DISPERSION_V1

Status: **research-only historical multi-bookmaker experiment**.

## Motivation

Three previous market-probability blocks kept the existing multiplicative de-vig method and rejected simple outcome-trained recalibration on Football-Data average prices.

This experiment tests genuinely new pre-match information: **cross-bookmaker disagreement**.

Two fixed hypotheses are tested:

1. an equal-weight consensus of independently quoted bookmakers can be a better probability estimate than Football-Data AvgH/AvgD/AvgA;
2. large disagreement between bookmakers can flag matches that subsequently reprice more strongly toward the Football-Data closing average.

## Source

Zero-cost Football-Data EPL CSV files, seasons 2019/20–2025/26.

No Odds API credits and no Supabase writes.

Benchmark price sets:

- AVG_STANDARD = AvgH / AvgD / AvgA
- AVG_CLOSING = AvgCH / AvgCD / AvgCA

Candidate individual standard bookmaker triplets:

- BET365 = B365H / B365D / B365A
- BETWAY = BWH / BWD / BWA
- INTERWETTEN = IWH / IWD / IWA
- PINNACLE = PSH / PSD / PSA
- WILLIAM_HILL = WHH / WHD / WHA
- VCBET = VCH / VCD / VCA

## Availability gate

An individual bookmaker is eligible only if all three columns exist and at least 90% of matches have valid decimal odds in **every** season.

At least two eligible individual bookmakers are required. Otherwise the experiment fails closed as INSUFFICIENT_SOURCE_DIVERSITY.

All primary comparisons use only the common fixtures where every eligible bookmaker plus AVG_STANDARD and AVG_CLOSING are valid.

## Probability transform

Every source uses the already-frozen MULTIPLICATIVE de-vig transform.

No Shin/Power/Additive selection is reopened.

## Consensus

For each fixture, de-vig each eligible individual bookmaker separately, then compute the equal-weight arithmetic mean of the three 1X2 probabilities.

CONSENSUS is compared against de-vigged AVG_STANDARD on the same common fixtures.

Consensus support requires:

- lower pooled LogLoss;
- lower pooled multiclass Brier;
- joint win on both metrics in at least 4 of 7 seasons;
- paired bootstrap 95% CI entirely below zero for both metrics.

## Dispersion

For fixture j and outcome i, let p_bji be the de-vigged probability from eligible bookmaker b.

Outcome dispersion is the cross-bookmaker standard deviation for each of H/D/A.

Fixture dispersion is:

sqrt(mean(std_H^2, std_D^2, std_A^2)).

This is computed without match outcomes.

Within each season, fixtures are split by dispersion quartiles:

- LOW = bottom 25%
- HIGH = top 25%

Quantiles use only pre-match bookmaker probabilities.

## Repricing target

Closing movement is measured using total-variation distance between AVG_STANDARD and AVG_CLOSING probabilities:

TV = 0.5 * sum_i |p_close_i - p_open_i|.

DISPERSION_REPRICING_SUPPORT requires:

- HIGH dispersion mean TV > LOW dispersion mean TV;
- positive HIGH-minus-LOW effect in at least 5 of 7 seasons;
- 95% bootstrap CI for the pooled HIGH-minus-LOW mean difference entirely above zero.

## Outcome-error diagnostic

A separate diagnostic compares AVG_STANDARD Brier loss in HIGH vs LOW dispersion fixtures.

DISPERSION_ERROR_SUPPORT requires:

- HIGH mean Brier > LOW mean Brier;
- positive effect in at least 5 of 7 seasons;
- 95% bootstrap CI entirely above zero.

This diagnostic is not a betting rule. It tests whether dispersion is a useful uncertainty flag.

## Interpretation

Possible independent conclusions:

- CONSENSUS_PROBABILITY_SUPPORT
- DISPERSION_REPRICING_SUPPORT
- DISPERSION_ERROR_SUPPORT

If none pass: NO_BOOKMAKER_DISPERSION_SIGNAL.

Any positive conclusion remains research-only and requires a separate prospective/integration block before production use.

## Safety

- zero paid API calls;
- no Supabase writes;
- no model training;
- no production .pkl changes;
- no promotion;
- JSON research artifact only.
