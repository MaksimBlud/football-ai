# V2B FULL-CALENDAR LOAD FEASIBILITY V1 — Results

Status: **FINAL SOURCE/FEATURE FEASIBILITY / FULL_43_RECONSTRUCTABLE_14D / NO DIRECTION TEST**

## Provenance

Workflow run:

`36586153137`

Authoritative zero-cost audit artifact:

- ID `11041174634`;
- digest `sha256:366ac99df321757c0a12bf306c0bbef0512632adb29023c7b5465b06dc61be87`;
- size 5,651 bytes;
- generating head `90abf6b9c5a9f35433d2c055e90a4296a846386e`.

Immutable V2B cohort source:

- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures = 43.

No V2B market rows or direction outcomes were read.

## Exact scope

Target dates:

- 19 September 2026;
- 20 September 2026.

Frozen lookback:

**14 calendar days strictly before each target date.**

This is an exact-cohort feasibility result, not a claim that the same manifest is a
universal all-season schedule source.

## Sources used

League match dates:

- public Understat 2026/27 top-five histories.

Frozen official non-league manifest:

- UEFA Champions League Matchday 1, 8–10 September;
- UEFA Europa League Matchday 1, 16–17 September;
- Carabao Cup Round 3, 8–17 September;
- relevant Coppa Italia fixtures on 15 September.

Official competition calendars were also used to establish that, inside this exact
14-day V2B window:

- DFB-Pokal had no fixture after its 1–2 September tail until late October;
- Copa del Rey professional-club participation had not started;
- Ligue 1 clubs had not entered Coupe de France;
- UEFA Conference League league phase had not started.

Frozen non-league fixture manifest:

**38 fixtures**

## Coverage

Fixture identity:

**43 / 43 matched**

Full-calendar reconstruction:

**43 / 43 feasible**

By league:

- EPL: **9 / 9** feasible;
- La Liga: **9 / 9**;
- Serie A: **9 / 9**;
- Bundesliga: **8 / 8**;
- Ligue 1: **8 / 8**.

Final status:

**`FULL_43_RECONSTRUCTABLE_14D`**

## How much league-only load was missing

Team-sides evaluated:

**86**

Team-sides with at least one official non-league event in prior 14 days:

**42 / 86**

Target-team non-league appearances inside the frozen manifest:

- UEFA Champions League = **19**;
- Carabao Cup = **17**;
- UEFA Europa League = **12**;
- Coppa Italia = **2**.

Total target-team appearances:

**50**

A team can appear more than once, so this is not the number of unique team-sides.

V2B fixtures whose load profile changes when non-league matches are added:

**27 / 43**

By league:

- EPL: **9 / 9**;
- La Liga: **6 / 9**;
- Serie A: **6 / 9**;
- Bundesliga: **3 / 8**;
- Ligue 1: **3 / 8**.

## Rest-day impact

Team-sides whose most recent match changes after adding non-league competitions:

**25 / 86**

For those 25 sides, mean reduction in apparent rest:

**3.84 days**

Rest-day reduction distribution:

- 3 days less rest: 10 sides;
- 4 days less rest: 10;
- 5 days less rest: 4;
- 6 days less rest: 1.

Match-level home-minus-away rest differential changes in:

**15 / 43 fixtures**

This is especially important because the old league-only schedule signal would treat
those 15 fixtures as having a different relative recovery state.

## Concrete examples

### Tottenham vs Aston Villa

League-only rest:

- Tottenham = 7 days;
- Aston Villa = 7 days.

Full-calendar rest:

- Tottenham = 4 days;
- Aston Villa = 3 days.

Both teams had non-league load inside the window, and Aston Villa had two non-league
appearances.

### Brighton vs Arsenal

League-only:

- Brighton = 6;
- Arsenal = 7.

Full calendar:

- Brighton = 3;
- Arsenal = 4.

Arsenal had both Champions League and Carabao Cup load.

### Bournemouth vs Liverpool

League-only:

- Bournemouth = 8;
- Liverpool = 8.

Full calendar:

- Bournemouth = 3;
- Liverpool = 5.

Both had two non-league appearances in the lookback.

### Man City vs Sunderland

League-only:

- Man City = 7;
- Sunderland = 8.

Full calendar:

- Man City = 3;
- Sunderland = 4.

Both had two non-league appearances.

### Lyon vs Rennes

League-only:

- Lyon = 7;
- Rennes = 8.

Full calendar:

- Lyon = 3;
- Rennes = 3.

Both played Europa League before the target fixture.

## Method conclusion

The old league-only schedule family and this source are **not equivalent**.

The earlier negative `SCHEDULE_V1` result cannot be used to dismiss this exact
full-calendar family because:

- 27/43 target fixtures change;
- 25/86 team-side latest-match dates change;
- relative rest differential changes in 15/43 matches;
- European and domestic cup load is concentrated immediately before the V2B weekend.

Therefore full-calendar congestion is a genuinely new schedule hypothesis family rather
than a same-sample threshold retune of the closed league-only signal.

## What has NOT been tested

This result says nothing yet about market direction.

There is currently:

- no UP/DOWN formula;
- no fitted weight;
- no threshold;
- no league selection;
- no centre_delta access;
- no Stage-A combination;
- no travel-distance feature.

## Next permitted block

Freeze **one simple recovery/load Stage-B mapping** before opening direction.

A conservative mapping should use only the already reconstructed quantities, for example
relative recovery/load between home and away, and must be frozen without:

- fitting weights;
- searching 7d vs 14d after outcome inspection;
- selecting leagues;
- using FAIR_CENTRE;
- adding travel until travel source provenance is separately audited.

Travel should remain a separate future source family.

## Safety

- research-only;
- NO_BET;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- market rows read = false;
- centre_delta read = false;
- direction test performed = false;
- production `.pkl` hashes unchanged.
