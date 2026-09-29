# V2B FULL-CALENDAR LOAD FEASIBILITY V1

Status: **SOURCE / FEATURE FEASIBILITY ONLY — NO DIRECTION TEST**

## Question

Can the exact frozen V2B cohort be reconstructed with a materially more complete
pre-match schedule than the already-closed league-only schedule signal?

The old `SCHEDULE_V1` used league fixtures only. This audit adds the non-league
competitions that actually occur inside the exact 14-day lookback before the V2B target
fixtures on 19–20 September 2026.

## Frozen target window

V2B target dates:

- 19 September 2026;
- 20 September 2026.

Primary lookback:

**14 calendar days strictly before target date.**

No future fixture after the target match is used.

## League source

Public Understat 2026/27 team histories.

Only match dates strictly before each target fixture are used.

Understat is used here only for league calendar dates, not xG as a predictor.

## Frozen official non-league manifest

The manifest is frozen before any schedule-direction comparison.

Relevant official competition windows:

### UEFA Champions League

Matchday 1: 8–10 September 2026.

Official source:
https://www.uefa.com/uefachampionsleague/news/02a8-2174c9e9019d-f909a77bd77a-1000--2026-27-champions-league-all-the-league-phase-fixtures/

### UEFA Europa League

Matchday 1: 16–17 September 2026.

Official source:
https://www.uefa.com/uefaeuropaleague/news/02a8-2174cafa5bb6-82bbc20c9b92-1000--2026-27-europa-league-all-the-league-phase-fixtures/

### Carabao Cup

Round 3: 8–17 September 2026.

Official source:
https://www.efl.com/news/2026/august/28/carabao-cup--third-round-dates-confirmed/

### Coppa Italia

Relevant fixtures inside the target lookback:

- Genoa vs Südtirol — 15 September;
- Fiorentina vs Pisa — 15 September.

Official source:
https://www.legaseriea.it/coppa-italia/news/ecco-quando-si-giocano-i-sedicesimi

## Explicit competition exclusions for this exact window

These are not silently assumed absent; their official calendars place them outside the
14-day target window:

- DFB-Pokal: first round ends 2 September; second round is 27–28 October.
- Copa del Rey: preliminary ties begin 26–27 September, after V2B targets.
- Coupe de France: Ligue 1 clubs enter 20 December.
- UEFA Conference League league phase begins 15 October.

Therefore the frozen manifest is specific to this exact V2B 14-day window. It is **not**
a universal all-season calendar source.

## Feasibility features

For each home and away team:

- league-only previous-match date;
- full-calendar previous-match date;
- league-only rest days;
- full-calendar rest days;
- league-only matches in prior 7 days;
- full-calendar matches in prior 7 days;
- league-only matches in prior 14 days;
- full-calendar matches in prior 14 days;
- non-league matches in prior 7/14 days;
- exact non-league fixture identities used.

The audit also reports how many V2B fixtures materially change when the official
non-league manifest is added.

## What this block does not do

It does not:

- inspect V2B market rows;
- inspect centre_delta;
- define UP/DOWN;
- fit weights;
- select a threshold;
- use travel distance;
- use future fixtures;
- use match outcomes as a target.

Travel is deliberately separate because venue/geographic reconstruction needs its own
source audit.

## Interpretation

Possible statuses:

- `FULL_43_RECONSTRUCTABLE_14D`;
- `PARTIAL_FULL_CALENDAR_FEASIBILITY`;
- `IDENTITY_GAPS`;
- `SOURCE_FETCH_GAPS`.

Only after feasibility is established may a separate Stage-B mapping be frozen.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no production model operations;
- no production promotion.
