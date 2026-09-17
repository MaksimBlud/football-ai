# CROSS_LEAGUE_DIRECT_MARKETS_V1

## Purpose

This is a preregistered historical temporal-OOT replication for **direct market targets**, not another 1X2 information diagnostic.

The question is whether leakage-safe pre-match football-state features add probabilistic information beyond the bookmaker market itself for:

1. full-time **Over/Under 2.5 goals**;
2. full-time **Asian Handicap home-cover** on unambiguous 0.5-step lines.

The La Liga `LA_LIGA_MULTIMARKET_ANCHOR_V5` experiment is context only: it used O/U and AH prices as features while the target remained 1X2. This V1 changes the target itself.

## Frozen scope

Leagues:

- `EPL`
- `LA_LIGA`
- `SERIE_A`

Temporal split, identical in every league:

- train: `2016-2017` through `2023-2024`;
- selection/validation: `2024-2025`;
- untouched final OOT: `2025-2026`;
- no `2026-2027` outcomes may be read.

Historical source is the existing Football-Data CSV contract already configured in the repository. No paid Odds API request and no Supabase write is allowed.

## Market extraction

### O/U 2.5

Use the first valid two-sided pair, in this frozen order:

1. `B365>2.5` / `B365<2.5`;
2. `P>2.5` / `P<2.5`;
3. `Avg>2.5` / `Avg<2.5`.

Both prices must be finite and greater than 1.0. The market baseline is the simple two-way de-vigged probability of Over 2.5.

Outcome:

- `1` if `FTHG + FTAG > 2.5`;
- `0` otherwise.

There are no pushes at 2.5.

### Asian Handicap

Use the first valid two-sided pair, in this frozen order:

1. `B365AHH` / `B365AHA`;
2. `PAHH` / `PAHA`;
3. `AvgAHH` / `AvgAHA`.

Handicap line fallback order:

1. `AHh`;
2. `B365AH`.

Both prices must be finite and greater than 1.0 and the line must be finite.

V1 includes only handicap lines that are integer or half-goal lines (`line * 2` is an integer). Quarter-lines are excluded rather than approximately settled. For integer lines, pushes are excluded from scoring. Home-cover outcome is:

- `1` if `FTHG + handicap_line > FTAG`;
- `0` if `FTHG + handicap_line < FTAG`;
- push rows are excluded.

The market baseline is the simple two-way de-vigged home-cover probability.

## Leakage-safe football state

Football-state values must be computed strictly before each match using the existing `historical_football_signal_lab.build_point_in_time_features` semantics.

No same-match goals, corners, cards, result, or later information may enter candidate features.

Fixed O/U candidate features:

- market logit;
- `home_goals_for_10`, `home_goals_against_10`;
- `away_goals_for_10`, `away_goals_against_10`;
- `home_corners_for_10`, `home_corners_against_10`;
- `away_corners_for_10`, `away_corners_against_10`;
- `home_goals_for_venue5`, `home_goals_against_venue5`;
- `away_goals_for_venue5`, `away_goals_against_venue5`;
- `home_corners_for_venue5`, `home_corners_against_venue5`;
- `away_corners_for_venue5`, `away_corners_against_venue5`.

Fixed AH candidate features:

- market logit;
- handicap line;
- `diff_points_10`;
- `diff_goals_for_10`, `diff_goals_against_10`;
- `diff_corners_for_10`, `diff_corners_against_10`;
- `diff_points_venue5`;
- `diff_goals_for_venue5`, `diff_goals_against_venue5`;
- `diff_corners_for_venue5`, `diff_corners_against_venue5`.

The AH differences use the existing `historical_football_signal_lab.add_difference_features` semantics.

## Fixed estimator

For each `(league, market)` independently:

- `SimpleImputer(strategy="median")`, fitted on training data only;
- `StandardScaler`, fitted on training data only;
- `LogisticRegression(C=0.1, max_iter=2000)`;
- no hyperparameter search;
- no threshold search;
- no feature-set search.

The candidate and bookmaker baseline must be scored on exactly the same validation/OOT rows.

## Selection and final gate

Metrics are binary Brier score and binary LogLoss. Accuracy is diagnostic only and cannot override the probabilistic gate.

For each `(league, market)`:

1. Candidate is **validation-admissible** only if it beats the bookmaker baseline on both Brier and LogLoss in `2024-2025`.
2. If validation is not admissible, final OOT active probabilities are exact bookmaker probabilities (`MARKET_FALLBACK`).
3. If validation is admissible, the unchanged fitted candidate is evaluated once on untouched `2025-2026`.
4. A league-market replication is `PASS` only if candidate beats the paired bookmaker baseline on both OOT Brier and OOT LogLoss; otherwise it is `FAIL` and active mode remains `MARKET_FALLBACK`.

No rule may be changed after OOT is opened.

Market-level decision across the three leagues:

- `PILOT` only if at least 2 of 3 leagues are `PASS` **and** the pooled paired OOT candidate beats pooled market on both Brier and LogLoss;
- otherwise `SKIP`.

This decision is research guidance only. It does not enable betting or production promotion.

## Corners market data gate

Bookmaker corners are deliberately **not** evaluated here.

Current project evidence records a provider `CAPABILITY_MISS` and zero stored bookmaker corner-line evidence. Post-match corner counts or rolling corner statistics must never be relabelled as bookmaker corner prices.

Therefore V1 must report bookmaker-corners status as:

`DATA_UNAVAILABLE`

and recommended next action as:

`COLLECT`

until a separately provenance-verified historical or prospective source provides a bookmaker corner line plus both-side prices.

Corner statistics remain allowed only as pre-match football-state features for the O/U and AH candidate models above.

## Safety / governance

- research-only;
- `NO_BET`;
- no production promotion;
- no production `.pkl` changes;
- no Supabase writes;
- no paid Odds API calls;
- no 2026-2027 outcome access;
- production `.pkl` hashes must be unchanged before/after CI execution.

The first implementation and first final-OOT run must preserve this frozen contract exactly.