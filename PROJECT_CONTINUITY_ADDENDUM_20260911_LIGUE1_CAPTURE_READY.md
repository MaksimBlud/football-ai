# Continuity Addendum — Ligue 1 prospective MARKET_ONLY capture ready

Date: 2026-09-11
Branch: `research/ligue1-prospective-capture-v1`
Protocol: `LIGUE_1_MARKET_ONLY_V1`
Target: `100`

## Frozen boundary

The Ligue 1 prospective MARKET_ONLY contract was committed before inspecting live future Ligue 1 fixture values.

The protocol is league-specific and does not broaden or alter the existing EPL, Serie A, La Liga, or Bundesliga prospective contracts.

Every observation is market-only evidence and can never be retrospectively relabeled as prospective AI evidence.

## First live prospective observation

A read-only Supabase query was executed after the contract/tool/test boundary had been committed. The query selected only future fixture identity, kickoff, source market snapshot timestamp, and 1X2 market odds. No result, score, outcome, settlement, or prospective evaluation fields were read.

Observation `1/100`:

- league: `LIGUE_1`
- home: `Rennes`
- away: `Marseille`
- kickoff: `2026-09-11T18:45:00+00:00`
- source event id: `a7e7bf9a8226e86eab6e5c1cb0780a0f`
- source snapshot: `2026-09-05T14:28:52.747994+00:00`
- capture time: `2026-09-11T02:56:46.132295+00:00`
- home odds: `2.29631578947368`
- draw odds: `3.74157894736842`
- away odds: `2.76263157894737`

Both capture time and source snapshot are strictly before kickoff.

Committed ledger:

`experiments/ligue1_market_only_v1.csv`

## Safety state

- `CAPTURE_READY=true` subject to PR/full CI and post-merge proof;
- prospective MARKET_ONLY count: `1/100`;
- `MODEL_READY=false`;
- `PROSPECTIVE_AI_READY=false`;
- no AI/model fields are permitted in this ledger;
- no prospective outcome was read;
- no Supabase write occurred;
- no paid Odds API request occurred;
- no `.pkl` artifact was changed or created;
- no model promotion occurred;
- existing Serie A/La Liga and Bundesliga prospective ledgers remain immutable and are checksum-guarded by regression tests.

## Next step after capture merge

Run a separate Ligue 1 league-specific historical AI-readiness protocol. All already completed/current historical Ligue 1 data must be treated as development evidence unless an untouched boundary can be independently proven. A PASS may at most justify freezing a future prospective AI protocol; it must not retroactively convert this MARKET_ONLY observation into AI evidence.
