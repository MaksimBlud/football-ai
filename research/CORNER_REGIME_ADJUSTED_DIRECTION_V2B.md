# CORNER_REGIME_ADJUSTED_DIRECTION_V2B

Status: **PREREGISTERED AFTER METADATA AVAILABILITY / BEFORE ANY V2B ODDS ACCESS**

## Why V2B exists

The original V2 operational metadata gate required:

- >=2 qualifying league-day blocks per league;
- >=12 qualifying blocks pooled;
- >=80 metadata potential pairs pooled.

Two authoritative metadata-only runs on 2026-09-26 showed stable inventory:

- 43 future finished fixtures;
- 10 qualifying league-day blocks;
- 74 metadata potential unordered pairs;
- exactly 2 qualifying blocks in each of all five leagues.

No V2 odds were opened and no market prices were inspected.

At explicit user instruction, the operational metadata lock gate is revised for a new experiment rather than rewriting V2 in place.

This new experiment is:

`CORNER_REGIME_ADJUSTED_DIRECTION_V2B`

The original V2 remains historically intact and must continue to be reported as `WAIT_FOR_COHORT` under its 12/80 operational gate.

## Methodological status

V2B is created **after seeing fixture metadata availability but before seeing any V2B odds or direction outcomes**.

Therefore:

- the 10/74 operational stopping rule is not an untouched prospective metadata-design choice;
- it must not be described as if it had been fixed before observing metadata density;
- however, the actual market data, FAIR_CENTRE values, centre_delta values and direction outcomes remain unopened at the moment of this preregistration.

The final statistical direction test is not weakened.

## Frozen V2B cohort gate

Future cutoff remains:

`2026-09-19T00:00:00Z`

Frozen leagues remain:

- EPL
- LA_LIGA
- SERIE_A
- BUNDESLIGA
- LIGUE_1

Regime block remains:

`(league, UTC kickoff date)`

Minimum fixtures per qualifying block remains:

**2**

Minimum qualifying blocks per league remains:

**2**

Revised pooled metadata gate:

- minimum total qualifying blocks = **10**;
- minimum metadata potential unordered pairs = **74**.

Selection remains deterministic:

1. use only finished fixtures at/after the frozen future cutoff;
2. exclude the same 151 prior frozen fixture IDs;
3. build whole league-day blocks;
4. sort blocks by UTC date ascending, then fixed league order;
5. select the earliest prefix satisfying:
   - >=2 blocks in every league;
   - >=10 blocks pooled;
   - >=74 metadata potential pairs;
6. never cherry-pick individual fixtures;
7. never replace/backfill a selected fixture.

## Frozen source artifact for first V2B cohort

V2B is allowed to consume the already-captured immutable metadata artifact from authoritative run:

`36218898253`

Artifact:

`10898297066`

Digest:

`sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`

That artifact was captured metadata-only:

- provider requests = 5;
- odds endpoint used = false;
- market prices opened = false;
- match outcomes used = false;
- football-state used = false;
- paid subscription used = false.

Under the V2B 10/74 operational gate, the deterministic earliest qualifying prefix is expected to contain all 10 available qualifying blocks and 43 fixtures.

That expectation must be verified by code, not hard-coded as fixture selection.

## Statistical direction gate remains unchanged

The downstream direction test remains exactly the V1/V2 contract:

- direction score = `-opening_lambda` / `-FAIR_CENTRE`;
- regime block = league + UTC kickoff date;
- within-block unordered pairwise concordance;
- ties omitted;
- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- permutation seed `20260918`;
- one-sided p <0.10.

Allowed final evaluated verdicts remain:

- `INDIVIDUAL_DIRECTION_DISCRIMINATION_REPLICATED`;
- `INDIVIDUAL_DIRECTION_DISCRIMINATION_NOT_CONFIRMED`;
- `SAMPLE_TOO_SMALL`.

No statistical threshold is lowered from V1/V2.

## Required safety chain

Before any V2B odds access:

1. validate the immutable source metadata artifact;
2. derive the deterministic V2B locked cohort;
3. persist exact selected blocks;
4. persist exact selected fixture IDs;
5. bind exact selected fixture metadata:
   - fixture_id;
   - league;
   - league_id;
   - kickoff_utc;
   - home_team;
   - away_team;
6. compute deterministic `selection_sha256`;
7. compute deterministic `fixture_metadata_sha256`;
8. generate deterministic offline acquisition batches;
9. only then may a separate live-capable odds-acquisition PR be created.

## Safety

- research-only;
- no betting;
- no production promotion;
- no Supabase writes;
- no automatic model changes;
- no provider odds access in cohort-lock construction;
- no post-odds fixture reselection;
- no post-result weakening of the unchanged statistical gate.

