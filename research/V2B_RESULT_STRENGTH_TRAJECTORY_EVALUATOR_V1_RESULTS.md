# V2B RESULT STRENGTH TRAJECTORY EVALUATOR V1 — Results

Status: **FINAL OPENED-SAMPLE HYPOTHESIS GENERATION / WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS**

## Provenance

Workflow run:

`36436521309`

Authoritative evaluation job:

`108975916615`

Artifact:

- ID `10975498533`;
- digest `sha256:0cf19ad84659227ad85197c4d3e8f6453a6f67db65f213e521f35dd86c07f004`;
- size 5,558 bytes.

Frozen Stage-B source:

- artifact `10975465958`;
- digest `sha256:d30f4231e7e0a9149d0869ac6d775eac9d2182316593610f2b42637afc26dbe3`;
- eligible fixture identity hash
  `sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`;
- exact frozen calls = 16 UP / 18 DOWN / 0 NO_CALL.

Already-opened V2B market source:

- artifact `10899842049`;
- digest `sha256:7d4ecad191518cc551567ad1513b5f6c53121d56154a6de86b51b99d54f078ff`.

No provider request was made by this evaluator.

## Frozen mapping evaluated

`JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1`

`stage_b_score = home_performance_residual_5 + away_performance_residual_5`

- score > 0 -> UP;
- score < 0 -> DOWN;
- score == 0 -> NO_CALL.

No refit, sign reversal, threshold search, league exclusion or Stage-A tuning occurred.

## Observed movement

Frozen evaluated rows:

**34**

Observed market direction:

- UP = **7**;
- DOWN = **3**;
- ZERO = **24**.

Therefore only:

**10 / 34**

rows were direction-comparable.

## Direction concordance

Comparable rows:

**10**

Concordant rows:

**6**

Pooled concordance:

**0.60**

The frozen exploratory rule required:

**> 0.60**

Therefore the pooled concordance condition did not pass.

## By-league diagnostics

- Bundesliga: 2 comparable, 2 concordant = **1.00**;
- EPL: 2 comparable, 1 concordant = **0.50**;
- La Liga: 2 comparable, 1 concordant = **0.50**;
- Ligue 1: 1 comparable, 0 concordant = **0.00**;
- Serie A: 3 comparable, 2 concordant = **0.6667**.

Leagues with >=2 comparable rows and concordance >0.50:

**2**

The frozen gate required at least:

**3**

## Frozen call-group diagnostics

UP calls:

- rows = 16;
- zero movement = 9;
- mean centre_delta = **+0.1260770552**;
- median centre_delta = 0.

DOWN calls:

- rows = 18;
- zero movement = 15;
- mean centre_delta = **+0.0548378841**;
- median centre_delta = 0.

Therefore the sign-group mean requirement also failed:

- UP mean was positive as expected;
- DOWN mean was **positive**, not negative.

## Confusion including zero movement

Frozen UP calls:

- observed UP = 5;
- observed DOWN = 2;
- observed ZERO = 9.

Frozen DOWN calls:

- observed DOWN = 1;
- observed UP = 2;
- observed ZERO = 15.

There were no frozen NO_CALL rows.

## Continuous relationship

Frozen continuous Stage-B score vs centre_delta:

- Pearson = **+0.1264712705**;
- Spearman = **+0.1436157950**.

The association is weak.

## Final classification

**`WEAK_OR_INCONSISTENT_DIRECTION_HYPOTHESIS`**

The result fails all three core consistency ideas:

1. pooled non-zero concordance is 0.60, not >0.60;
2. only 2 leagues meet the support definition, not >=3;
3. DOWN-call rows do not have negative mean centre movement.

## Binding interpretation

Do not:

- reverse the Stage-B sign;
- select a score threshold;
- change the five-match window;
- fit weights to residual/Elo components;
- drop EPL, La Liga or Ligue 1;
- add a Stage-A FAIR_CENTRE threshold using these same outcomes;
- call the 6/10 result a confirmed 60% predictive edge.

This exact `JOINT_PERFORMANCE_RESIDUAL_5_SIGN_V1` mapping is closed on V2B as a
weak/inconsistent opened-sample hypothesis.

The broader two-stage concept is not disproved. Stage A remains separately supported
for **repricing magnitude/risk**, but this particular Stage-B source does not supply a
portable direction rule.

## Next research implication

Do not spend a new unseen cohort on this exact Stage-B mapping as if it had earned
replication.

The next useful direction block should search for another genuinely independent
point-in-time information source **without** retuning:

- CORNERS10;
- HS/AS/HST/AST SHOTS10;
- this result/Elo residual mapping;
- FAIR_CENTRE opening-state direction.

Candidate families should be screened for source availability and methodological
independence before any new outcome comparison.

## Safety

- research-only;
- opened-sample hypothesis generation only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production .pkl hashes unchanged;
- no automatic promotion.
