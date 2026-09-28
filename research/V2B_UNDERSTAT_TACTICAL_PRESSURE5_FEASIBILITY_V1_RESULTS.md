# V2B UNDERSTAT TACTICAL PRESSURE5 FEASIBILITY V1 — Results

Status: **FINAL SOURCE FEASIBILITY / PARTIAL_TACTICAL5_FEASIBLE / NO DIRECTION TEST**

## Provenance

Workflow run:

`36444258107`

Authoritative feasibility artifact:

- ID `10979534783`;
- digest `sha256:c44f2494d53e627c04aa21b5cc6d733fd4d7373004e959f77892b6af9c9d77a2`;
- size 6,259 bytes;
- generating head `bf29d695f8de3366d981c82f7d16a7a059a7141b`.

Frozen V2B lock:

- artifact `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- locked fixtures = 43.

## Source

Public Understat league history, 2025/26 + 2026/27, all five leagues:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Required prior-match fields were present in every source league:

- `deep`;
- `deep_allowed`;
- `ppda`;
- `ppda_allowed`.

All downloaded history rows for these source payloads passed field normalization:

- EPL: 860 / 860 valid tactical rows;
- La Liga: 898 / 898;
- Serie A: 860 / 860;
- Bundesliga: 684 / 684;
- Ligue 1: 702 / 702.

## PPDA normalization

Dictionary PPDA payloads were normalized as:

`ppda_ratio = att / def`

with a finite positive denominator required.

Positive finite numeric payloads are accepted directly.

Invalid values fail closed.

Regression coverage confirms both formats and strict failure on invalid denominator.

## Identity and point-in-time coverage

Fixture identity:

**43 / 43 matched**

A fixture is tactical5-feasible only when both teams have at least five valid tactical
rows strictly before target kickoff.

Feasible:

**34 / 43**

By league:

- EPL = 6 / 9;
- La Liga = 9 / 9;
- Serie A = 7 / 9;
- Bundesliga = 6 / 8;
- Ligue 1 = 6 / 8.

## Nine fixtures below five prior tactical rows

- EPL — Newcastle vs Hull: Hull = 4;
- EPL — Everton vs Ipswich: Ipswich = 4;
- EPL — Nottm Forest vs Coventry: Coventry = 4;
- Serie A — Venezia vs Lazio: Venezia = 4;
- Serie A — Frosinone vs Como: Frosinone = 4;
- Bundesliga — Schalke vs Elversberg: Schalke = 3, Elversberg = 3;
- Bundesliga — Paderborn vs TSG Hoffenheim: Paderborn = 3;
- Ligue 1 — Le Mans vs Lorient: Le Mans = 4;
- Ligue 1 — Angers vs Troyes: Troyes = 4.

No lower-division backfill was used.

## Available point-in-time feature state

For each of the 34 eligible fixtures, the artifact now contains rolling last-five means
for both teams:

- deep;
- deep allowed;
- PPDA;
- PPDA allowed.

These are source/feature feasibility values only. No Stage-B sign was defined here.

## Independence from closed families

This family is not an algebraic rewrite of:

- CORNERS10;
- HS/AS/HST/AST SHOTS10;
- result/Elo residuals;
- absolute npxG environment;
- FAIR_CENTRE/opening-market direction.

It represents prior-match territorial entry and pressing structure.

That makes it a valid new information family for a separate hypothesis, although it may
still be empirically correlated with shots/xG.

## Safety proof

The authoritative artifact states:

- market rows read = false;
- V2B odds read = false;
- opening lambda read = false;
- FAIR_CENTRE read = false;
- centre_delta read = false;
- direction test performed = false;
- Odds API requests = 0;
- Supabase operations = 0;
- production model operations = 0.

Production `.pkl` hashes were unchanged.

## Next permitted block

Freeze one simple tactical-pressure mapping for the exact 34-fixture cohort before any
direction comparison.

The mapping should:

1. use only frozen prior-match deep/deep_allowed/PPDA/PPDA_allowed values;
2. avoid fitted weights on V2B;
3. avoid league-specific thresholds;
4. avoid opening line / FAIR_CENTRE;
5. not inspect centre_delta before the sign formula is frozen.

Because PPDA is inverse-pressure oriented (lower PPDA means more pressing activity), any
combined formula must make that orientation explicit before evaluation rather than
selecting a sign after opening outcomes.

## Safety

- research-only;
- NO_BET;
- no same-sample retuning;
- no automatic production promotion.
