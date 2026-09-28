# V2B TRUE XG STAGE-B FREEZE V1

Status: **PREREGISTERED FEATURE FREEZE / NO DIRECTION TEST**

## Purpose

Freeze one simple true-xG Stage-B direction hypothesis for the exact 34-fixture
V2B subset that passed `V2B_TRUE_XG5_REPLAY_FEASIBILITY_V1`.

No V2B market direction may be read in this block.

## Immutable upstream source

True-xG feasibility artifact:

- ID `10976063737`;
- digest `sha256:a5431c36071fe378791c7d4ace446133fcada6a5b2ba67e51b0dacea7a0de28c`;
- locked fixtures = 43;
- identity matched = 43/43;
- xG5 feasible = 34/43.

Eligibility is unchanged:

- source identity must be MATCHED;
- both teams must have >=5 strictly prior valid Understat xG rows;
- no lower-division backfill;
- no fixture replacement.

Expected coverage:

- EPL 6;
- La Liga 9;
- Serie A 7;
- Bundesliga 6;
- Ligue 1 6.

## Frozen source features

Use only the immutable feasibility artifact's rolling last-five non-penalty xG fields:

- home `npxG_last5`;
- home `npxGA_last5`;
- away `npxG_last5`;
- away `npxGA_last5`.

Penalty xG is deliberately excluded from the primary mapping because penalties are
high-impact but relatively sparse events and are not the intended representation of
sustained match pressure.

## Frozen common baseline

Use one **common**, not league-specific, baseline from the fully completed 2025/26
top-five Understat source.

For every valid 2025/26 team-match row in:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1;

compute:

`total_npxg_environment = npxG + npxGA`

Then compute one pooled row-weighted mean across all five leagues:

`pooled_2025_26_top5_baseline = mean(total_npxg_environment)`

This baseline uses only the completed prior season. It cannot contain a 2026/27 V2B
target result or market outcome.

No league-specific baseline or threshold is allowed.

## Frozen Stage-B mapping

Mapping ID:

`POOLED_2025_NPXG_ENVIRONMENT_SIGN_V1`

For each eligible fixture:

`expected_home_npxg = 0.5 * (home_npxg_last5 + away_npxga_last5)`

`expected_away_npxg = 0.5 * (away_npxg_last5 + home_npxga_last5)`

`joint_expected_npxg = expected_home_npxg + expected_away_npxg`

`stage_b_score = joint_expected_npxg - pooled_2025_26_top5_baseline`

Call:

- score > 0 -> `UP`;
- score < 0 -> `DOWN`;
- score == 0 -> `NO_CALL`.

Interpretation: recent non-penalty chance creation/concession implies a higher or lower
match chance environment than the single completed-season top-five reference level.

## No fitting / no post-hoc flexibility

The mapping contains:

- no fitted weights;
- no learned threshold;
- no league-specific sign;
- no league-specific baseline;
- no opening corner line;
- no FAIR_CENTRE;
- no `centre_delta`;
- no V2B direction outcome.

After this freeze, the sign, baseline definition, five-match horizon and formula may not
be changed based on V2B direction results.

## Allowed output

The freeze artifact may contain:

- exact 34 fixture identities;
- frozen xG5 values;
- previous-season pooled baseline and source summary;
- expected home/away/joint npxG environment;
- frozen score and UP/DOWN/NO_CALL;
- deterministic cohort and feature hashes.

It must not contain any market-direction target or evaluation statistic.

## Evidence status

A later V2B evaluation will be opened-sample hypothesis generation only.

Even a promising V2B result would require a genuinely new unseen market cohort for
confirmation.

## Safety

- research-only;
- NO_BET;
- no Odds API call;
- no Supabase write;
- no model training/promotion;
- no production `.pkl` modification.
