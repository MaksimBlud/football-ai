# CORNERS10_BET365_MARKET_V1

## Purpose

Test whether leakage-safe pre-match corner-state information adds predictive value beyond the **Bet365 opening full-time corner-total market**.

This is a research-only preregistration. It is frozen before any multi-season 5DollarFootballAPI backfill is opened or any aggregate model-vs-market metric is computed.

The experiment does **not** assume that the historical `CORNERS10` 1X2 classifier is itself a corner-total model. The prior research established that rolling corner state was a useful football-state signal for 1X2. This V1 derives a target-appropriate `CORNERS10_TOTAL` feature block from the same leakage-safe rolling histories and tests it directly against the bookmaker corner market.

## Source boundary

### Bookmaker market

Primary source: 5DollarFootballAPI.

Use Bet365 full-time corner market snapshots only:

- `opening.line`;
- `opening.over`;
- `opening.under`;
- `closing.*` may be retained for diagnostics only and must never enter the primary candidate features or validation/OOT selection logic.

The already-completed source pilot qualified this feed on EPL, La Liga and Serie A. This contract does not authorize any subscription purchase. A historical backfill may run only after the account tier legally exposes the frozen historical window.

### Football state and outcomes

Use the existing Football-Data historical league files and the repository's `historical_football_signal_lab.build_point_in_time_features` logic for point-in-time rolling team state.

Final corner outcome is `HC + AC` from the matched Football-Data fixture.

No same-match `HC`, `AC`, final score, cards, in-play event, closing price, or other post-kickoff information may enter the candidate features.

## Frozen leagues

- `EPL`
- `LA_LIGA`
- `SERIE_A`

No other league may be added to V1 after evaluation begins.

## Frozen seasons

- training: `2016-17` through `2023-24`;
- validation: `2024-25`;
- final untouched OOT: `2025-26`;
- `2026-27` is forbidden.

The OOT season must remain unopened for aggregate target/model metrics until the validation decision is fixed by code.

## Fixture reconciliation

A provider market row may join a Football-Data fixture only when all of the following are true:

- same frozen league;
- same season;
- canonical home team matches;
- canonical away team matches;
- kickoff calendar date matches, or there is exactly one otherwise-identical fixture within +/- 1 calendar day;
- the match is unique after reconciliation.

Ambiguous matches are rejected. A provider row must never be joined by row order or approximate team similarity alone.

## Eligible market rows

V1 deliberately uses only clean binary Asian-total cases.

A row is eligible only when:

- fixture is finished and reconciled uniquely;
- Bet365 opening corner line is finite and is exactly a half line (`x.5` within numerical tolerance);
- Bet365 opening Over odds are finite and > 1.0;
- Bet365 opening Under odds are finite and > 1.0;
- Football-Data `HC` and `AC` are finite;
- the fixture belongs to one of the frozen seasons.

Integer and quarter corner lines are excluded from V1. They may be studied only under a later separately frozen settlement contract.

## Target

For the frozen Bet365 opening line:

`y_over = 1` when `HC + AC > opening_line`, otherwise `0`.

Because V1 admits only half lines, pushes cannot occur.

## Market baseline

De-vig the same-row Bet365 opening prices:

- `q_over = 1 / opening_over`
- `q_under = 1 / opening_under`
- `p_market_over = q_over / (q_over + q_under)`

The market baseline prediction for every eligible fixture is `p_market_over`.

No closing price is substituted when an opening price is absent.

## Frozen candidate feature set

The candidate is `MARKET_CORNERS10_TOTAL`.

Market fields:

- `market_logit` = logit of de-vigged Bet365 opening Over probability;
- `opening_line`.

Leakage-safe rolling corner-state fields, all computed **before** the current match by the existing point-in-time builder:

- `home_corners_for_10`
- `home_corners_against_10`
- `away_corners_for_10`
- `away_corners_against_10`
- `home_corners_for_venue5`
- `home_corners_against_venue5`
- `away_corners_for_venue5`
- `away_corners_against_venue5`

No feature search, window search, alternate football feature set, interaction search, line bucket search, or league-specific feature selection is allowed in V1.

This feature block is intentionally symmetric because the target is a **match total**, unlike the prior 1X2 `CORNERS10` research which used home-minus-away differences.

## Frozen estimator

Per league:

1. `SimpleImputer(strategy="median")`
2. `StandardScaler()`
3. `LogisticRegression(C=0.1, max_iter=2000)`

No hyperparameter search and no refit using OOT labels.

## Data sufficiency gate

Before predictive metrics are used for a league, require:

- at least 600 eligible training fixtures;
- at least 100 eligible validation fixtures;
- at least 100 eligible OOT fixtures.

If a league fails this gate, its status is `DATA_INSUFFICIENT`; it cannot PASS and must not trigger threshold relaxation or broader line inclusion inside V1.

## Primary metrics

On paired identical eligible rows:

- Brier score;
- binary LogLoss.

Lower is better.

Accuracy and sample prevalence may be reported as diagnostics only. ROI, profit, staking and betting thresholds are forbidden in V1.

## Validation gate

For a data-sufficient league, the candidate is `VALIDATION_ADMISSIBLE` only when it beats the Bet365 opening baseline on **both**:

- validation Brier;
- validation LogLoss.

If either metric is not strictly better, the candidate is validation-inadmissible and the final active OOT prediction for that league is the market baseline.

No rule may be changed after validation is seen.

## Final OOT decision

A league is `PASS` only when:

- it is data-sufficient;
- it is validation-admissible;
- on untouched `2025-26` OOT it beats Bet365 opening probability on both Brier and LogLoss.

Otherwise it is `FAIL`, `MARKET_FALLBACK`, or `DATA_INSUFFICIENT` as applicable.

Raw candidate OOT metrics may be retained for audit, but an inadmissible candidate is not treated as active evidence.

## Cross-league decision

Overall decision is `PILOT` only when both conditions hold:

1. at least 2 of 3 leagues are `PASS`;
2. pooled validation-selected OOT predictions beat the pooled Bet365 opening baseline on both Brier and LogLoss.

Otherwise overall decision is `SKIP`.

No league weighting or threshold may be tuned after OOT is opened.

## Closing-market diagnostics

Bet365 closing line/prices, when present, may be used only after the primary result is fixed for descriptive diagnostics such as line movement coverage.

Closing information must not:

- enter candidate features;
- choose samples beyond the opening-row eligibility rules;
- choose model parameters;
- determine PASS/SKIP in V1.

Any CLV or opening-to-closing forecasting experiment requires a separate preregistration.

## Acquisition contract

Historical provider data must be downloaded once and persisted raw before evaluation. Finished historical responses should be cached and reused rather than repeatedly requested.

The acquisition layer must:

- use official 5DollarFootballAPI endpoints only;
- keep raw provider payloads separate from normalized research rows;
- never log or persist `FIVE_DOLLAR_FOOTBALL_API_KEY`;
- fail closed when the account plan does not expose the requested historical window;
- never silently shorten the requested seasons to the available plan window;
- record coverage before model evaluation.

A plan upgrade or subscription purchase is outside this contract and requires explicit user action.

## Safety and interpretation

- research-only;
- `NO_BET`;
- no production `.pkl` changes;
- no production model promotion;
- no Supabase writes;
- no The Odds API spend;
- no 2026-27 data;
- no automatic subscription purchase;
- no post-OOT retuning of V1.

A `PASS` would mean the fixed corner-state augmentation improved probabilistic prediction of the Bet365 **opening half-line** outcome on the frozen historical test. It would not by itself prove profitability, execution feasibility, or a production betting strategy.

A `SKIP` closes this specific V1 augmentation without implying that all corner-market research is useless.
