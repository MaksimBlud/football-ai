# V2B TRUE XG STAGE-B FREEZE V1 — Results

Status: **FEATURE COHORT FROZEN / NO DIRECTION TEST**

## Provenance

Workflow run:

`36442273923`

Authoritative zero-cost feature-freeze artifact:

- ID `10978762060`;
- digest `sha256:e48adcc90274fbb06b6d915d0e1bb521d75cbcc564a86a6290f17da3cd8f189f`;
- size 4,806 bytes;
- generating head `0bf86769aa968634ad7427fc46d4ad92ed92bf8a`.

Immutable feasibility source:

- artifact `10976063737`;
- digest `sha256:a5431c36071fe378791c7d4ace446133fcada6a5b2ba67e51b0dacea7a0de28c`;
- exact true-xG5 feasible cohort = 34/43.

## Frozen previous-season baseline

One common pooled top-five baseline was computed only from completed 2025/26 Understat
team-match rows.

Definition:

`total_npxg_environment = npxG + npxGA`

Pooled team-match rows:

**3,504**

Frozen pooled baseline:

**2.8041087623**

Descriptive source means:

- Bundesliga = 3.133981;
- EPL = 2.874279;
- La Liga = 2.737942;
- Ligue 1 = 2.751611;
- Serie A = 2.576745.

These league values are diagnostics only. The mapping uses the single pooled value
2.8041087623 for every fixture.

## Frozen mapping

Mapping ID:

`POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`

`expected_home_npxg = 0.5 * (home_npxg_last5 + away_npxga_last5)`

`expected_away_npxg = 0.5 * (away_npxg_last5 + home_npxga_last5)`

`joint_expected_npxg = expected_home_npxg + expected_away_npxg`

`stage_b_score = joint_expected_npxg - 2.8041087623`

Call:

- score > 0 -> UP;
- score < 0 -> DOWN;
- score == 0 -> NO_CALL.

## Frozen cohort

Eligible:

**34 / 43**

By league:

- EPL 6;
- La Liga 9;
- Serie A 7;
- Bundesliga 6;
- Ligue 1 6.

Eligible fixture hash:

`sha256:ccfd8c7cdc7b80a9ea2c725bc0da792ead21cd2232f495c6041eecc699edb1a1`

Frozen feature hash:

`sha256:f4128f41a541788a4690bd8f1065cef468622494fe56de2a561a4ba07b59b0a5`

## Frozen call distribution

- UP = **30**;
- DOWN = **4**;
- NO_CALL = **0**.

By league:

- EPL: 6 UP / 0 DOWN;
- La Liga: 8 UP / 1 DOWN;
- Serie A: 6 UP / 1 DOWN;
- Bundesliga: 6 UP / 0 DOWN;
- Ligue 1: 4 UP / 2 DOWN.

Stage-B score range:

- minimum = **-0.284523**;
- maximum = **+1.374900**;
- mean = **+0.463702**;
- median = **+0.466375**.

## Interpretation before direction evaluation

The mapping is validly frozen but materially imbalanced toward UP.

That imbalance is a feature-only fact and was observed without reading V2B market
direction in this block.

Therefore a later opened-sample evaluator must not interpret raw concordance in
isolation. It must preserve the exact mapping and report at minimum:

- all-34 call distribution;
- non-zero market-direction concordance;
- UP/DOWN call-group direction diagnostics;
- by-league diagnostics;
- continuous score-to-centre_delta association;
- a simple constant-direction diagnostic for context, without retuning the frozen
  mapping.

No call-balance tuning is authorized after this freeze.

## Safety proof

The workflow asserted:

- market rows read = false;
- V2B odds read = false;
- opening lambda read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.

## Next permitted block

Evaluate the exact immutable 34-row feature artifact against the already-opened V2B
market artifact as hypothesis generation only.

Do not:

- rebalance the calls;
- move the baseline;
- introduce league-specific baselines;
- change the five-match horizon;
- add xG rather than npxG after seeing direction;
- combine Stage A with a threshold selected on these outcomes.

Confirmation still requires a new unseen cohort.
