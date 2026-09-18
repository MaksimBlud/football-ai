# CORNER_REGIME_ADJUSTED_DIRECTION_V1

Status: **PREREGISTERED / THIRD UNTOUCHED FREE SAMPLE / MARKET-ONLY**

## Purpose

This experiment asks the next question after `CORNER_REPRICING_DIRECTION_REPLICATION_V1`.

The already-supported result is that opening `FAIR_CENTRE` helps identify corner markets with elevated repricing magnitude risk. The unresolved question is whether the opening state contains **individual direction information beyond a contemporaneous market-wide regime**.

This experiment therefore does **not** test whether fresh moves are simply more often upward than 50/50.

Primary question:

> within matches exposed to the same league-day market regime, does lower opening `FAIR_CENTRE` identify the match whose reconstructed Bet365 corner-market centre subsequently moves farther upward relative to its peers?

A common upward or downward shift affecting every match in the same league-day block cannot create a positive primary result because the test uses only within-block ordering.

## Frozen prior data

Two previously opened datasets remain immutable:

1. the original 55-row V1 discovery sample from artifacts `10503575942` and `10506736726`;
2. the 50-row fresh replication selected in artifact `10551727936`.

The 50-row replication closing outcomes must **not** be used for feature choice, fitting, threshold selection or effect-size tuning in this experiment.

Artifact `10551727936` may be read only to obtain the fixture IDs from its `selected_fixtures.json` so those fixtures can be excluded from the next sample.

The original 55-row V1 data are used only to reconstruct the already-defined `FAIR_CENTRE` representation and to exclude their fixture IDs. No new direction classifier is fit.

## Frozen third-sample selection

Use a new set of previously unused provider fixture IDs.

Leagues:

- EPL
- LA_LIGA
- SERIE_A
- BUNDESLIGA
- LIGUE_1

For each league:

1. fetch completed fixtures from the provider Free endpoint;
2. exclude every fixture ID from the original 55-row V1 sample;
3. exclude every fixture ID in the prior 50-row replication `selected_fixtures.json`;
4. sort remaining completed fixtures by kickoff descending, then fixture ID ascending;
5. select the first **10** fixtures;
6. do not replace a selected fixture because its corner market is inconvenient;
7. if the selected fixture lacks a structurally valid Bet365 full-time corner opening+closing market, keep it selected but mark it ineligible.

Target selection = 50 previously unused fixtures.

No paid endpoint or subscription is allowed.

## Frozen market representation

Use exactly the existing V1 reconstruction:

- proportional de-vig of Over/Under prices;
- integer and half-integer corner lines only;
- Poisson-implied opening and closing market centre;
- `centre_delta = closing_lambda - opening_lambda`;
- `FAIR_CENTRE = opening_lambda`.

Quarter-lines and malformed markets are excluded, not approximated.

No match outcome, CORNERS10, team form, injuries, xG, 1X2, totals, handicaps or ROI variables are allowed.

## Frozen direction score

There is exactly one candidate opening-state score:

`direction_score = -opening_lambda`

Higher score therefore means lower opening `FAIR_CENTRE`.

Frozen directional hypothesis:

> lower opening `FAIR_CENTRE` is associated with a stronger upward closing repricing relative to contemporaneous peers.

No feature search, sign flip, coefficient fit, league-specific refit or threshold search is allowed after fresh closing data are opened.

## Contemporaneous regime blocks

For every eligible fresh row define:

`kickoff_date_utc = UTC calendar date of kickoff`

and:

`regime_block = (league, kickoff_date_utc)`

Only pairs of matches inside the **same league and same UTC kickoff date** are compared in the primary statistic.

This design removes any additive common regime inside that block. For example, if all Bet365 corner markets in an EPL Saturday block receive a +0.30 centre shift, that +0.30 disappears from every pairwise comparison.

## Primary statistic: within-regime pairwise concordance

For every unordered pair of eligible matches inside a regime block:

- skip the pair if the two opening `FAIR_CENTRE` values are tied;
- skip the pair if the two `centre_delta` values are tied;
- otherwise call the pair **concordant** when the match with lower opening `FAIR_CENTRE` has the larger `centre_delta`.

Primary effect size:

`concordance = concordant_pairs / comparable_pairs`

Interpretation:

- `0.50` = no individual directional ranking signal;
- above `0.50` = lower opening `FAIR_CENTRE` tends to identify the stronger upward / less downward mover inside the same contemporaneous regime;
- below `0.50` = relationship runs opposite to the frozen hypothesis.

## Frozen regime-preserving null test

Use **20,000** deterministic permutations with RNG seed **20260918**.

For every permutation:

- keep all opening scores fixed;
- independently shuffle `centre_delta` **only within each regime block**;
- recompute pooled pairwise concordance.

This preserves, exactly, each league-day block's:

- number of matches;
- distribution of upward/downward/zero moves;
- movement magnitudes;
- market-wide directional regime.

One-sided permutation p-value:

`p = (1 + count(permuted_concordance >= observed_concordance)) / (20000 + 1)`

## Frozen sample gate

Evaluation is valid only if all are true:

- at least **30** eligible fresh rows pooled;
- at least **4** leagues contribute at least one comparable pair;
- at least **8** regime blocks contribute at least one comparable pair;
- at least **40** comparable pairs pooled.

Otherwise verdict = `SAMPLE_TOO_SMALL`.

## Frozen confirmation gate

Individual direction discrimination is confirmed only if all are true:

- sample gate passes;
- pooled concordance >= **0.60**;
- one-sided regime-preserving permutation p-value < **0.10**.

Verdicts:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`
- `SAMPLE_TOO_SMALL`

No alternative threshold or secondary metric may replace the primary gate after fresh closing data are opened.

## Diagnostics only

Report but do not gate on:

- overall positive/negative/zero movement counts;
- per-league positive shares;
- per-regime-block median `centre_delta`;
- per-league concordance;
- top-versus-bottom direction-score residual spread after subtracting the regime-block median.

These diagnostics are for interpretation only.

## Safety

- research-only;
- `NO_BET`;
- no match outcomes;
- no CORNERS10 / football-state inputs;
- no ROI optimization;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid provider request;
- no use of the prior 50-row replication closing outcomes for tuning;
- no post-result retuning;
- production artifact hash guard required.
