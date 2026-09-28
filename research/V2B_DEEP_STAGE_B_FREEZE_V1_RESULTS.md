# V2B DEEP STAGE-B FREEZE V1 — Results

Status: **FEATURE COHORT FROZEN / NO DIRECTION TEST**

## Provenance

Workflow run:

`36448872259`

Authoritative freeze artifact:

- ID `10982056918`;
- digest `sha256:e92112d98805a06e2452ce70c365735c2a2dd308a7a62be66b1081182fa7f812`;
- size 3,383 bytes;
- generating head `d80b9350df28cc6b4cb03e61512dc1a3a6877b93`.

Frozen tactical feasibility source:

- artifact `10981596648`;
- digest `sha256:e686e483e375b59484bb493904870f8942e1df70d4553ad5928596476d9054c5`.

No market-direction artifact was read in this block.

## Frozen pooled baseline

Completed 2025/26 Understat top-five source:

- valid team-match rows = **3,504**;
- pooled `deep + deep_allowed` environment baseline =
  **12.8561643836**.

One pooled value is used for all leagues.

No league-specific threshold or baseline is allowed.

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

`sha256:7d114e4fb36ef08dc9e2e7998bc4560ea1b10b28e6296743a68ca08bb073b483`

## Frozen mapping

`POOLED_2025_DEEP_ENVIRONMENT_SIGN_V1`

`expected_home_deep = 0.5 * (home_deep_last5 + away_deep_allowed_last5)`

`expected_away_deep = 0.5 * (away_deep_last5 + home_deep_allowed_last5)`

`joint_expected_deep = expected_home_deep + expected_away_deep`

`stage_b_score = joint_expected_deep - 12.8561643836`

- score > 0 -> UP;
- score < 0 -> DOWN;
- score == 0 -> NO_CALL.

PPDA is explicitly not part of the primary mapping.

## Frozen calls

- UP = **28**;
- DOWN = **6**;
- NO_CALL = **0**.

Observed score range:

- minimum = **-2.1561643836**;
- maximum = **+8.0438356164**.

The call imbalance is retained unchanged. It does not authorize threshold movement or
league-specific normalization after market direction is opened.

## Safety proof

The authoritative run confirms:

- market rows read = false;
- V2B odds read = false;
- opening lambda read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- PPDA used in primary mapping = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.

## Next permitted block

A separate evaluator may join this exact immutable feature artifact to the already-opened
V2B market-direction artifact.

It must:

1. validate artifact ID/digest and both frozen hashes;
2. keep the exact 34 fixtures and 28/6 call split;
3. report zero movement explicitly;
4. compare raw concordance with a constant-UP baseline because the calls are imbalanced;
5. report balanced directional accuracy / UP and DOWN recall;
6. report by-league diagnostics and continuous score association;
7. not switch to PPDA after seeing outcomes;
8. not move the pooled baseline or change the five-match horizon.

Any result is opened-sample hypothesis generation only.

## Safety

- research-only;
- NO_BET;
- no same-sample retuning;
- no automatic production promotion.
