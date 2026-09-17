# FREE_CORNERS_SIGNAL_SCREEN_V1

## Purpose

Run a no-paid-subscription screen for whether leakage-safe football corner state contains incremental information beyond Bet365 opening corner-total prices on the currently available free window.

This is a separate exploratory screen. It does not alter or replace the already-frozen multi-season `CORNERS10_BET365_MARKET_V1` contract.

## Free-only boundary

Provider market/current-season source: 5DollarFootballAPI Free plan only.

- no subscription purchase;
- no plan upgrade;
- no `include=odds` bulk expansion;
- hard provider budget: 60 requests for the live screen;
- exactly 5 league-list requests plus at most 55 per-fixture corner-odds requests;
- prior source-pilot odds may be reused from its immutable GitHub Actions artifact instead of being requested again;
- no retries that exceed the hard budget;
- no The Odds API spend.

Historical football-state/training source: Football-Data CSV files, 2016-17 through 2025-26 only.

### Pre-live amendment

Before any new FREE_CORNERS_SIGNAL_SCREEN_V1 provider acquisition or aggregate metric was opened, the current 5Dollar fixture-list schema was re-checked using the already-completed source-pilot artifact. The fixture-list response already contains full-time corner counts. Therefore 2026-27 current-season rows use the 5Dollar league-list data directly rather than waiting for Football-Data's current-season CSV refresh. This removes a source-lag reconciliation problem without changing the test sample, model, features, market rule or verdict thresholds.

## Frozen leagues

- EPL — provider league id `4160026622`, Football-Data code `E0`;
- La Liga — `4212821298`, `SP1`;
- Serie A — `3405541143`, `I1`;
- Bundesliga — `686337048`, `D1`;
- Ligue 1 — `3614399544`, `F1`.

## Frozen time split

Football model training data: Football-Data 2016-17 through 2025-26 only.

Market screen/current-season rolling updates: 5Dollar 2026-27 finished fixtures only.

No 2026-27 row may enter model fitting.

## Frozen market sample

For each league, make one fixture-list request for up to 50 finished current-season fixtures. From that response, deterministically select the 11 most recent unique fixture ids by kickoff time.

Selection is based only on league, finished status, fixture id and kickoff time. It occurs before the selected fixture's Bet365 corner prices are requested and does not depend on the realized corner result.

Then request `GET /v1/fixtures/{id}/odds?market=corner` for selected fixture ids not already covered by the immutable 15-match source-pilot artifact.

Maximum selected fixtures: 55.

## Current-season identity and outcomes

The 5Dollar league-list payload is the authoritative 2026-27 fixture identity/current-season result source for this screen. It contains:

- fixture id;
- league id;
- kickoff UTC;
- home/away team names;
- finished status;
- full-time corner counts.

Historical Football-Data team names and current 5Dollar team names are canonicalized before continuous rolling histories are built. Canonicalization may use only deterministic text normalization plus an explicit alias table committed before the live screen. No fuzzy many-to-one matching is allowed.

## Football-state construction

For each league:

1. load Football-Data top-flight rows from 2016-17 through 2025-26;
2. canonicalize team names;
3. append all available finished 2026-27 5Dollar league-list rows in chronological order;
4. run the existing leakage-safe point-in-time rolling history builder continuously across the season boundary.

Returning top-flight teams therefore enter 2026-27 with prior-season history. Promoted/re-entering teams without 10 prior top-flight matches remain ineligible until the frozen history requirement is met.

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

Fit one independent model per league on 2016-17 through 2025-26 only.

Pipeline:

1. `SimpleImputer(strategy="median")`
2. `StandardScaler()`
3. `PoissonRegressor(alpha=0.1, max_iter=2000)`

Target: `HC + AC` total corners.

Training rows require both teams to have at least 10 prior top-flight matches.

No hyperparameter search, league-specific tuning or post-screen refit is allowed.

## Opening market eligibility

Use Bet365 full-time corner opening prices only.

Require:

- finite opening line;
- finite opening Over and Under decimal odds, both > 1;
- opening line fractional part is either `.0` or `.5`;
- selected finished fixture;
- finite provider full-time home/away corner counts;
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
