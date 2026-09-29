# V2B TRAVEL / VENUE SOURCE FEASIBILITY V1

Status: **SOURCE / VENUE-CITY PROVENANCE FEASIBILITY ONLY — NO DIRECTION TEST**.

## Purpose

Audit whether a reproducible pre-match travel proxy can be reconstructed for the exact
43-fixture V2B cohort **without reading market direction**.

The upstream full-calendar load audit already reconstructed the true latest prior match
date for both teams in every locked fixture. This block adds only previous-match host
identity and geographic provenance.

## Immutable upstream source

Full-calendar feasibility artifact:

- artifact ID `11041563442`;
- digest `sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c`;
- locked fixtures = 43;
- team-sides = 86;
- full-calendar feasible = 43/43;
- direction not opened.

## Previous-match host reconstruction

For each team-side:

1. read the frozen `full_previous_match_date`;
2. if that date is represented by a frozen non-league event, use the fixture label's
   left-side club as the host;
3. otherwise reconstruct the league fixture from public Understat 2026/27 league
   schedule data for the exact previous date and team, and use the Understat home club
   as the host.

The current target host is the locked target fixture's home team.

No market field is needed for either step.

## Geographic source contract

### Technical correction before first result

The first source-audit workflow attempted live Wikidata entity search and was rate-limited
with HTTP 429 before a single travel result/report was produced. No market direction or
travel outcome was observed. Therefore the hypothesis is unchanged, but the source
contract is corrected before the first result to remove a non-reproducible live-search
dependency.

V1 now uses two bulk/offline public sources:

1. **openfootball/clubs**, pinned to commit
   `ae3800227c449447b3a337fc0aac79a8f02f4c8b`, for club alias -> home city identity;
2. **GeoNames cities500 bulk dump** for city coordinates.

The workflow records the SHA-256 digest of both downloaded source archives in the audit
artifact. No per-club geocoding API is used.

Because this is city-level provenance, the feature is explicitly renamed a
**venue-city travel proxy**, not exact stadium travel.

## Distance

For every unique host club:

- resolve the club to one openfootball club record and country;
- extract its home city;
- resolve that city/country against GeoNames names/ASCII names/alternate names;
- use the selected GeoNames WGS84 latitude/longitude.

For each team-side:

`travel_city_km_since_previous_match = distance(previous_host_city, target_host_city)`

Distance is great-circle haversine distance.

This intentionally avoids claiming exact stadium coordinates. Same-city stadium changes
therefore map to approximately zero city travel, which is appropriate for a travel-load
proxy.

## Feasibility gates

Primary full-cohort status `FULL_43_TRAVEL_CITY_PROXY_FEASIBLE` requires:

- 86/86 previous-match host identities reconstructed;
- every unique previous/current host club resolved to exactly one club/country/city;
- every resolved city matched to GeoNames coordinates;
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
