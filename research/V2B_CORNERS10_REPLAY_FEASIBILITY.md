# V2B CORNERS10 REPLAY FEASIBILITY

Status: **PREREGISTERED SOURCE/IDENTITY FEASIBILITY AUDIT / NO DIRECTION TEST**

## Purpose

Determine whether the already-opened 43-fixture V2B market cohort can be replayed with a leakage-safe, point-in-time CORNERS10 football-history signal using only repository-owned/public Football-Data corner outcomes.

This block does **not** test the direction hypothesis.

It does not read the V2B raw odds artifact or evaluation rows.

## Frozen cohort source

Immutable V2B lock:

- workflow run `36219786013`;
- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures = 43;
- locked leagues = EPL, La Liga, Serie A, Bundesliga, Ligue 1.

Only `selected_fixture_metadata` from this immutable lock may define target fixtures.

## Outcome-history sources

Use only zero-cost Football-Data CSVs already covered by repository runtime/source contracts.

For every target league:

- previous top-flight season = 2025/26;
- current top-flight season = 2026/27.

Historical 2025/26 source:

- EPL: E0 / 2526;
- La Liga: SP1 / 2526;
- Serie A: I1 / 2526;
- Bundesliga: D1 / 2526;
- Ligue 1: F1 / 2526.

Current 2026/27 source:

- EPL: explicit repository-owned corner-only E0 / 2627 contract;
- La Liga: SP1 / 2627;
- Serie A: I1 / 2627;
- Bundesliga: D1 / 2627;
- Ligue 1: F1 / 2627.

No Odds API requests.
No Supabase writes.
No production-model operations.

## Canonical historical rule

Follow the existing Historical Football Signal Lab convention:

- concatenate seasons in chronological order;
- process each fixture using only rows strictly before that fixture;
- maintain team histories continuously across season boundaries;
- never use the target fixture itself;
- never use a later fixture.

The canonical CORNERS10 horizon is 10 prior matches.

This feasibility block does not invent lower-division carryover for newly promoted clubs. If a club has fewer than 10 prior matches in the top-flight source history available under these contracts, that club is insufficient for canonical top-flight CORNERS10 replay.

## Identity matching

Identity matching is data plumbing only.

Use:

- repository league aliases;
- repository team-name normalizer where applicable;
- a frozen explicit provider-to-Football-Data identity alias map for known naming variants;
- deterministic Unicode/punctuation normalization after aliasing.

No fuzzy matching is allowed for final automatic fixture identity.

Every target fixture must resolve to at most one Football-Data row on the target date.

Ambiguous or unmatched fixtures fail closed.

## Feasibility output

For each of the 43 locked fixtures report:

- fixture_id;
- league;
- kickoff date;
- home and away locked names;
- whether exact source fixture identity was matched;
- prior top-flight corner-history count for home team;
- prior top-flight corner-history count for away team;
- whether both counts are >=10;
- fail reason if not eligible.

Aggregate report:

- matched fixtures / 43;
- fixtures with both teams >=10 prior top-flight matches;
- coverage by league;
- unmatched identities;
- insufficient-history identities.

## Decision rule

This block has no predictive/statistical success threshold.

It only classifies source feasibility:

- `FULL_43_REPLAY_FEASIBLE` if all 43 fixtures match and both teams have >=10 prior top-flight corner-result matches;
- `PARTIAL_REPLAY_FEASIBLE` if all fixtures match but at least one fixture lacks 10-match history for one or both teams;
- `IDENTITY_OR_SOURCE_GAPS` if at least one locked fixture cannot be uniquely matched.

Any later exploratory direction analysis must preserve this exact feasibility result and may not silently replace or backfill ineligible fixtures.

## Safety

- research-only;
- zero-cost public results source;
- no provider odds request;
- no V2B raw odds read;
- no direction statistic;
- no threshold search;
- no betting/staking;
- no production promotion;
- no production `.pkl` modification.
