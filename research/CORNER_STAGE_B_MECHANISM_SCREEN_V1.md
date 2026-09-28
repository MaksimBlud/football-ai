# CORNER_STAGE_B_MECHANISM_SCREEN_V1

Status: **COMPLETED FEASIBILITY / METHOD SCREEN / NO DIRECTION TEST**

## Purpose

Screen a small set of genuinely different Stage-B mechanisms for the two-stage
corner-market direction idea:

- Stage A: use the already replicated FAIR_CENTRE repricing-risk signal to identify
  fixtures more likely to move;
- Stage B: only inside likely movers, use information independent of the current
  scalar CORNERS10/opening-lambda mechanism to estimate direction.

This block is feasibility/method selection only. It does not read new provider odds,
does not fit a direction model on V2B outcomes, and is not confirmation evidence.

## Binding constraints

- Do not retune the existing CORNERS10 scalar formula on the opened 31-fixture subset.
- Do not lower V2B thresholds or exclude leagues after seeing results.
- Do not reuse SHOTS10 by searching new windows/subsets on the already-seen HS/AS/HST/AST
  family; that family is already closed for same-sample retuning.
- No paid provider calls.
- Point-in-time features must use only matches strictly before the target fixture.
- Any V2B use from here is hypothesis generation only; confirmation requires a new unseen cohort.

## Candidates screened

### 1. RESULT_STRENGTH_TRAJECTORY_5 — selected feasibility winner

Source:
- prior completed top-flight results;
- existing leakage-safe Elo / five-match trajectory implementation in
  `historical_team_strength_trajectory.py`.

Why it is genuinely different:
- uses result/Elo state rather than corner counts;
- uses no opening corner line or FAIR_CENTRE in the Stage-B feature construction;
- therefore it is not another algebraic rewrite of `football_gap`.

Existing project evidence:
- `TEAM_STRENGTH_TRAJECTORY_V1` is the strongest retained football-only signal from
  the historical signal-discovery block;
- it did not establish incremental superiority over the 1X2 market, so that prior result
  must not be misrepresented as a corner-direction edge.

Point-in-time feasibility on the frozen V2B 43:
- the existing CORNERS10 feasibility artifact already records each target team's count of
  prior top-flight matches;
- 31/43 fixtures have >=10 prior matches for both teams;
- three additional La Liga fixtures have promoted/returning teams with 6 prior top-flight
  matches and therefore pass a five-match trajectory requirement;
- the remaining nine fixtures contain at least one team with only 3-4 prior top-flight matches.

Therefore a strict five-prior-match result/Elo trajectory state is reconstructable for:

**34 / 43 V2B fixtures**

This 34-fixture coverage statement is a feasibility result only, not a direction result.

### 2. CORNER_TREND_5V5 — not selected

Concept:
- compare recent corner state (last five) with the preceding five matches to represent
  acceleration/deceleration rather than the CORNERS10 level.

Availability:
- zero-cost and point-in-time for the same 31/43 fixtures already eligible for CORNERS10.

Reason not selected:
- it uses the same underlying corner-history information as the failed scalar
  CORNERS10 direction mechanism;
- on an already-opened cohort this is too close to post-hoc feature engineering of the
  same signal family and does not satisfy the preferred independent-information criterion.

### 3. SHOT_QUALITY_TREND — not selected

Concept:
- use prior shots / shots-on-target state or trend as a football-pressure direction signal.

Availability:
- Football-Data historical sources contain HS/AS/HST/AST for the established historical
  SHOTS10/shot-quality workflows.

Reason not selected:
- the exact SHOTS10 / shot-quality family has already been tested and formally closed for
  same-sample retuning;
- project closure explicitly says not to search alternative rolling windows, SOT-only
  subsets, league subsets, or another transformation of the same HS/AS/HST/AST evidence
  and present it as new confirmation.

A future reopening needs genuinely richer information such as timestamp-safe true xG or
shot-location quality, not another transform of the same shot-count family.

### 4. CROSS_MARKET_H2H_LEAD — conceptually useful, current V2B data gap

Concept:
- use independent movement/disagreement from another market (for example 1X2 fair
  probabilities) before the corner close as a directional lead.

Read-only live-data audit on 2026-09-28:
- `league_h2h_bookmaker_snapshots`: no stored rows returned;
- `league_multi_market_snapshots`: only 2 rows, both EREDIVISIE;
- top-five `odds_snapshots` coverage ends on 2026-09-11;
- V2B frozen future cutoff is 2026-09-19.

Therefore this mechanism cannot be reconstructed for the frozen V2B cohort from existing
durable top-five snapshots. New provider capture could make it feasible prospectively,
but that would be a separate acquisition decision and may incur provider cost.

## Selection

Selected next Stage-B source family:

**RESULT_STRENGTH_TRAJECTORY_5**

Selection rationale:
1. genuinely different raw information from CORNERS10/opening-lambda;
2. strict pre-match reconstruction is possible from free completed-match history;
3. exact V2B feasibility is materially better than CORNERS10: 34/43 vs 31/43;
4. a leakage-safe implementation already exists in the repository;
5. it avoids reopening a formally closed SHOTS10 family or requiring new paid acquisition.

## Important limitation

This screen does **not** yet define or validate a final UP/DOWN rule.

The existing trajectory research was built for 1X2 prediction. A corner-total direction
mapping must be separately specified before it is evaluated. It is not valid to inspect
V2B direction rows and then search arbitrary sums/differences, thresholds, league subsets,
or signs until something works.

## Recommended next bounded block

Create a zero-cost V2B trajectory reconstruction/preregistration block that:

1. freezes the exact 34-fixture eligibility rule (>=5 prior top-flight matches for both teams);
2. reconstructs the existing pre-match Elo level, Elo delta-5 and performance-residual-5
   components without reading V2B odds;
3. freezes one small, interpretable Stage-B mapping before opening any new row-level
   direction comparison;
4. treats any V2B evaluation as hypothesis generation only;
5. requires a new unseen cohort for confirmation.

## Safety

- research-only;
- NO_BET;
- no Odds API request;
- no Supabase write;
- no model training/promotion;
- no production `.pkl` modification;
- no V2B threshold change;
- no claim of predictive direction accuracy.
