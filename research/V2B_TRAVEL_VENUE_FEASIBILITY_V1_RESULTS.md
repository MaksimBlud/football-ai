# V2B TRAVEL / VENUE SOURCE FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / FULL_43_TRAVEL_CITY_PROXY_FEASIBLE**.

## Provenance

First full source-audit workflow run:

`36592526049`

Authoritative artifact:

- ID `11044402420`;
- digest `sha256:24eaa543e51f1d19ec34d5b348fa091b91d31e7eca2ceeac270338dbaab3ab04`;
- generating head `962bb906f3a0552dc6e6cdd7d7a3b1affe470fcf`.

Immutable upstream full-calendar artifact:

- ID `11041563442`;
- digest `sha256:93a2f808b7542a5f9c6429e2808e6f462f044404f3219adef5a1b80d880cf68c`.

Bulk geography sources:

- openfootball/clubs commit `ae3800227c449447b3a337fc0aac79a8f02f4c8b`;
- downloaded archive SHA-256 `9fb8f3376c154b57ef5499645ed4e4a9e4b4881e7b6d74ab6c08705887741816`;
- GeoNames cities500 archive SHA-256 `12ee80f3497790fab8b90102682313bf1e0a740fcbd5950d1463a617df093baa`.

## Technical source correction

The first implementation attempted per-club Wikidata search and was rejected by HTTP 429
before any travel result/report was produced. No market direction had been read. V1 was
therefore corrected, before its first result, to use reproducible bulk sources and a
venue-city centroid proxy instead of exact live-searched stadium coordinates.

One source-plumbing exception was required: the pinned openfootball record for SV
Elversberg contains aliases but no city. The club's official arena information identifies
the venue location as Spiesen-Elversberg, which is frozen as an identity override.

## Coverage

Locked target fixtures:

**43 / 43**

Team-sides:

**86 / 86**

Previous-match host identity reconstructed:

**86 / 86**

Previous host club -> home city:

**86 / 86**

Current target host club -> home city:

**86 / 86 team-sides**

Previous city coordinates:

**86 / 86**

Current city coordinates:

**86 / 86**

Finite travel-city distance:

**86 / 86**

Unique host clubs touched by previous/current venues:

**91**

Resolved club cities:

**91 / 91**

Resolved city coordinates:

**91 / 91**

Unresolved clubs: **0**

Unresolved cities: **0**

## Travel-city distribution

Across the 86 team-sides:

- mean = **399.58 km**;
- median = **316.64 km**;
- maximum = **3695.69 km**;
- <=5 km = **15 / 86**.

These are great-circle city-centroid distances between the host city of the latest
full-calendar prior fixture and the host city of the target fixture.

## Interpretation

`FULL_43_TRAVEL_CITY_PROXY_FEASIBLE`

The source gate passes completely. Travel is therefore a genuinely available, independent
pre-match feature family for the exact locked V2B cohort.

This result says nothing about market direction. It only establishes that the feature can
be reconstructed without leakage and without paid odds requests.

## Next permitted step

A separate feature-only freeze may now define exactly one simple travel/recovery Stage-B
mapping before market direction is joined.

The freeze must be generated from the immutable source artifact and may not inspect
`centre_delta`, observed UP/DOWN, FAIR_CENTRE, or target match outcomes.

## Safety proof

- market rows read = false;
- V2B odds read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- match outcome target used = false;
- threshold fitted to outcomes = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
