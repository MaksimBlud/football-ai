# V2B TRAVEL COORDINATE FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / FULL_86_STADIUM_COORDINATE_FEASIBLE / NO DISTANCE / NO DIRECTION TEST**

## Provenance

Workflow run:

`36596063770`

Authoritative coordinate artifact:

- ID `11046082462`;
- digest `sha256:f6b334614adde392ad9195c00c883ecf2d1e4d5f1d810b87e86c4d21ae549b02`;
- size 7,963 bytes;
- generating head `8efa70ea5216c1ae523fff9f01939db1218c4b3e`.

Immutable upstream route source:

- experiment `V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1`;
- artifact `11044111558`;
- digest `sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b`;
- 43 locked fixtures;
- 86/86 team-sides with previous/target venue identity resolved.

No V2B market row, centre_delta or direction target was read.

## Coordinate source contract

Primary identity path:

`canonical club title -> English Wikipedia pageprops.wikibase_item -> Wikidata club`

Primary stadium path:

`Wikidata club -> P115 home venue -> P625 coordinate`

A direct club P625 coordinate was allowed only as an explicit fallback category and was
never promoted silently to stadium-level coverage.

Final artifact required **zero** such fallbacks.

## Coverage result

Unique route venue labels:

**93**

Stadium-coordinate labels:

**93 / 93**

Direct club-coordinate fallbacks:

**0**

Ambiguous active home venues:

**0**

Unresolved club identities:

**0**

No-coordinate labels:

**0**

Final label status distribution:

- `STADIUM_COORDINATE` = **93**.

## Route-level coverage

Team-side routes with both previous and target stadium coordinates:

**86 / 86**

V2B fixtures with both teams fully stadium-coordinate feasible:

**43 / 43**

Therefore the exact frozen route cohort is now fully geospatially reconstructable at
stadium level.

Final status:

**`FULL_86_STADIUM_COORDINATE_FEASIBLE`**

## External request efficiency

Public HTTP requests:

**6**

The first implementation used one Wikidata search request per club and hit public 429
rate limiting.

The final implementation instead used:

1. batched English Wikipedia title -> Wikidata QID resolution;
2. batched Wikidata club entity reads;
3. batched Wikidata home-venue entity reads.

This reduced external calls to six while preserving the same selection contract.

## Identity corrections

Five initial unresolved labels were generic English Wikipedia titles rather than missing
clubs:

- Chelsea;
- Crystal Palace;
- Everton;
- Fulham;
- Liverpool.

They were frozen to football-club titles:

- Chelsea F.C.;
- Crystal Palace F.C.;
- Everton F.C.;
- Fulham F.C.;
- Liverpool F.C.

This is identity plumbing only and was performed without reading market direction.

## SC Freiburg ambiguity

Wikidata exposes two coordinate-bearing home venues for SC Freiburg without a unique
preferred selection:

- old Dreisamstadion;
- current Europa-Park-Stadion.

The source contract therefore failed closed rather than arbitrarily choosing one.

A single explicit current-venue override was then frozen:

- route label: `Freiburg`;
- club: SC Freiburg;
- venue: Europa-Park-Stadion;
- Wikidata venue: `Q64586775`.

Independent source support:

- OpenFootball current club file lists SC Freiburg at Europa-Park Stadion;
- OpenFootball stadium file lists Europa-Park Stadion as the new SC Freiburg ground;
- Wikidata Q64586775 supplies stadium coordinates and SC Freiburg occupancy.

No other venue override was required.

## Binding interpretation

Travel distance is now technically feasible for the entire frozen V2B cohort.

This result does **not** imply that travel distance predicts corner-market direction.

No distance has yet been calculated in the authoritative experiment and no market outcome
has been joined.

## Next permitted block

Compute one deterministic route-distance artifact from the coordinates frozen here.

Recommended primary metric:

**great-circle / Haversine distance from previous stadium to target stadium**

Reasons:

- deterministic;
- independent of inferred transport mode;
- comparable across countries;
- requires no commercial routing API;
- can be reproduced exactly from frozen coordinates.

The distance block should report:

- all 86 team-side route distances;
- home vs away target role;
- previous-match HOME/AWAY role if carried through route provenance;
- route distance distribution;
- team-side and fixture-level coverage;
- zero-distance/shared-city cases;
- no market direction.

Only after distance itself is frozen should a separate Stage-B hypothesis be defined.

## Safety

- research-only;
- NO_BET;
- coordinate layer applied = true;
- distance km computed = false;
- market rows read = false;
- centre_delta read = false;
- direction test performed = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
