# CROSS_MARKET_LEAD_LAG_V1

Status: **PREREGISTERED HISTORICAL OPEN→CLOSE LEAD-LAG PROXY / RESEARCH-ONLY / NO_BET**.

## Motivation

The next research direction is temporal market information rather than another static
transformation of one price vector.

The ideal test would use timestamped intraday snapshots for 1X2, Asian Handicap and goals
totals. A live source audit on 2026-10-04 shows that
`public.league_multi_market_snapshots` currently contains only:

- 2 rows;
- 2 unique events;
- both in Eredivisie;
- exactly one multi-market snapshot per event;
- provider keys only `spreads` and `totals`.

That is not enough to estimate true intraday lead-lag and must not be treated as if it were.

V1 therefore uses a cheaper historical **open→close proxy** available in the pinned
Football-Data source.

## Research question

At Bet365 market opening, O/U 2.5 + Asian Handicap imply an independent synthetic 1X2
distribution.

Does the later Bet365 **closing 1X2** move in the direction implied by that opening
cross-market discrepancy?

In symbols:

`opening O/U + AH -> synthetic opening 1X2`

versus

`actual opening 1X2 -> actual closing 1X2`.

If the opening synthetic residual predicts the later 1X2 move, that is evidence that the
non-1X2 markets contain information that is incorporated into 1X2 later.

This is a lead-lag proxy, not proof of the exact intraday ordering of individual quote
changes.

## Frozen source

Leagues:

- EPL;
- La Liga;
- Serie A.

Seasons:

- reference/train: 2019/20 through 2023/24;
- validation: 2024/25;
- untouched OOT: 2025/26.

No 2026/27 data are permitted.

Historical transport reuses the already-proven pinned Football-Data mirror fallback.

No paid Odds API request and no Supabase write is allowed.

## Same-bookmaker opening inputs

All opening signals must come from Bet365:

### Opening 1X2

- `B365H`
- `B365D`
- `B365A`

### Opening O/U 2.5

- `B365>2.5`
- `B365<2.5`

### Opening Asian Handicap

- line: first finite value from `AHh`, then `B365AH`;
- `B365AHH`;
- `B365AHA`.

As in CROSS_MARKET_SCORE_COHERENCE_V1, the primary reconstruction uses exact half-goal
handicap lines only. Integer and quarter lines are excluded.

## Closing target

Closing 1X2 uses Bet365 only:

- `B365CH`
- `B365CD`
- `B365CA`.

Both opening and closing 1X2 are multiplicative no-vig normalized.

No match result is used anywhere in V1.

Outcome columns may exist in the source CSV because Football-Data distributes one combined
file, but the V1 code must not read, join, score or branch on FTR/FTHG/FTAG or any other
match-result field.

## Opening synthetic score model

Reuse the frozen structural reconstruction from CROSS_MARKET_SCORE_COHERENCE_V1:

1. infer total goal intensity `mu` from opening Bet365 O/U 2.5;
2. infer home goal share from opening Bet365 half-goal AH;
3. derive `lambda_home` and `lambda_away`;
4. convert the Poisson/Skellam score model into synthetic HOME/DRAW/AWAY probabilities.

No fitted outcome parameters are introduced.

## Lead and future-move vectors

Let:

- `p_open` = opening Bet365 no-vig 1X2;
- `p_score_open` = opening synthetic 1X2 from O/U+AH;
- `p_close` = closing Bet365 no-vig 1X2.

Define the opening lead vector:

`lead = p_score_open - p_open`.

Define the later 1X2 move:

`move = p_close - p_open`.

The primary per-match statistic is:

`alignment_dot = dot(lead, move)`.

Interpretation:

- positive -> closing 1X2 moved in the direction suggested by opening O/U+AH;
- negative -> closing 1X2 moved against that opening cross-market signal;
- zero -> no directional alignment.

The dot product naturally downweights tiny opening discrepancies.

## Primary null

A positive raw mean is not enough, because all markets may share broad league/season drift.

The primary null is therefore **within-league-season permutation**:

- keep each match's opening→closing 1X2 move fixed;
- randomly permute opening lead vectors among matches within the same league-season;
- recompute pooled mean alignment;
- repeat 10,000 times.

This destroys match-specific O/U/AH -> later-1X2 linkage while preserving:

- league;
- season;
- lead-vector distribution;
- closing-movement distribution.

Primary one-sided p-value:

fraction of permuted pooled means >= observed pooled mean.

Permutation seed: **20261004**.

## Supporting diagnostics

Report without changing the decision:

- mean and median `alignment_dot`;
- fraction of matches with positive alignment;
- opening score-gap TV;
- TV distance from opening synthetic 1X2 to opening real 1X2;
- TV distance from opening synthetic 1X2 to closing real 1X2;
- `gap_reduction_tv = gap_open_tv - gap_close_to_open_score_tv`;
- mean opening→closing 1X2 TV movement;
- HOME/DRAW/AWAY component correlations:
  `lead_component` vs `future_move_component`;
- by-league results;
- reconstruction residuals;
- source coverage by league/season.

## Validation gate — 2024/25

The signal is validation-admissible only if all are true:

1. pooled mean `alignment_dot > 0`;
2. at least 2 of 3 leagues have positive mean alignment;
3. one-sided within-league permutation p-value < 0.05;
4. every league has at least 40 eligible validation rows.

No sign, subset, line restriction or metric may change after validation.

## Final untouched OOT gate — 2025/26

`OPEN_CROSS_MARKET_LEADS_CLOSE_1X2_SUPPORTED` only if validation passes and all OOT
conditions also hold:

1. pooled mean `alignment_dot > 0`;
2. at least 2 of 3 leagues have positive mean alignment;
3. every league has at least 40 eligible OOT rows;
4. one-sided within-league permutation p-value < 0.05;
5. a stratified-by-league bootstrap with 10,000 draws has a 95% CI for mean
   `alignment_dot` entirely above zero.

Bootstrap seed: **20261004**.

Otherwise:

`NO_OPEN_TO_CLOSE_CROSS_MARKET_LEAD_SIGNAL`.

Validation failure cannot be rescued by OOT.

## Interpretation boundary

A positive result means only:

> opening Bet365 O/U+AH contain match-specific information associated with the direction of
> the later Bet365 1X2 move.

It does not establish:

- the exact hour/minute at which AH moved first;
- profitability;
- that AH itself rather than totals carries the information;
- that a live implementation can trade the signal;
- production promotion.

A positive V1 would justify a separate finer timestamped prospective collector.

A negative V1 would mean there is no reason to spend paid provider credits building that
collector for this hypothesis.

## Safety

- research-only;
- NO_BET;
- no result scoring;
- no 2026/27 access;
- zero paid Odds API calls;
- no Supabase writes;
- no production model operations;
- no production `.pkl` changes;
- no automatic promotion.
