# OU25_CLOSING_MOVEMENT_V1

## Purpose

Preregister an outcome-independent market-discovery test after `CROSS_LEAGUE_DIRECT_MARKETS_V1` found no stable direct O/U 2.5 augmentation over the bookmaker price.

Question: **can leakage-safe pre-match football-state predict where the fixed O/U 2.5 bookmaker probability will move from opening to closing, beyond simply assuming no movement?**

This is not a retune of the opened direct-market V1 outcome gate. The target here is the later bookmaker closing probability, not the match result.

## Frozen scope

Leagues:

- `EPL`
- `LA_LIGA`
- `SERIE_A`

Temporal split:

- train: `2016-2017` through `2023-2024`;
- validation/selection: `2024-2025`;
- final temporal OOT: `2025-2026`;
- no `2026-2027` outcomes or market observations.

Historical source is the same Football-Data CSV contract and the same SHA-verified transport fallback already merged by PR #363. No paid provider call and no Supabase write is allowed.

## Paired opening/closing extraction

A row is eligible only when one provider family has all four finite prices greater than 1.0: opening Over, opening Under, closing Over, closing Under.

Frozen provider priority:

1. Bet365:
   - opening: `B365>2.5` / `B365<2.5`;
   - closing: `B365C>2.5` / `B365C<2.5`;
2. Pinnacle:
   - opening: `P>2.5` / `P<2.5`;
   - closing: `PC>2.5` / `PC<2.5`;
3. market average:
   - opening: `Avg>2.5` / `Avg<2.5`;
   - closing: `AvgC>2.5` / `AvgC<2.5`.

Opening and closing prices must come from the **same provider family** on each row. Cross-provider opening/closing pairs are forbidden.

Both opening and closing probabilities are simple two-way de-vigged Over 2.5 probabilities.

Primary continuous target:

`closing_logit - opening_logit`

The zero-information baseline predicts exactly `0`, equivalent to predicting that closing probability equals opening probability.

## Leakage-safe candidate features

Candidate inputs are fixed before any aggregate movement metrics are opened:

- `opening_logit`;
- `home_goals_for_10`, `home_goals_against_10`;
- `away_goals_for_10`, `away_goals_against_10`;
- `home_corners_for_10`, `home_corners_against_10`;
- `away_corners_for_10`, `away_corners_against_10`;
- `home_goals_for_venue5`, `home_goals_against_venue5`;
- `away_goals_for_venue5`, `away_goals_against_venue5`;
- `home_corners_for_venue5`, `home_corners_against_venue5`;
- `away_corners_for_venue5`, `away_corners_against_venue5`.

Point-in-time football features must use the existing `historical_football_signal_lab.build_point_in_time_features` semantics. Same-match goals, corners, cards, result, closing odds, or any later information are forbidden candidate inputs.

## Fixed estimator

For each league independently:

- `SimpleImputer(strategy="median")`, train-only fit;
- `StandardScaler`, train-only fit;
- `Ridge(alpha=1.0)`;
- no feature search;
- no alpha search;
- no threshold search;
- no post-OOT refit.

The regression predicts logit movement. Predicted closing probability is:

`sigmoid(opening_logit + predicted_movement)`

and is clipped to `[1e-6, 1-1e-6]` only for numerical safety.

## Frozen metrics and gate

Primary metrics compare predicted closing probability with actual de-vigged closing probability on exactly paired rows:

1. probability RMSE;
2. probability MAE.

Baseline metrics use opening probability as the closing-probability prediction.

Movement-direction accuracy is diagnostic only. Rows with effectively zero actual movement (`abs(closing_probability-opening_probability) < 1e-9`) are excluded from direction accuracy only, not from RMSE/MAE.

For each league:

1. candidate is validation-admissible only when candidate RMSE < baseline RMSE **and** candidate MAE < baseline MAE on `2024-2025`;
2. if validation is not admissible, OOT active prediction is exact no-movement baseline;
3. if validation is admissible, the unchanged trained candidate is evaluated once on `2025-2026`;
4. league status is `PASS` only if the candidate also beats baseline on both OOT RMSE and OOT MAE; otherwise `FAIL` and final active mode is `NO_MOVEMENT_FALLBACK`.

Cross-league decision:

- `PILOT` only if at least 2 of 3 leagues are `PASS` and the pooled validation-selected OOT predictions beat pooled opening baseline on both RMSE and MAE;
- otherwise `SKIP`.

No decision may be changed after OOT movement metrics are opened.

## Interpretation boundary

A `PASS` would mean the fixed football-state construction contains information about **future market price discovery** beyond the opening price. It would not by itself prove profitable betting, superior match-outcome probabilities, or production readiness.

A `FAIL` means this construction does not justify using football-state to anticipate O/U 2.5 closing movement.

## Safety

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` modification;
- no Supabase writes;
- no paid Odds API requests;
- no 2026-27 access;
- production `.pkl` hashes must remain unchanged in CI.

The first implementation and first aggregate movement run must preserve this document exactly.