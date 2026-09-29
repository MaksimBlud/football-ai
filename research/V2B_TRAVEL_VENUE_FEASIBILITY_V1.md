# V2B TRAVEL / VENUE SOURCE FEASIBILITY V1

Status: **SOURCE / VENUE PROVENANCE FEASIBILITY ONLY — NO DIRECTION TEST**.

## Purpose

Audit whether a reproducible pre-match travel feature can be reconstructed for the exact
43-fixture V2B cohort **without reading market direction**.

The upstream full-calendar load audit already reconstructed the true latest prior match
date for both teams in every locked fixture. This block adds only venue identity and
geographic provenance.

## Immutable upstream source

Full-calendar feasibility artifact:

- artifact ID `11041563442`;
- digest `sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c`;
- locked fixtures = 43;
- team-sides = 86;
- full-calendar feasible = 43/43;
- direction not opened.

## Previous-match venue reconstruction

For each team-side:

1. read the frozen `full_previous_match_date`;
2. if that date is represented by a frozen non-league event, use the fixture label's
   left-side club as the venue host;
3. otherwise reconstruct the league fixture from public Understat 2026/27 league
   schedule data for the exact previous date and team, and use the Understat home club
   as the venue host.

The current target venue host is the locked target fixture's home team.

No market field is needed for either step.

## Geographic source

Primary geographic source: **Wikidata public API**.

For every unique current/previous host club:

- resolve the football-club entity;
- read current home venue property `P115`;
- resolve venue coordinates from `P625`;
- prefer a current/non-ended home-venue statement when qualifiers are available;
- retain entity IDs, venue IDs, labels and coordinates in the audit artifact.

Club search aliases may be frozen only for identity plumbing and may not depend on any
market outcome.

## Distance

If both coordinates are available, compute great-circle distance with the haversine
formula.

For each team-side:

`travel_km_since_previous_match = distance(previous_match_venue, current_target_venue)`

This is a **host-club home-venue proxy**. The audit does not claim that every historical
fixture necessarily used that stadium; neutral-site or exceptional venue cases remain a
limitation and must be flagged if discovered.

## Feasibility gates

Primary full-cohort status `FULL_43_TRAVEL_PROXY_FEASIBLE` requires:

- 43/43 target current venue hosts resolved;
- 86/86 previous-match host identities reconstructed;
- 86/86 previous venue coordinates resolved;
- 86/86 current venue coordinates resolved;
- finite non-negative travel distance for all 86 team-sides.

Otherwise the audit reports the exact failure class and unresolved identities. No
direction mapping is allowed from a partial cohort.

## What is explicitly prohibited

This block must not read or use:

- `centre_delta`;
- market direction;
- FAIR_CENTRE;
- opening/closing corner line;
- target match outcome;
- any Stage-A label;
- any direction threshold.

It also must not:

- fit a travel threshold;
- decide UP/DOWN;
- select leagues;
- drop unresolved rows to manufacture a signal.

## Next permitted block

Only if the exact 43-fixture cohort passes the source gate may a **separate** feature-only
freeze define one simple travel/recovery mapping before any direction join.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase reads/writes;
- no model training;
- no production `.pkl` changes;
- no production promotion.
