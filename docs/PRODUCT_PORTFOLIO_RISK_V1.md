# Product Portfolio / Risk Layer v1

Version: `product-portfolio-risk.v1`

## Purpose

This layer defines how Football AI treats multiple simultaneous product signals
and future actionable betting decisions without inventing a staking system.

It separates two concepts:

1. **Signal inventory** — model forecasts, alternative forecasts and value
   signals shown by the product.
2. **Actionable portfolio** — only selections explicitly authorized by a future
   betting policy via `bet_decision.status == "bet"`.

A forecast is not a bet. A positive raw EV value signal is not a bet. Therefore
neither creates portfolio exposure by itself.

## Current product state

Product Decision Framework v1 emits `bet_decision.status = no_bet`.
Consequently Portfolio/Risk v1 must report:

`NO_ACTIONABLE_EXPOSURE`

for the current live product unless a future separately validated betting policy
changes that contract.

## Structural risk rules

### Exact duplicates

The exact same actionable `(fixture, market, selection)` appearing more than once
is blocked as `EXACT_DUPLICATE_POSITION`.

### One fixture = one risk slot

Until Football AI has a validated within-fixture covariance/correlation model,
multiple actionable positions on the same match are blocked.

The v1 limit is therefore:

`MAX_ACTIONABLE_RISK_SLOTS_PER_FIXTURE = 1`

This is a conservative structural safety rule, not an empirical claim that two
markets always have correlation 1.0.

It means that Over 2.5, BTTS Yes and Home Win from the same fixture must not be
counted as three independent portfolio risks merely because their individual
probabilities/EVs look attractive.

### Conflicting same-market selections

Different actionable selections from the same market/fixture are blocked as
`CONFLICTING_SELECTIONS_SAME_MARKET`.

Examples:

- HOME and AWAY on the same 1X2 market;
- OVER_2_5 and UNDER_2_5 on the same total line.

### Probability and EV aggregation

Product Portfolio/Risk v1 never adds probabilities or raw EV values across
signals.

Neither of these is allowed:

- `EV(A) + EV(B)` as portfolio EV when covariance is unknown;
- treating two same-match forecasts as two independent confidence observations.

## Concentration

For future actionable positions the layer reports descriptive counts by:

- league;
- team.

These are **position counts, not money exposure**.

No league/team monetary caps are defined in v1 because Football AI does not yet
have an approved bankroll/staking policy. A later policy may introduce such caps,
but it must do so explicitly and with regression coverage.

## Staking / bankroll boundary

Portfolio/Risk v1 does not define:

- bankroll size;
- stake amount;
- stake units;
- bankroll fraction;
- Kelly fraction;
- maximum monetary exposure;
- portfolio VaR;
- stop-loss / drawdown rules.

If fields such as `stake`, `stake_units`, `bankroll_fraction` or `kelly_fraction`
appear in a future bet decision before a staking policy is approved, the risk
layer blocks the portfolio with `UNAPPROVED_STAKE_INPUT`.

The monetary exposure section therefore remains explicitly unavailable:

- `available = false`;
- `total_stake = null`;
- `bankroll_fraction = null`;
- `portfolio_var = null`.

## Correlation boundary

Two separate unknowns are kept explicit:

- same-fixture covariance model: unavailable;
- cross-fixture covariance model: unavailable.

Same-fixture signals are therefore clustered and marked
`UNKNOWN_NOT_INDEPENDENT`.

Cross-fixture positions are not claimed to be independent; v1 merely lacks a
validated covariance model and does not manufacture one from shared teams,
league, probability or EV.

## Statuses

### `NO_ACTIONABLE_EXPOSURE`

No explicit actionable `bet` positions exist and there are no malformed betting
states.

### `BLOCKED_STRUCTURAL_RISK`

At least one portfolio safety violation exists, for example duplicate positions,
multiple positions on the same fixture, conflicting selections, unsupported bet
status, malformed bet payload or unapproved staking input.

### `UNSIZED_ACTIONABLE_PORTFOLIO`

Explicit actionable selections exist and pass the structural checks, but no
stake/bankroll sizing exists. This does **not** mean the positions should be
placed; it only means the structural portfolio representation is valid.

## Relationship to Product Decision Framework

Portfolio/Risk v1 cannot change:

- main forecast;
- value signal;
- decision tier;
- model probability;
- model promotion state.

It also cannot create a bet from a forecast or from positive EV.

A later betting/recommendation framework must explicitly produce the actionable
selection first. Risk validation comes after that decision, not before.

## Read-only API

`GET /portfolio-risk-view`

The endpoint reuses the same live `product-market-view` payload and runs only the
pure structural risk layer over it. It performs no extra Supabase writes, model
inference, Odds API calls or model promotion.

The response includes:

- schema/version and policy;
- signal inventory;
- same-fixture signal clusters;
- actionable positions;
- structural violations;
- descriptive team/league concentration;
- monetary exposure unavailable state;
- explicit automatic-effect prohibitions.
