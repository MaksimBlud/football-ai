# Continuity Addendum — Serie A + La Liga prospective capture ready

Date: 2026-09-11
PR: #243 — Freeze non-EPL prospective market capture for Serie A and La Liga
Branch: `research/serie-a-la-liga-prospective-capture-v1`

## Frozen protocol

`NON_EPL_MARKET_ONLY_V1`

- leagues: `SERIE_A`, `LA_LIGA`
- target: 100 prospective observations per league
- observation counter starts at `1/100` for the first valid pre-kickoff row
- canonical fixture identity: league + normalized home team + normalized away team + UTC kickoff + protocol
- capture must occur strictly before kickoff
- immutable source provenance is mandatory: `source_event_id` + `source_snapshot_time_utc`
- source snapshot must be strictly before kickoff and no later than `captured_at_utc`
- finite positive 1X2 decimal odds are required
- outcome, score, settlement and other post-match fields are rejected at capture time
- AI/model fields are rejected unless a separate league-specific frozen AI eligibility contract exists
- duplicate canonical rows are idempotent only with identical market values and provenance; conflicting rewrites fail closed
- malformed/non-contiguous existing counters fail closed
- the committed ledger is revalidated in CI
- no production `.pkl` dependency or write path
- no Supabase dependency and no Odds API dependency in the capture tool itself
- no paid Odds API authorization is created by this protocol

## First prospective observations — recorded before kickoff

Read-only live Supabase was queried only for future fixtures and pre-match market fields. No result, score, outcome, or settlement fields were read. Database time at source retrieval was `2026-09-11T02:12:02.819799+00:00`, before both kickoffs.

### Serie A — 1/100

- fixture: `Venezia` vs `Fiorentina`
- kickoff: `2026-09-11T18:45:00+00:00`
- source event: `a9656d25ca6b06be9e477a098333bd70`
- source snapshot: `2026-09-05T15:08:05.114487+00:00`
- captured at: `2026-09-11T02:12:02.819799+00:00`
- 1X2: home `2.64111111111111`, draw `3.19333333333333`, away `2.54`
- evidence class: `MARKET_ONLY`

### La Liga — 1/100

- fixture: `Sevilla` vs `Valencia`
- kickoff: `2026-09-11T19:00:00+00:00`
- source event: `79bc2eff76fa09664659765d5b1ded1a`
- source snapshot: `2026-09-05T15:21:32.513020+00:00`
- captured at: `2026-09-11T02:12:02.819799+00:00`
- 1X2: home `2.248125`, draw `3.02875`, away `3.24625`
- evidence class: `MARKET_ONLY`

The durable rows are in `experiments/non_epl_market_only_v1.csv`. They must never receive retrospective AI predictions or be relabeled as AI evidence.

## State after PR #243 implementation

### Serie A

- `CAPTURE_READY=true` for prospective `MARKET_ONLY` observations under `NON_EPL_MARKET_ONLY_V1`.
- current prospective count: `1/100`.
- `PROSPECTIVE_AI_READY=false`.
- `MODEL_READY=false` until the independent Serie A league-specific candidate/readiness protocol supplies admissible evidence and a frozen eligibility manifest.

### La Liga

- `CAPTURE_READY=true` for prospective `MARKET_ONLY` observations under `NON_EPL_MARKET_ONLY_V1`.
- current prospective count: `1/100`.
- `PROSPECTIVE_AI_READY=false`.
- Existing La Liga pure-AI v1, frozen hybrid v1, and nested historical v1 remain `CLOSED/REJECTED`; PR #243 does not reopen or retune them.

## CI requirement

PR #243 must not merge until every exact-head workflow is green. `Non-EPL Prospective Capture V1` compiles the tool, runs the fail-closed tests, validates the committed ledger, and proves no `.pkl` changes. Repository-level research and league validation workflows must also pass on the exact final head.

## Safety proof

No paid Odds API request, prospective result/settlement read, Supabase write, production `.pkl` modification, or production model promotion was performed. The only live database action was a read-only query limited to future fixture identity and pre-match 1X2 snapshot fields.

## Next executable step

After exact-head CI and merge, the two current rows remain immutable prospective MARKET_ONLY evidence. Additional rows may be appended only before kickoff under the same frozen invariants and with source provenance.

In parallel, continue the independent Serie A candidate-development/readiness path. A Serie A historical pass may only make a future AI protocol eligible for freezing; it cannot retroactively add AI predictions to already captured MARKET_ONLY rows. La Liga AI remains closed unless a genuinely new preregistered hypothesis with a defensible new evidence boundary is introduced.
