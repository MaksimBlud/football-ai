# V2B DEEP STAGE-B FREEZE V1

Status: **PREREGISTERED FEATURE FREEZE / NO DIRECTION TEST**

## Purpose

Freeze one simple territorial-pressure Stage-B hypothesis for the exact 34-fixture
cohort that passed the Understat tactical-pressure feasibility audit.

No market direction is read in this block.

## Immutable upstream source

Feasibility artifact:

- ID `10981596648`;
- digest `sha256:e686e483e375b59484bb493904870f8942e1df70d4553ad5928596476d9054c5`;
- identity matched = 43/43;
- tactical5 feasible = 34/43.

Eligibility remains unchanged. No lower-division backfill or fixture replacement.

## Primary feature choice

Use only:

- deep last5;
- deep_allowed last5.

PPDA and PPDA_allowed are **not** used in this primary mapping.

Reason: PPDA is inverse-oriented and lives on a different scale. Combining it with
absolute deep counts without an independently frozen normalization would introduce
unnecessary degrees of freedom. PPDA remains source-feasible but may not be substituted
after V2B direction is opened.

## Frozen baseline

Use one pooled completed-2025/26 top-five Understat baseline.

For each valid team-match row:

`total_deep_environment = deep + deep_allowed`

Pool all valid 2025/26 team-match rows from EPL, La Liga, Serie A, Bundesliga and Ligue 1
and compute one row-weighted mean.

No league-specific baseline.

## Frozen mapping

Mapping ID:

`POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`

`expected_home_deep = 0.5 * (home_deep_last5 + away_deep_allowed_last5)`

`expected_away_deep = 0.5 * (away_deep_last5 + home_deep_allowed_last5)`

`joint_expected_deep = expected_home_deep + expected_away_deep`

`stage_b_score = joint_expected_deep - pooled_2025_26_top5_deep_baseline`

- score > 0 -> UP;
- score < 0 -> DOWN;
- score == 0 -> NO_CALL.

No fitted weight, learned threshold, league-specific sign, opening-line input or
FAIR_CENTRE input is allowed.

## After freeze

A later evaluator may only test this exact score/call against the already-opened V2B
centre_delta. It may not switch to PPDA, rebalance calls, move the baseline or select
leagues after seeing outcomes.

Any V2B result remains hypothesis generation; confirmation requires unseen data.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no production model changes.
