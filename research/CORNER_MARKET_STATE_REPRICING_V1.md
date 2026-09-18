# CORNER_MARKET_STATE_REPRICING_V1

Status: **PREREGISTERED / MARKET-ONLY / FREE-DATA**

## Purpose

This experiment restores the intended research sequence used after the 1X2 market-state work.

It does **not** ask whether a football model predicts corner totals better than Bet365. It asks the same market-discovery question as the successful 1X2 repricing-risk track:

> Does the current bookmaker corner-market state contain information about whether that market will be materially repriced by closing?

Match outcomes, realised corner counts, CORNERS10, team-form features and football-state models are forbidden inputs and are not required for the target.

The previously merged `FREE_CORNERS_SIGNAL_SCREEN_V1` and `SERIE_A_CORNERS_PROSPECTIVE_V1` answer a different football-model-vs-market question. They are retained as historical research records but are **not** the continuation of the 1X2 -> handicap -> totals -> corners market-state sequence.

## Frozen source

Primary replay source is the already acquired free Bet365 corner-market data:

- 5Dollar source pilot artifact `10503575942`;
- free corners screen artifact `10506736726`;
- union by `fixture_id`, with the newer raw response taking precedence only when the payload is structurally complete;
- no new paid request;
- no match outcome columns are read.

Eligible row requires Bet365 full-time `corner_line` with finite, >1.0 opening and closing Over/Under prices and an opening/closing line that is an integer or half-integer.

## Comparable corner-market centre

Unlike 1X2, a corner market may change both its line and its prices. Therefore opening and closing are mapped to one comparable latent market centre, `lambda`, using a fixed Poisson reconstruction.

For each market state:

1. de-vig the two quoted prices proportionally:
   `p_over = (1/over) / ((1/over) + (1/under))`;
2. for a half-line `L + 0.5`, solve the Poisson mean `lambda` such that
   `P(X >= L+1) = p_over`;
3. for an integer line `L`, solve `lambda` such that
   `P(X > L) / (P(X > L) + P(X < L)) = p_over`,
   which removes the push mass from the two-way comparison;
4. numerical solve interval is fixed to `[1.0, 25.0]`.

Quarter-lines or malformed rows are excluded rather than approximated.

Primary continuous movement:

`centre_delta = closing_lambda - opening_lambda`

Primary movement magnitude:

`movement_magnitude = abs(centre_delta)`

Direction `sign(centre_delta)` is diagnostic only, exactly as direction was not promoted in the 1X2 work unless independently robust.

## Frozen opening-state feature variants

No football features are allowed. Candidate feature families are fixed before aggregate feature-target metrics are opened:

- `FULL_STATE`: `opening_line`, `opening_over_prob`;
- `OVER_LEVEL`: `opening_over_prob`;
- `ENTROPY`: binary entropy of the de-vigged opening Over/Under probabilities;
- `LINE_LEVEL`: `opening_line`;
- `PRICE_IMBALANCE`: `abs(opening_over_prob - 0.5)`;
- `FAIR_CENTRE`: reconstructed `opening_lambda`.

These are the two-way corner-market analogues of the fixed, interpretable opening-market geometry tested in the 1X2 repricing track. No post-result feature search is allowed inside V1.

## Frozen target and estimator

The material-repricing label follows the 1X2 convention:

- training movement threshold = 75th percentile of `movement_magnitude`;
- target = 1 when movement magnitude is at or above that threshold;
- threshold is fitted on training rows only.

Estimator for every feature variant:

- `SimpleImputer(strategy="median")`;
- `StandardScaler`;
- `LogisticRegression(C=0.1, max_iter=2000)`.

No C search, quantile search or feature-combination search.

## Short-window validation design

The free corner sample has five leagues but no long season history. Therefore V1 uses fixed leave-one-league-out transfer:

- leagues: EPL, LA_LIGA, SERIE_A, BUNDESLIGA, LIGUE_1;
- each fold trains on four leagues and evaluates the fifth league once;
- threshold, imputer, scaler and classifier are fitted only on the four training leagues;
- the held-out league is never used to choose parameters.

For each fold and feature variant compare against a constant training-prevalence baseline using:

- Brier score;
- LogLoss;
- ROC AUC and Average Precision as diagnostics.

Primary robustness summaries:

- count of held-out leagues where candidate beats constant baseline on both Brier and LogLoss;
- pooled out-of-fold Brier and LogLoss versus the fold-specific constant baseline.

Screen interpretation:

- `STRONG_REPRICING_SIGNAL`: one fixed variant beats baseline on both pooled metrics and in at least 4/5 held-out leagues;
- `INDICATIVE_REPRICING_SIGNAL`: one fixed variant beats baseline on both pooled metrics and in 3/5 held-out leagues;
- `NO_CLEAR_REPRICING_SIGNAL`: no variant satisfies the indicative rule;
- `SAMPLE_TOO_SMALL`: fewer than 40 eligible rows or fewer than 6 eligible rows in any league.

This is a discovery screen, not betting evidence or production readiness.

## Direction diagnostic

For the best magnitude-risk variant only, report whether its high-risk predictions are associated with a stable sign of `centre_delta`.

No direction classifier is tuned in V1. A magnitude signal must not be restated as a direction signal.

## Free-only extension rule

If V1 is `NO_CLEAR_REPRICING_SIGNAL` or `SAMPLE_TOO_SMALL`, the experiment may be extended only by collecting **additional previously unseen fixtures from the provider's free historical window** under the same feature set, target construction, q=.75, C=.1 and leave-one-league-out rule.

No paid subscription is allowed. No existing V1 row may be dropped because of its result.

## Safety

- research-only;
- NO_BET;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid provider request;
- no match outcomes;
- no CORNERS10 / football-state inputs;
- production artifact hash guard required.
