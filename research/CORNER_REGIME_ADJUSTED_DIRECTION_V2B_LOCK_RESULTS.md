# CORNER_REGIME_ADJUSTED_DIRECTION_V2B_LOCK_RESULTS

Status: **IMMUTABLE_COHORT_LOCKED / 43 FIXTURES / NO ODDS OPENED**

## Provenance

V2B implementation:

- PR #411;
- merge: `385df56a54d36a8326f02ae07c02dd868111dca1`.

V2B lock materialization workflow:

- PR #412;
- merge: `277f53c3717c468c21ac704e1ca041bd5a91c007`;
- authoritative workflow run: `36219786013`;
- immutable lock artifact ID: `10899325930`;
- artifact digest: `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- artifact size: 9,198 bytes.

Source metadata artifact:

- run: `36218898253`;
- artifact ID: `10898297066`;
- digest: `sha256:eb163d097dc2713b8f8f03370eacead91a15d3a38c0757e48b301d82e799446c`.

## Methodological status

V2B was created after fixture-metadata density had been observed but before any V2B odds or market prices were opened.

Therefore the 10-block / 74-potential-pair operational stopping rule is a **post-metadata / pre-odds amendment** and must be reported that way.

The original V2 remains historically intact under its 12/80 metadata gate.

The downstream statistical direction gate was not weakened.

## Locked cohort

Operational metadata gate:

- minimum blocks per league = **2**;
- minimum pooled blocks = **10**;
- minimum metadata potential pairs = **74**.

Result:

- status = `COHORT_LOCKED`;
- selected blocks = **10**;
- selected fixtures = **43**;
- metadata potential pairs = **74**;
- EPL blocks = 2;
- La Liga blocks = 2;
- Serie A blocks = 2;
- Bundesliga blocks = 2;
- Ligue 1 blocks = 2.

No fixture reselection or backfill is permitted after this lock.

## Immutable identity

`selection_sha256`:

`sha256:9f4470ee2e11d94e821e37bf1e3a5d9ebd40da893290d0c636c1ed3c62600f73`

`fixture_metadata_sha256`:

`sha256:dd057a3fc9c6a069f4717ecc7f3863f1e7dc991e6b01e82a4c84f13c40271bbb`

The selection hash binds:

- future cutoff;
- V2B cohort gate;
- exact ordered selected blocks;
- exact ordered 43 fixture IDs;
- exact ordered immutable fixture metadata.

Fixture metadata includes:

- fixture_id;
- league;
- league_id;
- kickoff_utc;
- home_team;
- away_team.

## Statistical gate remains unchanged

The later direction evaluator must still require:

- >=30 eligible normalized rows;
- >=4 leagues with comparable pairs;
- >=8 contributing regime blocks;
- >=40 actual comparable pairs;
- concordance >=0.60;
- 20,000 regime-preserving permutations;
- seed `20260918`;
- one-sided p <0.10.

The 74 metadata potential pairs are not a substitute for the later >=40 actual comparable pairs after market normalization.

## Safety proof

Lock materialization used:

- immutable GitHub metadata artifact only;
- no provider requests;
- no odds endpoint;
- no market-price reads;
- no match outcomes;
- no football-state features;
- no paid action;
- no Supabase writes;
- no production model changes.

Production `.pkl` hash guard passed.

The lock explicitly keeps:

- `odds_acquisition_authorized = false`;
- `betting_enabled = false`;
- `production_promotion_authorized = false`.

## Next step

The project no longer waits for additional fixtures for V2B.

Next:

1. generate a deterministic offline acquisition plan from immutable lock artifact `10899325930`;
2. preserve exact 43 fixture IDs and immutable metadata;
3. split requests deterministically under the pre-existing operational request cap;
4. only then create a separate controlled live odds-acquisition PR;
5. after complete raw acquisition, run the frozen offline direction evaluator.

## Deterministic offline acquisition plan

PR #414 merged as:

`8809fc7b61b2a1d9807a536a8d4de1a876cc2e2c`

Plan workflow run:

`36220204953`

Immutable plan artifact:

- ID `10899305926`;
- digest `sha256:8fe2203443f4e59a5800fd7315df6d333a19771e9827d3cad64ef4f658119c56`;
- size 3,142 bytes.

Plan:

- exact 43 locked fixture IDs;
- batch 1 = 30;
- batch 2 = 13;
- total requests = 43;
- no fixture discovery/reselection;
- no provider call during plan construction;
- live odds acquisition remains disabled until a separate controlled live PR.

