# V2B RESULT STRENGTH TRAJECTORY FREEZE V1

Status: **PREREGISTERED / FEATURE-FREEZE ONLY / NO DIRECTION TEST**

## Research question

Can a result/Elo state that is independent of CORNERS10 and the corner opening
market provide a useful Stage-B sign hypothesis inside a future two-stage
corner-market direction structure?

This block freezes the feature cohort and one deterministic mapping only.
It does not evaluate direction.

## Immutable upstream inputs

V2B cohort lock:

- artifact ID: `10899325930`;
- artifact digest: `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures: 43.

V2B CORNERS10 replay-feasibility artifact:

- artifact ID: `10900784704`;
- artifact digest: `sha256:66c83b96f8c1143397aca660701d0a7f5950c3b59a1bd0158bbefe6501d7ecfb`;
- fixture identity matched: 43/43.

The feasibility artifact is reused only for immutable point-in-time prior-match
counts and fixture identity. Corner counts themselves are not Stage-B inputs.

## Frozen eligibility rule

A fixture is eligible iff:

1. it is one of the exact 43 locked V2B fixtures;
2. its source identity is `MATCHED` in the immutable feasibility artifact;
3. both teams have at least **5** prior recent top-flight matches in that artifact.

Expected frozen eligible cohort:

**34 / 43**

By league:

- EPL: 6/9;
- La Liga: 9/9;
- Serie A: 7/9;
- Bundesliga: 6/8;
- Ligue 1: 6/8.

No ineligible fixture may be replaced or backfilled.

## Point-in-time result/Elo source

Use public Football-Data top-flight result history configured in the repository:

- historical seasons 2016/17 through 2025/26;
- current 2026/27 finished rows;
- only `Date`, `HomeTeam`, `AwayTeam`, `FTR` are required for this mechanism.

Team identity follows the existing V2B source-normalization plumbing.

The existing leakage-safe implementation
`historical_team_strength_trajectory.add_team_strength_trajectory` is reused:

- initial Elo = 1500;
- K = 20;
- home advantage = 65;
- feature snapshot occurs before the target fixture result updates state.

Required frozen components per team:

- `elo_level`;
- `elo_delta_5`;
- `performance_residual_5`.

## Frozen primary Stage-B mapping

Mapping ID:

`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1`

Formula:

`stage_b_score = home_performance_residual_5 + away_performance_residual_5`

Decision:

- score > 0 -> `UP`;
- score < 0 -> `DOWN`;
- score == 0 -> `NO_CALL`.

Interpretation:

the score represents joint recent match-performance relative to Elo expectation.
For a total market, a joint two-team state is preferred over the home-away
difference used by 1X2 research.

There are:

- no fitted weights;
- no learned threshold;
- no league-specific sign;
- no subset search;
- no use of opening corner line;
- no use of FAIR_CENTRE;
- no use of `centre_delta`.

The other trajectory components are frozen in the artifact for auditability but
are not allowed to replace the primary mapping after direction is opened.

## Separation from Stage A

Stage A remains the separately replicated FAIR_CENTRE repricing-risk concept.

This V1 freeze does **not** yet combine Stage A and Stage B and does not choose a
Stage-A risk threshold. The purpose here is only to freeze Stage-B football-state
features and sign before any new direction comparison.

## Allowed output in this block

The feature-freeze artifact may contain:

- exact eligible fixture identities;
- eligibility counts;
- point-in-time Elo/trajectory components;
- the frozen Stage-B score and call;
- deterministic cohort hash;
- source provenance and safety flags.

It must not contain:

- opening corner prices;
- closing corner prices;
- FAIR_CENTRE;
- opening lambda;
- `centre_delta`;
- observed UP/DOWN market direction;
- concordance;
- p-values;
- betting returns.

## Evidence status

Any later V2B evaluation remains **opened-sample hypothesis generation**.

Even if this frozen mapping looks promising on V2B, confirmation requires a new
unseen market cohort frozen before its direction outcomes are opened.

## Safety

- research-only;
- `NO_BET`;
- zero Odds API calls;
- no Supabase write;
- no production model training/promotion;
- no production `.pkl` modification;
- no V2B threshold weakening;
- no direction accuracy claim in this block.
