# V2B TRUE XG5 REPLAY FEASIBILITY V1

Status: **PREREGISTERED SOURCE/FEATURE FEASIBILITY / NO DIRECTION TEST**

## Purpose

Determine whether a genuinely richer football-state source — prior completed-match
true xG/npxG from Understat — can be reconstructed point-in-time for the exact frozen
43-fixture V2B cohort.

This block exists because the closed SHOTS10 research explicitly permits a future
independent experiment using true expected-goals or shot-location quality rather than
another transformation of HS/AS/HST/AST.

## Source

Public Understat league-history endpoint already used by the repository's historical
xG pipeline.

Leagues:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Seasons requested:

- 2025 (2025/26);
- 2026 (2026/27).

Required source fields per prior team-match:

- xG;
- xGA;
- npxG;
- npxGA;
- match date.

No current target match xG is allowed into a target feature.

## Frozen target cohort

Consume the immutable V2B lock:

- artifact ID `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- selected fixtures = 43.

## Point-in-time feasibility rule

For each target team:

1. resolve provider-lock team identity to exactly one Understat team title;
2. keep only valid xG rows with match timestamp strictly before target kickoff;
3. require at least 5 valid prior xG rows.

A target fixture is `xg5_feasible` only if **both teams** pass.

No promoted club may be backfilled from a lower division in this V1.

## Allowed output

The feasibility artifact may record:

- source team titles;
- identity matches/gaps;
- counts of valid prior xG rows;
- rolling last-5 xG/xGA/npxG/npxGA values;
- exact feasible fixture count and by-league coverage.

These feature values are source-feasibility evidence only.

## Prohibited in this block

Do not read:

- V2B market evaluation rows;
- opening corner line;
- FAIR_CENTRE/opening lambda;
- centre_delta;
- observed UP/DOWN direction.

Do not calculate:

- direction concordance;
- direction correlation;
- betting return;
- Stage-A threshold;
- final Stage-B mapping.

If true-xG source feasibility passes, a **separate** block must freeze one mapping
before any direction comparison.

## Safety

- research-only;
- zero Odds API calls;
- no Supabase writes;
- no model training/promotion;
- no production .pkl modification;
- NO_BET.
