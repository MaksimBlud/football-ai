# V2B TRAVEL COORDINATE FEASIBILITY V1

Status: **COORDINATE SOURCE FEASIBILITY ONLY — NO DISTANCE, NO DIRECTION TEST**

## Purpose

The previous travel block established deterministic route identities for all 86 team-sides:

`previous fixture venue identity -> target fixture venue identity`

This block asks whether those endpoint identities can be mapped to reproducible
coordinates without inventing locations.

## Immutable upstream route artifact

Use:

- experiment `V2B_TRAVEL_VENUE_IDENTITY_FEASIBILITY_V1`;
- artifact ID `11044111558`;
- digest `sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b`;
- 43 fixtures;
- 86/86 team-sides resolved.

## Primary coordinate source

Wikidata API.

Primary stadium-level contract:

`football club -> home venue (P115) -> coordinate location (P625)`

The target date for filtering dated home-venue claims is:

**20 September 2026**

Deprecated claims are ignored. A P115 claim explicitly ended before the target date is
not considered active.

## Coordinate quality levels

### STADIUM_COORDINATE

Accepted only when a selected club has one unambiguous active/preferred P115 home venue
with a valid P625 coordinate.

### CLUB_COORDINATE_FALLBACK

If no usable stadium coordinate exists but the club item itself has P625, record it only
as an explicit fallback.

It is **not** treated as stadium-level coverage.

### AMBIGUOUS_ACTIVE_HOME_VENUES

If multiple active coordinate-bearing home venues remain without an unambiguous preferred
selection, fail closed for stadium-level coverage.

### CLUB_IDENTITY_UNRESOLVED / NO_COORDINATE

Remain unresolved. Do not geocode them by guess.

## Identity queries

The route artifact contains provider aliases such as:

- Man City;
- Milan;
- Ath Bilbao;
- Vallecano;
- Leverkusen.

A frozen alias table maps only these identities to clearer club search labels. It does
not change the route or choose values based on market outcomes.

## Mandatory report

Report both label-level and route-level coverage:

- unique route venue labels;
- stadium-coordinate labels;
- direct-club fallback labels;
- ambiguous labels;
- unresolved labels;
- stadium-coordinate feasible team-sides;
- any-coordinate feasible team-sides;
- fixtures with both sides stadium-coordinate feasible;
- fixtures with both sides any-coordinate feasible.

## Explicitly NOT done

This block does not:

- compute Haversine distance;
- compute road/rail/flight distance;
- infer transport mode;
- combine distance with rest;
- inspect market rows;
- inspect centre_delta;
- define UP/DOWN;
- use target match outcomes.

Only a later block may compute route distance, and only from coordinates frozen here.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no model training/promotion;
- production `.pkl` unchanged.
