# V2B RESULT STRENGTH TRAJECTORY FREEZE V1 — Results

Status: **FEATURE COHORT FROZEN / NO DIRECTION TEST**

## Provenance

Workflow run:

`36434578760`

Authoritative successful feature-freeze job:

`108969276571`

Artifact:

- ID `10975465958`;
- digest `sha256:d30f4231e7e0a9149d0869ac6d775eac9d2182316593610f2b42637afc26dbe3`;
- size 5,116 bytes;
- generating head `b7c5f00a458931ff9a4264aeff4754ddad81a127`.

Upstream immutable inputs remained:

- V2B lock artifact `10899325930`, digest
  `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- V2B replay-feasibility artifact `10900784704`, digest
  `sha256:66c83b96f8c1143397aca660701d0a7f5950c3b59a1bd0158bbefe6501d7ecfb`.

## Frozen eligible cohort

Eligibility rule was applied exactly as preregistered:

- source identity = `MATCHED`;
- both teams have >=5 prior recent top-flight matches in the immutable feasibility artifact;
- no replacement or backfill.

Result:

**34 / 43 fixtures**

By league:

- EPL = 6;
- La Liga = 9;
- Serie A = 7;
- Bundesliga = 6;
- Ligue 1 = 6.

Deterministic eligible-fixture identity hash:

`sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`

## Frozen Stage-B mapping

Primary mapping remained exactly:

`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1`

`stage_b_score = home_performance_residual_5 + away_performance_residual_5`

- score > 0 -> `UP`;
- score < 0 -> `DOWN`;
- score == 0 -> `NO_CALL`.

No weights or thresholds were fitted after seeing the feature values.

Frozen call distribution:

- UP = **16**;
- DOWN = **18**;
- NO_CALL = **0**.

By league:

- EPL: 2 UP / 4 DOWN;
- La Liga: 5 UP / 4 DOWN;
- Serie A: 3 UP / 4 DOWN;
- Bundesliga: 3 UP / 3 DOWN;
- Ligue 1: 3 UP / 3 DOWN.

Observed Stage-B score range in the frozen feature artifact:

- minimum = `-0.4738804979`;
- maximum = `+0.5195856880`.

These are feature-distribution facts only. They do not contain or imply observed market direction.

## Safety proof

The successful workflow asserted:

- `direction_test_performed = false`;
- `v2b_odds_read = false`;
- `opening_lambda_read = false`;
- `centre_delta_read = false`;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.

No opening/closing corner prices or direction outcomes exist in the feature-freeze rows.

## CI note

The first PR attempt exposed a regression-test issue: a leakage test compared two
expected unavailable `NaN` fields with `pytest.approx`. This was a test defect,
not a feature/data result. The test was corrected to require matching missingness,
and the repeated regression run passed without weakening the research contract.

## Interpretation

The Stage-B feature cohort is now genuinely frozen before the next direction comparison.

This block establishes:

- exact 34-fixture membership;
- exact point-in-time Elo/trajectory values;
- exact primary Stage-B formula;
- exact UP/DOWN calls.

It establishes **no direction accuracy or edge**.

## Next permitted block

A separate evaluator may now join these exact frozen 34 fixture IDs to the already-opened
V2B market-direction artifact and evaluate only the preregistered
`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1` calls.

That evaluation must:

1. validate artifact digests and the eligible-fixture hash;
2. never refit the Stage-B score/sign;
3. report zero-movement rows explicitly;
4. separate all-34 target diagnostics from non-zero-direction comparability;
5. report per-league diagnostics without excluding any league;
6. remain hypothesis generation because V2B is already opened;
7. require a new unseen cohort for confirmation.

Stage A / Stage B combination or a Stage-A threshold must not be selected post-hoc from
the same V2B direction outcomes.

## Safety

- research-only;
- NO_BET;
- no production promotion;
- no real staking;
- no paid provider action;
- no same-sample mapping retuning.
