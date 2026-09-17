# FREE_CORNERS_SIGNAL_SCREEN_V1

## Purpose

Run a no-paid-subscription screen for whether leakage-safe football corner state contains incremental information beyond Bet365 opening corner-total prices on the currently available free window.

This is a separate exploratory screen. It does not alter or replace the already-frozen multi-season `CORNERS10_BET365_MARKET_V1` contract.

## Free-only boundary

Provider market source: 5DollarFootballAPI Free plan only.

- no subscription purchase;
- no plan upgrade;
- no `include=odds` bulk expansion;
- hard provider budget: 60 requests for the live screen;
- exactly 5 league-list requests plus at most 55 per-fixture corner-odds requests;
- no retries that exceed the hard budget;
- no The Odds API spend.

Football-state source: Football-Data CSV files, which are free public historical match-stat files.

## Frozen leagues

- EPL — provider league id `4160026622`, Football-Data code `E0`;
- La Liga — `4212821298`, `SP1`;
- Serie A — `3405541143`, `I1`;
- Bundesliga — `686337048`, `D1`;
- Ligue 1 — `3614399544`, `F1`.

## Frozen time split

Football model training data: 2016-17 through 2025-26 only.

Market screen: 2026-27 only, using the most recent finished fixtures available to the Free plan at acquisition time.

No 2026-27 row may enter model fitting.

## Frozen market sample

For each league, request finished fixtures ordered newest first and deterministically select the first 11 unique fixture ids. Selection occurs before reading the fixture's corner odds or final corner outcome.

Then request `GET /v1/fixtures/{id}/odds?market=corner` for those selected fixture ids.

Maximum selected fixtures: 55.

The league-list fixture payload may be retained for identity/date/outcome audit, but no fixture is selected or dropped because of its realized corner result.

## Reconciliation

Each selected provider fixture must reconcile uniquely to the 2026-27 Football-Data row using:

- league;
- kickoff calendar date, allowing at most +/- 1 day for timezone/source date convention;
- canonical home team;
- canonical away team.

No fuzzy many-to-one matching is allowed. Ambiguous rows are rejected.

Provider final corner totals may be used as an audit cross-check against Football-Data `HC + AC`; a disagreement rejects the row.

## Football-state construction

Use continuous point-in-time rolling histories across season boundaries, so returning top-flight teams enter 2026-27 with prior-season history.

A test row is eligible only if both teams have at least 10 prior top-flight matches in the continuous history.

Frozen corner-state features:

- `home_corners_for_10`
- `home_corners_against_10`
- `away_corners_for_10`
- `away_corners_against_10`
- `home_corners_for_venue5`
- `home_corners_against_venue5`
- `away_corners_for_venue5`
- `away_corners_against_venue5`

No goals, cards, final score, same-match corners, closing odds or in-play data enter the football model.

## Frozen football model

Fit one independent model per league on 2016-17 through 2025-26.

Pipeline:

1. `SimpleImputer(strategy="median")`
2. `StandardScaler()`
3. `PoissonRegressor(alpha=0.1, max_iter=2000)`

Target: `HC + AC` total corners.

No hyperparameter search, league-specific tuning or post-screen refit is allowed.

## Opening market eligibility

Use Bet365 full-time corner opening prices only.

Require:

- finite opening line;
- finite opening Over and Under decimal odds, both > 1;
- opening line fractional part is either `.0` or `.5`;
- unique reconciled finished fixture;
- both teams have at least 10 prior top-flight matches.

Quarter lines are excluded before outcome scoring.

For half-lines, score the binary Over event directly.

For integer lines, a realized exact-line push is settlement-neutral and is excluded from conditional Over/Under proper-score metrics. Model and market probabilities are both interpreted conditional on non-push for integer lines.

## Market probability

De-vig opening prices:

`p_market = (1/opening_over) / ((1/opening_over) + (1/opening_under))`.

## Football probability

Let the fitted Poisson mean be `lambda`.

For half line `L = k + 0.5`:

`p_football = P(X >= k+1 | lambda)`.

For integer line `L = k`:

`p_football = P(X > k) / (P(X > k) + P(X < k))`.

## Fixed incremental screen

No market-history fitting is permitted.

Define a fixed conservative blend before seeing screen results:

`p_blend25 = 0.75 * p_market + 0.25 * p_football`.

Primary proper scores on identical eligible rows:

- Brier score;
- binary LogLoss.

Primary incremental diagnostic:

`residual_alignment = mean((y - p_market) * (p_football - p_market))`.

Positive values mean the football model tends to deviate from the market in the direction later supported by the result.

Also report per-league residual alignment and a row bootstrap 90% interval for the pooled statistic using fixed seed `20260917` and 10,000 resamples.

## Sample gate

The screen is interpretable only with at least 40 non-push eligible rows pooled across the five leagues and at least 5 eligible rows in at least 4 leagues.

If this gate fails, verdict is `SAMPLE_TOO_SMALL`.

## Frozen verdict

`STRONG_SIGNAL_SCREEN` only if all are true:

- sample gate passes;
- `p_blend25` has lower pooled Brier than `p_market`;
- `p_blend25` has lower pooled LogLoss than `p_market`;
- pooled `residual_alignment > 0`;
- at least 3 leagues have positive residual alignment;
- the 90% bootstrap lower bound for pooled residual alignment is > 0.

`INDICATIVE_SIGNAL_SCREEN` if the sample gate passes and all conditions above hold except the bootstrap lower bound may cross zero.

Otherwise verdict is `NO_CLEAR_SIGNAL_SCREEN`.

This screen can detect a strong free-window signal. `NO_CLEAR_SIGNAL_SCREEN` does not prove that a small 1-2% edge is absent; the free OOT sample is too small for that stronger claim.

## Safety

- research-only;
- `NO_BET`;
- no ROI/staking thresholds;
- no production `.pkl` changes;
- no production model promotion;
- no Supabase writes;
- no paid subscription;
- no post-result feature or threshold tuning inside V1.
