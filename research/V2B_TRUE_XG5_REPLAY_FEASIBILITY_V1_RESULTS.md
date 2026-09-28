# V2B TRUE XG5 REPLAY FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / PARTIAL_XG5_FEASIBLE / NO DIRECTION TEST**

## Provenance

Workflow run:

`36438275056`

Authoritative source-feasibility artifact:

- ID `10976063737`;
- digest `sha256:a5431c36071fe378791c7d4ace446133fcada6a5b2ba67e51b0dacea7a0de28c`;
- size 5,492 bytes;
- generating head `d7289f69c7b161253fd9f7c6ff4f67abb54790a9`.

Frozen V2B lock:

- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures = 43.

## Source

Public Understat league history was fetched successfully for all five leagues and
both requested seasons:

- 2025/26;
- 2026/27.

Required valid prior fields:

- xG;
- xGA;
- npxG;
- npxGA;
- match timestamp.

No V2B market artifact was opened by this audit.

## Identity result

After source-driven aliases derived from the actual Understat team titles:

**43 / 43 fixtures identity-matched**

The alias amendments were limited to source identity and did not use any market outcome.

Examples include:

- Hamburg -> Hamburger SV;
- Cologne -> FC Cologne;
- SC Freiburg -> Freiburg;
- Mainz -> Mainz 05;
- RB Leipzig -> RasenBallsport Leipzig;
- Schalke -> Schalke 04;
- Deportivo A Coruna -> Deportivo La Coruna;
- Parma -> Parma Calcio 1913.

## xG5 feasibility result

Fixture passes iff both teams have at least five valid Understat xG rows strictly
before target kickoff.

Feasible:

**34 / 43**

By league:

- EPL: **6 / 9**;
- La Liga: **9 / 9**;
- Serie A: **7 / 9**;
- Bundesliga: **6 / 8**;
- Ligue 1: **6 / 8**.

Final classification:

**`PARTIAL_XG5_FEASIBLE`**

## Nine fixtures below five prior xG matches

- EPL — Newcastle vs Hull: Hull = 4;
- EPL — Everton vs Ipswich: Ipswich = 4;
- EPL — Nottm Forest vs Coventry: Coventry = 4;
- Serie A — Venezia vs Lazio: Venezia = 4;
- Serie A — Frosinone vs Como: Frosinone = 4;
- Bundesliga — Schalke vs Elversberg: Schalke = 3, Elversberg = 3;
- Bundesliga — Paderborn vs TSG Hoffenheim: Paderborn = 3;
- Ligue 1 — Le Mans vs Lorient: Le Mans = 4;
- Ligue 1 — Angers vs Troyes: Troyes = 4.

No lower-division xG history was synthesized.

## Interpretation

A true-xG / npxG Stage-B source is technically reconstructable point-in-time for an
exact **34-fixture** V2B subset.

This is a genuinely richer source family than the closed SHOTS10 count features.

The audit establishes source/identity/feature availability only. It does not establish
that xG predicts corner-market direction.

## Next permitted block

Freeze one simple xG-based total-pressure Stage-B mapping for these exact 34 fixtures
**before** opening any market-direction comparison.

A natural preregistration candidate is a non-penalty xG match-environment score:

- use both teams' rolling last-5 npxG for and npxG against;
- compare their joint expected match environment with a leakage-safe prior league baseline;
- no fitted weights, league-specific thresholds or V2B direction access.

The exact formula must be frozen in a separate block.

## Safety

- research-only;
- market rows read = false;
- V2B odds read = false;
- centre_delta read = false;
- direction test performed = false;
- target match outcome not used;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0;
- production .pkl hashes unchanged;
- NO_BET.
