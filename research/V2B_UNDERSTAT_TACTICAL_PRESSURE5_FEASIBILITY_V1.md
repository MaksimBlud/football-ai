# V2B UNDERSTAT TACTICAL PRESSURE5 FEASIBILITY V1

Status: **PREREGISTERED SOURCE/FEATURE FEASIBILITY / NO DIRECTION TEST**

## Purpose

Test whether a new Stage-B information family can be reconstructed point-in-time for
the exact frozen V2B cohort using prior completed-match Understat tactical-pressure
fields rather than shots, xG, corners, Elo or opening-market state.

Candidate raw fields:

- `deep`;
- `deep_allowed`;
- `ppda`;
- `ppda_allowed`.

This block is source feasibility only. It does not choose a direction mapping.

## Why this is a different information dimension

The already-closed families are:

- CORNERS10 level vs opening line;
- HS/AS/HST/AST SHOTS10 transformations;
- result/Elo residual Stage B;
- absolute true-npxG environment Stage B;
- FAIR_CENTRE direction.

Understat `deep` and PPDA describe territorial entry / pressing structure from prior
matches rather than shot volume or expected-goal value.

Correlation with other football variables is possible, but the raw source fields are
not algebraic rewrites of the closed inputs.

## Frozen source

Public Understat league history:

- EPL;
- La Liga;
- Serie A;
- Bundesliga;
- Ligue 1.

Seasons:

- 2025/26;
- 2026/27.

Frozen V2B lock:

- artifact ID `10899325930`;
- digest `sha256:ad6bba499cc12abf5ca10732d88e0403565e2582e6c6c8a642ca7bb81248726f`;
- fixtures = 43.

## PPDA normalization

If Understat exposes PPDA as:

`{"att": numerator, "def": denominator}`

normalize to:

`ppda_ratio = att / def`

with positive finite denominator required.

If a positive finite numeric PPDA is provided directly, use it as-is.

Invalid/missing fields fail closed.

## Point-in-time feasibility rule

For each target team:

1. resolve the immutable V2B team to exactly one Understat title;
2. keep only rows with valid `deep`, `deep_allowed`, `ppda`, and
   `ppda_allowed`;
3. keep only rows strictly before target kickoff;
4. require at least five valid prior tactical rows.

A fixture passes only if both teams pass.

No lower-division backfill is allowed.

## Allowed output

For source audit only:

- schema keys actually seen;
- source team titles and identity status;
- valid prior tactical-row counts;
- rolling last-five means of deep/deep_allowed/ppda/ppda_allowed;
- exact feasible count and league coverage.

## Prohibited

Do not read:

- V2B market evaluation rows;
- opening corner line;
- FAIR_CENTRE;
- centre_delta;
- observed market direction.

Do not define or evaluate a Stage-B sign in this block.

If source feasibility passes, one mapping must be frozen separately before any direction
comparison.

## Safety

- research-only;
- NO_BET;
- zero Odds API calls;
- no Supabase writes;
- no model training/promotion;
- no production `.pkl` changes.
