# V2B TRAVEL VENUE IDENTITY FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / FULL_86_VENUE_IDENTITY_FEASIBLE / NO DISTANCE / NO DIRECTION TEST**

## Provenance

Workflow run:

`36591494472`

Authoritative route-identity artifact:

- ID `11044111558`;
- digest `sha256:8c895a500169760c1fe36fe5eeb40861d06d2aa23a4b26e15d3f580f3243837b`;
- size 5,589 bytes;
- generating head `9872b2c71d025675f1182e12d976f609cb6be24e`.

Immutable V2B cohort source:

- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures = 43;
- team-sides = 86.

No V2B market row or direction outcome was read.

## Sources

League fixture identity:

Football-Data 2026/27 public CSVs:

- EPL = E0;
- La Liga = SP1;
- Serie A = I1;
- Bundesliga = D1;
- Ligue 1 = F1.

Only Date, HomeTeam and AwayTeam are used.

Non-league fixture identity:

the already-frozen official manifest from
`V2B_FULL_CALENDAR_LOAD_FEASIBILITY_V1`.

It covers the relevant Champions League, Europa League, Carabao Cup and Coppa Italia
fixtures inside the V2B pre-match window.

## Result

Immediately previous competitive fixture resolved:

**86 / 86 team-sides**

V2B fixtures with both teams resolved:

**43 / 43**

Final status:

**`FULL_86_VENUE_IDENTITY_FEASIBLE`**

## Previous-fixture structure

Team-sides whose immediately previous match was away:

**39 / 86**

Team-sides whose immediately previous match came from the frozen non-league manifest:

**25 / 86**

Team-sides where the previous fixture venue identity differs from the target fixture
venue identity:

**72 / 86**

This does not yet mean 72 positive travel distances; clubs can share cities or stadium
areas. It means the route endpoints are distinct club-venue identities and are ready for
a coordinate layer.

## By league

EPL:

- sides = 18;
- resolved = 18;
- previous away = 9;
- previous non-league = 14;
- venue identity changed = 15.

La Liga:

- sides = 18;
- resolved = 18;
- previous away = 8;
- previous non-league = 2;
- venue identity changed = 15.

Serie A:

- sides = 18;
- resolved = 18;
- previous away = 6;
- previous non-league = 4;
- venue identity changed = 14.

Bundesliga:

- sides = 16;
- resolved = 16;
- previous away = 8;
- previous non-league = 2;
- venue identity changed = 15.

Ligue 1:

- sides = 16;
- resolved = 16;
- previous away = 8;
- previous non-league = 3;
- venue identity changed = 13.

## Identity correction

The first audit resolved 85/86 sides.

The only unresolved side was:

- Rayo Vallecano in Osasuna vs Rayo Vallecano.

Football-Data uses:

`Vallecano`

The correction added only the identity alias:

`Rayo Vallecano -> Vallecano`

No fixture selection, timing rule, market outcome or travel interpretation changed.

After the alias regression, coverage became 86/86.

## What is now known

For every V2B team-side we now know:

- previous competitive fixture date;
- competition;
- previous HOME/AWAY role;
- previous fixture home club;
- previous fixture away club;
- previous venue identity;
- previous opponent identity;
- target venue identity.

This is enough to define route endpoints at the club/venue-identity level.

## What is NOT known yet

This artifact does not contain:

- stadium coordinates;
- city coordinates;
- great-circle distance;
- road/rail distance;
- flight distance;
- transport mode;
- border crossings;
- time-zone changes.

No numerical travel burden should be claimed yet.

## Next permitted block

Audit one coordinate source for the exact venue labels present in this immutable route
artifact.

Preferred order:

1. try a public football-club/stadium coordinate source with explicit club/venue identity;
2. fall back to city-level coordinates only when stadium coordinates are unavailable;
3. freeze the coordinate mapping before computing any relationship with market direction.

The coordinate audit must report:

- unique previous/target venue identities;
- exact coordinate coverage;
- stadium-level vs city-level source type;
- unresolved identities;
- duplicate/ambiguous identities;
- source provenance.

Only after coordinate coverage is acceptable may a separate block compute route
distance.

## Safety

- research-only;
- NO_BET;
- coordinate layer applied = false;
- distance km computed = false;
- market rows read = false;
- centre_delta read = false;
- direction test performed = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production `.pkl` hashes unchanged.
