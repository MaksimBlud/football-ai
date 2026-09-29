# V2B TRAVEL VENUE IDENTITY FEASIBILITY V1

Status: **SOURCE / ROUTE-IDENTITY FEASIBILITY ONLY — NO DISTANCE, NO DIRECTION TEST**

## Question

Before computing travel kilometers, can we reconstruct the venue identity of the
immediately previous competitive fixture for both teams in every frozen V2B match?

This is deliberately narrower than a travel model.

A distance number is only meaningful if we first know:

1. the previous fixture identity;
2. whether the target team was home or away;
3. the previous fixture venue identity;
4. the target fixture venue identity.

## Frozen cohort

Use the immutable 43-fixture V2B lock:

- artifact ID `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`.

There are exactly 86 team-sides.

## League fixture source

Use the public 2026/27 Football-Data CSV fixture/result identity:

- EPL: `E0`;
- La Liga: `SP1`;
- Serie A: `I1`;
- Bundesliga: `D1`;
- Ligue 1: `F1`.

Only:

- Date;
- HomeTeam;
- AwayTeam

are used.

Scores, odds and market columns are irrelevant to this audit.

## Non-league source

Reuse the already-frozen official fixture manifest from:

`V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1`

covering the relevant Champions League, Europa League, Carabao Cup and Coppa Italia
fixtures before the V2B targets.

Fixture labels are parsed as:

`home vs away`

and the previously frozen target-team identity list determines which V2B team
participated.

## Output per team-side

For each home and away team in each of the 43 target fixtures, record:

- previous event date;
- previous event source;
- previous competition;
- previous HOME/AWAY role;
- previous home/away labels;
- previous venue identity = previous fixture home team;
- previous opponent identity;
- target venue identity = target fixture home team;
- whether the venue identity changes between the previous and target fixtures.

This is an identity layer only.

## Explicitly NOT done here

Do not:

- assign latitude/longitude;
- compute kilometers;
- infer flights;
- infer road/rail travel;
- weight European vs domestic travel;
- inspect centre_delta;
- define UP/DOWN;
- use match outcomes as a target;
- use odds.

A later coordinate-source audit may consume this route identity artifact.

## Success status

`FULL_86_VENUE_IDENTITY_FEASIBLE`

requires a resolved immediately previous fixture and venue identity for all 86 team-sides.

Any unresolved league source or team identity fails closed.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no production model operations;
- no promotion.
